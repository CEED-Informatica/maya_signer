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
from typing import Dict

from PySide6.QtWidgets import (QApplication, QMessageBox, QSystemTrayIcon, QStyle,
                               QMenu)
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon

from odoo_client import OdooClient

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from custom_logging import setup_logger  # logging local

SERVICE_PORT = 50304                    ## inventado
LOCK_FILE = Path.home() / ".maya-signer.lock"

logger = setup_logger("service.log", __name__)

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
      content_length = int(self.headers['Content-Length'])
      post_data = self.rfile.read(content_length)
      data = json.loads(post_data.decode('utf-8'))

      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps({'status': 'processing'}).encode())
          
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
    self.running = False
  
    self.version = "0.2a0"

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
      self.tray_icon.setIcon(QIcon(str(icon_path)))
    else:
      self.tray_icon.setIcon(self.create_icon())

    menu = QMenu()
    title_action = menu.addAction(f'Maya Signer {self.version}')
    title_action.setEnabled(False)

    menu.addSeparator()

    connections_action = menu.addAction(f"Conexión activa")
    connections_action.setEnabled(False)

    menu.addSeparator()
    
    quit_action = menu.addAction('Salir')
    quit_action.triggered.connect(self.quit_service)
    
    self.tray_icon.setContextMenu(menu)
    self.tray_icon.show()
    
    self.tray_icon.showMessage(
        'Maya Signer',
        'Servicio iniciado. Esperando solicitudes...',
        QSystemTrayIcon.Information,
        2000
    )

  def start_server(self):
    """
    Inicia el servidor HTTP local
    """
    try:
      self.server = HTTPServer(('127.0.0.1', SERVICE_PORT), MayaServiceHandler)
      self.server.maya_service = self
      
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
        
    # Iniciar servidor
    if not self.start_server():
      QMessageBox.critical(
          None,
          "Error",
          "El servicio ya está ejecutándose"
      )
      return 1
    
    # Ejecutar aplicación Qt
    return self.app.exec()
 
    """ def init_ui(self):
    
    Inicializa interfaz gráfica
    
    self.setWindowTitle('Maya Signer - Configuración')
    self.setGeometry(300, 300, 450, 400)
        
    layout = QVBoxLayout()
    
    # Campos
    layout.addWidget(QLabel('URL Maya/Odoo:'))
    self.url_input = QLineEdit(self.config.get('odoo_url', ''))
    layout.addWidget(self.url_input)
    
    layout.addWidget(QLabel('Base de datos:'))
    self.db_input = QLineEdit(self.config.get('odoo_db', ''))
    layout.addWidget(self.db_input)
    
    layout.addWidget(QLabel('Usuario:'))
    self.user_input = QLineEdit(self.config.get('odoo_username', ''))
    layout.addWidget(self.user_input)
    
    layout.addWidget(QLabel('Contraseña:'))
    self.pass_input = QLineEdit()
    self.pass_input.setEchoMode(QLineEdit.Password)
    layout.addWidget(self.pass_input)
    
    # Checkbox DNIe
    self.dnie_checkbox = QCheckBox('Usar DNIe')
    self.dnie_checkbox.setChecked(self.config.get('use_dnie', False))
    self.dnie_checkbox.stateChanged.connect(self.on_dnie_changed)
    layout.addWidget(self.dnie_checkbox)
    
    layout.addWidget(QLabel('Ruta certificado .p12 (solo si no usas DNIe):'))
    cert_layout = QVBoxLayout()
    self.cert_input = QLineEdit(self.config.get('cert_path', ''))
    self.cert_input.setEnabled(not self.dnie_checkbox.isChecked())
    cert_layout.addWidget(self.cert_input)
    
    browse_btn = QPushButton('Examinar...')
    browse_btn.clicked.connect(self.browse_certificate)
    cert_layout.addWidget(browse_btn)
    layout.addLayout(cert_layout)
    
    # Botones
    save_btn = QPushButton('Guardar configuración')
    save_btn.clicked.connect(self.save_settings)
    layout.addWidget(save_btn)
    
    test_btn = QPushButton('Probar conexión')
    test_btn.clicked.connect(self.test_connection)
    layout.addWidget(test_btn)
    
    self.setLayout(layout)

 
    

  def load_config(self) -> Dict:
    
    Carga configuración
    
    if self.config_file.exists():
      with open(self.config_file, 'r') as f:
        return json.load(f)
      
    return {
      'odoo_url': '',
      'odoo_db': '',
      'odoo_username': '',
      'cert_path': '',
      'use_dnie': False
    }
  
  def save_config(self):
    
    Guarda configuración
    
    with open(self.config_file, 'w') as f:
      json.dump(self.config, f, indent=2)
 
  def save_settings(self):
    
    Guarda configuración
    
    self.config = {
      'odoo_url': self.url_input.text(),
      'odoo_db': self.db_input.text(),
      'odoo_username': self.user_input.text(),
      'cert_path': self.cert_input.text(),
      'use_dnie': self.dnie_checkbox.isChecked()
    }

    self.save_config()

    QMessageBox.information(self, 'Guardado', 'Configuración guardada correctamente')

  def on_dnie_changed(self, state):
  
    Habilita/deshabilita campo de certificado
  
    self.cert_input.setEnabled(state == 0)
    
  def test_connection(self):
    
    Prueba conexión con Odoo
    
    try:
      odoo_client = OdooClient(
        self.url_input.text(),
        self.db_input.text(),
        self.user_input.text(),
        self.pass_input.text()
        )
            
      if odoo_client.authenticate():
        QMessageBox.information(self, 'Éxito', 'Conexión exitosa con Odoo')
      else:
        QMessageBox.warning(self, 'Error', 'No se pudo autenticar')
                    
    except Exception as e:
        QMessageBox.critical(self, 'Error', f'Error de conexión: {e}')

  def browse_certificate(self):
    
    Abre diálogo para seleccionar certificado
    
    file_path, _ = QFileDialog.getOpenFileName(
      self,
      "Seleccionar certificado",
      str(Path.home()),
      "Certificados (*.p12 *.pfx);;Todos los archivos (*.*)"
    )

    if file_path:
      self.cert_input.setText(file_path)
      
  def handle_protocol(self, url: str):
    
    Gestiona llamadas al protocolo maya://sign
    
    logger.info(f"Protocolo recibido: {url}")
        
    try:
      parsed = urlparse(url)
      params = parse_qs(parsed.query)
    
      batch_id = int(params['batch'][0])
      token = params.get('token', [None])[0]
      odoo_url = params.get('url', [self.config['odoo_url']])[0]
    
      # Autenticar
      odoo_client = OdooClient(
        odoo_url,
        self.config['odoo_db'],
        self.config['odoo_username'],
        self.pass_input.text()
      )
            
      if not odoo_client.authenticate():
        raise ValueError("Error de autenticación con Odoo")
            
      # Obtener contraseña del certificado si no es DNIe
      cert_password = None
      cert_password, ok = QInputDialog.getText(
                    self, 
                    'Contraseña del certificado', 
                    'Introduce la contraseña del certificado:',
                    QLineEdit.Password
                )
      if not ok:
        return
       
    except Exception as e:
      logger.error(f"Error manejando protocolo: {str(e)}")
      QMessageBox.critical(self, 'Error', str(e)) """

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
