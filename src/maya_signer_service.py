#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Maya Signer Service
Se ejecuta en background y procesa peticiones de firma
"""

import logging

import sys

from pathlib import Path
import json
import time

from PySide6.QtWidgets import (QApplication, QMessageBox, QSystemTrayIcon, QStyle,
                               QMenu, QDialog)
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon

from credentials_dialog import CredentialsDialog

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from custom_logging import setup_logger  # logging local

SERVICE_PORT = 50304                    ## inventado
LOCK_FILE = Path.home() / ".maya-signer.lock"

logger = setup_logger("service.log", "maya_signer")

class SignalEmitter(QObject):
  """
  Emisor de señales (eventos) para comunicación con Qt
  """
  show_credentials_dialog = Signal(str, str)  # odoo_url, database

class MayaServiceHandler(BaseHTTPRequestHandler):
  """
  Maneja peticiones HTTP del cliente
  """
    
  def log_message(self, format, *args):
    """
    Silencia los logs HTTP
    """
    pass
    
  def do_POST(self):
    """
    Maneja peticiones POST
    Procesa la petición de firma de documentos
    """
    try:
      self.server.maya_signer_service.quit_action.setEnabled(False)
      content_length = int(self.headers['Content-Length'])
      post_data = self.rfile.read(content_length)
      data = json.loads(post_data.decode('utf-8'))

      # Obtener credenciales almacenadas
      credentials = self.server.maya_signer_service.get_credentials(data['url'])

      if not credentials:
        # Solicitar credenciales vía dialogo Qt
        self.server.maya_signer_service.signals.show_credentials_dialog.emit(
          data['url'],
          data.get('database', '') # por si en un futuro permito firmas sin asociarlas a BD
        )
        
        # Esperar a que se introduzcan (timeout 120s)
        for _ in range(60):
          time.sleep(2)
          status = self.server.maya_signer_service.get_credentials(data['url'])

          if status == "CANCELLED":
            # Si detectamos la cancelación, salimos del bucle inmediatamente
            credentials = "CANCELLED"
            break
          
          if status:  # hay credenciales, y no es cancelled
            credentials = status
            break
          
      if credentials and credentials != "CANCELLED":
        # Procesar firma en background
        threading.Thread(
            target=self.server.maya_signer_service.process_signature,
            args=(data, credentials),
            daemon=True
        ).start()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'processing'}).encode())
      elif credentials == "CANCELLED":
        self.send_response(499)
        self.end_headers()
        self.wfile.write(json.dumps({'error': "user_cancelled"}).encode())

        # Limpio el marcador de cancelación para la próxima vez
        if data['url'] in self.server.maya_signer_service.credentials_store:
          del self.server.maya_signer_service.credentials_store[data['url']]
      else:
        self.send_response(401)
        self.end_headers()
        self.wfile.write(json.dumps({'error': "credentials_required"}).encode())


    except Exception as e:
      logger.error(f"Error en handler: {str(e)}")
      self.send_response(500)
      self.end_headers()
      self.wfile.write(json.dumps({'error': str(e)}).encode())
    
  def do_GET(self):
    """
    ¿Estás vivo?
    """
    if self.path == '/health':
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps({'status': 'running'}).encode())

class MayaSignerService(QObject):
  """
  Servicio principal
  """
    
  def __init__(self, app):
    super().__init__()

    self.app = app
    
    self.server = None
    self.tray_icon = None
    self.tray_menu = None  
    self.running = False
    # diccionario de credenciales.
    # lo normal es que haya una única entrada, 
    # pero permite varias por si hubiera diferentes servidores para diferentes tareas 
    # (Gestion documental/Gestion alumnos)
    self.credentials_store = {}  
  
    self.version = "0.3a0"

    # Señales para Qt
    self.signals = SignalEmitter()
    self.signals.show_credentials_dialog.connect(self._show_credentials_dialog)

  def get_credentials(self, odoo_url):
    """
    Obtiene credenciales almacenadas por servidor
    """
    return self.credentials_store.get(odoo_url)
  
  def store_credentials(self, odoo_url: str, username: str, password: str, 
                        cert_password: str, use_dnie: bool, cert_path: str):
    """
    Almacena credenciales en memoria
    """
    self.credentials_store[odoo_url] = {
        'username': username,
        'password': password,
        'cert_password': cert_password,
        'use_dnie': use_dnie,
        'cert_path': cert_path  
    }
    
    self.update_tray_menu()

  def _show_credentials_dialog(self, odoo_url: str, database: str):
    """
    Muestra diálogo de credenciales
    """
    dialog = CredentialsDialog(odoo_url, database)
        
    if dialog.exec() == QDialog.Accepted and dialog.credentials:
      self.store_credentials(
          odoo_url,
          dialog.credentials['username'],
          dialog.credentials['password'],
          dialog.credentials['cert_password'],
          dialog.credentials['use_dnie'],
          dialog.credentials['cert_path'],
      )
    else:
      # Guardo un marcador de cancelación para este servidor
      logger.info(f"Firma cancelada por el usuario para {odoo_url}")
      self.credentials_store[odoo_url] = "CANCELLED"

  def create_icon(self) -> QIcon:
    """
    Crea el icono en la bandeja del sistema, en caso de que no haya ninguno definido
    """
    from PySide6.QtGui import Qt, QPainter, QColor, QFont, QPixmap

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
   
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Fondo azul
    painter.setBrush(QColor("#2196F3"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 10, 10)
    
    # Texto "MySg"
    painter.setPen(QColor("white"))
    font = QFont("Arial", 16, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "MySg")
    painter.end()
    
    icon = QIcon(pixmap)

    return  icon

  def init_tray(self):
    """
    Inicializa icono en bandeja
    """
    self.tray_icon = QSystemTrayIcon(self)
    
    # Intenta cargar icono y si no puede usa uno por defecto
    icon_path = Path(__file__).parent / 'icon.png'
    if icon_path.exists():
      self.icon = QIcon(str(icon_path))
    else:
      self.icon = self.create_icon()

    self.tray_icon.setIcon(self.icon)

    self.update_tray_menu()

    self.tray_icon.show()
    
    self.tray_icon.showMessage(
        'Maya Signer',
        'Servicio iniciado. Esperando solicitudes...',
        QSystemTrayIcon.Information,
        3000
    )

  def update_tray_menu(self):
    """
    Actualiza el menú del system tray
    
    Destruye el menú anterior para evitar memory leaks.
    Qt no libera automáticamente el QMenu viejo al hacer setContextMenu().
    """
    # Destruyo menú anterior si existe
    if self.tray_menu is not None:
      self.tray_icon.setContextMenu(None)
      self.tray_menu.clear()
      self.tray_menu.deleteLater()  # destruyo el objeto Qt
      self.tray_menu = None
    
    self.tray_menu = QMenu()
    title_action = self.tray_menu.addAction(f'Maya Signer {self.version}')
    title_action.setEnabled(False)

    self.tray_menu.addSeparator()

    # Información sobre el estado de la firma
    self.status_action = self.tray_menu.addAction("Servicio Listo")
    self.status_action.setEnabled(False) 
    
    self.tray_menu.addSeparator()

    connections_action = self.tray_menu.addAction(f"Conexiones activas: {'OK' if self.credentials_store else 'Ninguna'} ({len(self.credentials_store)})")
    connections_action.setEnabled(False)

    clear_action = self.tray_menu.addAction("Borrar credenciales")
    clear_action.triggered.connect(self.clear_credentials)

    self.tray_menu.addSeparator()
    
    self.quit_action = self.tray_menu.addAction('Salir')
    self.quit_action.triggered.connect(self.quit_service)

    self.tray_icon.setContextMenu(self.tray_menu)

    self.tray_icon.setToolTip("Maya Signer - Servicio Listo")

  def start_server(self):
    """
    Inicia el servidor HTTP local
    """
    try:
      self.server = HTTPServer(('127.0.0.1', SERVICE_PORT), MayaServiceHandler)
      self.server.maya_signer_service = self
      
      logger.info(f"Maya Signer Service iniciado en puerto {SERVICE_PORT}")
      
      # Creo archivo de lock
      LOCK_FILE.write_text(str(SERVICE_PORT))
      
      self.running = True
      
      # Ejecuto el servidor en un thread separado
      server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
      server_thread.start()
      
      return True
      
    except OSError as e:
      if e.errno == 48 or e.errno == 98:
        logger.error(f"Servicio ya está ejecutándose en el puerto {SERVICE_PORT}")
        return False
      raise
    finally:
      if LOCK_FILE.exists() and not self.running:
        LOCK_FILE.unlink()

  def clear_credentials(self):
    """
    Borra todas las credenciales almacenadas
    """
    self.credentials_store.clear()
    self.update_tray_menu()
    
  def quit_service(self):
    """
    Cierra el servicio
    """
    self.running = False
    if self.server:
      self.server.shutdown()
    
    self.app.quit()
  
  def run(self):
    """
    Prepara el arranque del servicio
    """
        
    logger.info("=" * 60)
    logger.info("  MAYA SIGNER SERVICE")
    logger.info("=" * 60)
        
    # Icono en tray
    self.init_tray()

    # Iniciao el servidor
    if not self.start_server():
      QMessageBox.critical(
          None,
          "Error",
          "El servicio ya está ejecutándose"
      )
      return 1
    
    # Ejecuto la aplicación Qt
    return self.app.exec()
  
  def update_progress_ui(self, message):
    """
    Actualiza el estado de la firma en la bandeja de sistema
    """
    """ if current == total and total > 0:
      self.status_action.setText("Servicio Listo")
      self.tray_icon.setToolTip("Servicio Listo")
    elif total > 0:
      status_text = f"Procesando: {current}/{total} documentos"
      self.status_action.setText(status_text)
      self.tray_icon.setToolTip(f"Maya Signer - {status_text}") """
    
    self.status_action.setText(f"{message}")
    self.tray_icon.setToolTip(f"Maya Signer - {message}")
      
  def process_signature(self, data, credentials):
    """
    Procesa la firma de documentos usando subproceso
    """
    try:
      from odoo_client import OdooClient, OdooTokenError, OdooAuthenticationError
      from subprocess_signature_manager import SubprocessSignatureManager

      logger.info(f"** (1) => Iniciando proceso de firma del lote {data['batch']}... **")
      logger.info(f"\tServidor: {data['url']}")
      logger.info(f"\tBase de datos: {data.get('database', '')}")
      logger.info(f"\tUsuario: {credentials['username']}")
      logger.info(f"\tToken: {data.get('token', 'N/A')[:10]}...")
    
      logger.info("** (2) => Conectando con Odoo... **")

      self.quit_action.setEnabled(False)

      client = OdooClient(
          url=data['url'],
          db=data.get('database', ''),
          username=credentials['username'],
          password=credentials['password'],
          batch_token=data.get('token'),
          progress_callback=self.update_progress_ui
      )
          
      if not client.authenticate():
        raise Exception("Error de autenticación con Odoo")

      logger.info("\tAutenticación correcta")

      # 2. Validar token del batch
      try:
        logger.info("** (3) Validando token de sesión... **")
        validation = client.validate_batch_token(int(data['batch']))
        # OJO logger.info(f"\tToken validado: {validation.get('batch_name')}")
      except OdooTokenError as e:
        logger.error(f"\tToken inválido o expirado: {e}")
        
        QMessageBox.critical(
            None,
            "Error de autenticación",
            "El token de firma ha expirado. Inicia el proceso nuevamente desde Maya."
        )

        #self.signals.update_tray_icon.emit()
        return

      logger.info("** (4) => Descargando PDFs sin firmar... **")
      documents = client.download_unsigned_pdfs(int(data['batch']))
          
      if not documents:
        raise Exception("No hay documentos para firmar")

      logger.info(f"\t{len(documents)} documentos descargados")

      logger.info("** (5) => Iniciando firma con subproceso... **")
      
      manager = SubprocessSignatureManager()
      
      result = manager.sign_documents(
        documents=documents,
        cert_path=credentials.get('cert_path'),
        cert_password=credentials['cert_password'],
        use_dnie=credentials.get('use_dnie', False),
        progress_callback=self.update_progress_ui,
        cleanup=True  # solo ponerlo a False en entornos de pruebas!!
      )
      
      if not result['success']:
        error_msg = result.get('error', 'Error desconocido')
        logger.error(f"\tError en firma: {error_msg}")
        
        QMessageBox.critical(
            None,
            "Error de firma",
            f"Error firmando documentos: {error_msg}"
        )
            
        return
      
      signed_documents = result['signed_documents']
      
      if not signed_documents:
        logger.error("No se firmó ningún documento")
        
        if self.tray_icon:
          self.tray_icon.showMessage(
            'Sin documentos',
            'No se pudo firmar ningún documento',
            QSystemTrayIcon.Warning,
            5000
          )
        return
      
      logger.info(f"\t{len(signed_documents)} documentos firmados correctamente")
      
      logger.info("** (6) => Subiendo documentos firmados a Odoo... **")

      try:
        upload_correct = client.upload_signed_pdfs(int(data['batch']), signed_documents)
        
        if upload_correct:
          logger.info("\tTodos los documentos subidos correctamente")

          if self.tray_icon:
            self.tray_icon.showMessage(
            'Firma completada',
            f'{len(signed_documents)} documentos firmados correctamente',
            QSystemTrayIcon.Information,
            5000
          )
            
        else:
          logger.error("\tError al subir documentos firmados a Odoo")
          
          QMessageBox.critical(
            None,
            "Error de subida",
            "Error al subir documentos firmados a Odoo"
          )
          return
              
      except OdooTokenError as e:
        logger.error(f"\tToken expiró durante la subida: {str(e)}")
        
        QMessageBox.critical(
            None,
            "Error de sesión",
            "El token expiró durante la subida. Algunos documentos pueden no haberse guardado."
        )
        return
      
      logger.info("=" * 60)
      logger.info("    PROCESO COMPLETADO CON ÉXITO")
      logger.info("=" * 60)
        
    except Exception as e:
      logger.error(f"Error procesando firma: {str(e)}", exc_info=True)

      if type(e) == OdooAuthenticationError:
        self.clear_credentials()

      # Notificar error
      QMessageBox.critical(
        None,
        "Error",
        f'Error en el proceso de firma: {str(e)}'
      )
     
    finally:
      self.quit_action.setEnabled(True)
      self.status_action.setText(f"Servicio Listo")  

def main():
  """
  Inicia el servicio persistente
  """

  app = QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)
    
  service = MayaSignerService(app)
  return service.run()


if __name__ == "__main__":
  sys.exit(main())
