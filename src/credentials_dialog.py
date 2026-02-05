#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialogo PySide6 que solicita las credenciales
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,QCheckBox,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog,
    QFrame, QProgressBar)
from PySide6.QtCore import Qt, QTimer

from pathlib import Path
import json
from typing import Dict

from datetime import datetime, timedelta

logger = logging.getLogger("maya_signer")

class CredentialsDialog(QDialog):
  """
  Diálogo para solicitar credenciales
  """
    
  def __init__(self, odoo_url: str, database: str, parent=None):
    super().__init__(parent)

    # Resultado
    self.credentials = None
    self.url = odoo_url
    self.database = database

    # Tiempo límite para introducir credenciales
    self.expiry_minutes = 2
    self.expiry_time = datetime.now() + timedelta(minutes=self.expiry_minutes)
    self.start_time = datetime.now()

    # configuracion
    self.config_file = Path.home() / '.maya_signer' / 'config.json'
    self.config_file.parent.mkdir(exist_ok=True)

    self.config = self.load_config()

    self.init_ui()

    # Timer para actualizar barra de progreso
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.update_progress)
    self.timer.start(1000)  # Actualizar cada segundo

  def init_ui(self):
    """
    Inicializa interfaz gráfica
    """
        
    # componentes de la interfaz    
    self.setWindowTitle('Maya Signer - Credenciales')
    self.setModal(True)
    
    self.setGeometry(300, 300, 750, 430)
    self.setMinimumWidth(550)
    self.setMinimumHeight(430)
    self.setMaximumHeight(430)

    main_layout = QVBoxLayout()
        
    # datos 
    layout = QHBoxLayout()
    layout.setSpacing(20)  # separación horizontal
    layout.setContentsMargins(15, 2, 15, 15)

    ## Conexión Odoo    
    left_layout = QVBoxLayout()
    
    ### Info
    info_layout = QVBoxLayout()
    info_layout.setSpacing(4)
    
    title_label = QLabel(f"<b>Conectar a Odoo</b>")
    title_label.setStyleSheet("font-size: 14px;")
    info_layout.addWidget(title_label)
    
    url_label = QLabel(f"URL: {self.url}")
    url_label.setStyleSheet("color: #999;")
    info_layout.addWidget(url_label)

    db_label = QLabel(f"Base de datos: {self.database}")
    db_label.setStyleSheet("color: #999;")
    info_layout.addWidget(db_label)
        
    left_layout.addLayout(info_layout)

    ### Campo usuario
    layout1 = QVBoxLayout()
    layout1.setSpacing(5)
    layout1.addWidget(QLabel("Usuario de Maya:"))
    self.username_input = QLineEdit(self.config.get('odoo_username', ''))
    self.username_input.setPlaceholderText("tu@email.com")
    layout1.addWidget(self.username_input)
    left_layout.addLayout(layout1)

    ### Campo contraseña Odoo
    layout2 = QVBoxLayout()
    layout2.setSpacing(5)
    layout2.addWidget(QLabel("Contraseña de Maya:"))
    self.password_input = QLineEdit()
    self.password_input.setEchoMode(QLineEdit.Password)
    layout2.addWidget(self.password_input)
    left_layout.addLayout(layout2)

    layout.addLayout(left_layout) 
    
    ## Separador
    separator = QFrame()
    separator.setFrameShape(QFrame.VLine)  
    separator.setFrameShadow(QFrame.Plain) 
    separator.setLineWidth(1) 
    layout.addWidget(separator)
    
    ## Datos Firma
    right_layout = QVBoxLayout()

    header_layout = QVBoxLayout()
    header_layout.setSpacing(4)
    
    title_cert_label = QLabel(f"<b>Datos firma electrónica</b>")
    title_cert_label.setStyleSheet("font-size: 14px;")
    header_layout.addWidget(title_cert_label)
    
    ### Checkbox DNIe
    self.dnie_checkbox = QCheckBox('Usar DNIe  ⚠️')
    self.dnie_checkbox.setChecked(self.config.get('use_dnie', False))
    self.dnie_checkbox.stateChanged.connect(self.on_dnie_changed)
    self.dnie_checkbox.setToolTip(
    "ATENCIÓN: Si marca esta opción, el sistema requerirá que\n"
    "confirme la firma manualmente para CADA documento del lote."
)
    header_layout.addWidget(self.dnie_checkbox)
    header_layout.addWidget(QLabel(""))

    right_layout.addLayout(header_layout)

    ### Datos certificado
    layout3 = QVBoxLayout()
    layout3.setSpacing(5)
    layout3.addWidget(QLabel('Ruta certificado .p12 (solo si no usas DNIe):'))
    cert_layout = QHBoxLayout()
    self.cert_input = QLineEdit(self.config.get('cert_path', ''))
    self.cert_input.setEnabled(not self.dnie_checkbox.isChecked())
    cert_layout.addWidget(self.cert_input)
    layout3.addLayout(cert_layout)
    
    browse_btn = QPushButton('Examinar...')
    browse_btn.clicked.connect(self.browse_certificate)
    browse_btn.setEnabled(not self.dnie_checkbox.isChecked())
    cert_layout.addWidget(browse_btn)
    layout3.addLayout(cert_layout)

    right_layout.addLayout(layout3)

    ### Campo contraseña certificado
    layout4 = QVBoxLayout()
    layout4.setSpacing(5)
    layout4.addWidget(QLabel("Contraseña del certificado/DNIe:"))
    self.cert_password_input = QLineEdit()
    self.cert_password_input.setEchoMode(QLineEdit.Password)
    layout4.addWidget(self.cert_password_input)
    right_layout.addLayout(layout4)

    layout.addLayout(right_layout) 

    # status
    self.status_label = QLabel("")
    self.status_label.setAlignment(Qt.AlignCenter)
    self.status_label.setWordWrap(True)
    self.status_label.setStyleSheet("font-size: 11px; padding: 5px;")

    # Nota informativa
    note_label = QLabel("Las credenciales se guardan en memoria solo durante esta sesión")
    note_label.setStyleSheet("color: #999; font-size: 12px;")
    note_label.setAlignment(Qt.AlignCenter)

    # barra de progreso
    timeout_layout = QVBoxLayout()
    timeout_layout.setContentsMargins(15, 10, 15, 5)
    
    self.timeout_label = QLabel(f"Tiempo restante: {self.expiry_minutes}:00")
    self.timeout_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2196F3;")
    timeout_layout.addWidget(self.timeout_label)
    
    self.progress_bar = QProgressBar()
    self.progress_bar.setMaximum(self.expiry_minutes * 60)  # En segundos
    self.progress_bar.setValue(self.expiry_minutes * 60)
    self.progress_bar.setTextVisible(False)
    self.progress_bar.setStyleSheet("""
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f5f5f5;
            height: 8px;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 4px;
        }
    """)
    timeout_layout.addWidget(self.progress_bar)

    # Botones
    button_layout = QHBoxLayout()
    button_layout.addStretch()

    self.test_btn = QPushButton("Probar Conexión")
    self.test_btn.clicked.connect(self.test_connection)
    button_layout.addWidget(self.test_btn)

    self.clean_cfg = QPushButton("Borrar configuración")
    self.clean_cfg.clicked.connect(self.clear_config)
    button_layout.addWidget(self.clean_cfg)

    cancel_btn = QPushButton("Cancelar")
    cancel_btn.clicked.connect(self.reject)
    button_layout.addWidget(cancel_btn)
      
    accept_btn = QPushButton("Firmar")
    accept_btn.setDefault(True)
    accept_btn.clicked.connect(self.accept_credentials)
    accept_btn.setStyleSheet("""
        QPushButton {
            background-color: #2196F3;
            color: white;
            padding: 6px 18px;
            border: none;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        """)
    button_layout.addWidget(accept_btn)

    main_layout.addLayout(layout) 
    main_layout.addWidget(self.status_label)
    main_layout.addWidget(note_label)
    main_layout.addLayout(timeout_layout)
    main_layout.addLayout(button_layout) 
        
    self.setLayout(main_layout) 

    if not self.username_input.text():
      self.username_input.setFocus()
    else:
      self.password_input.setFocus()

  def load_config(self) -> Dict:
    """
    Carga configuración
    """
    
    if self.config_file.exists():
      with open(self.config_file, 'r') as f:
        return json.load(f)
      
    return {
      'odoo_username': '',
      'cert_path': '',
      'use_dnie': False
    }

  def save_config(self, clean: bool = False):
    """
    Guarda configuración
    """
    self.config = {
      'odoo_username': self.username_input.text() if not clean else '',
      'cert_path': self.cert_input.text() if not clean else '',
      'use_dnie': self.dnie_checkbox.isChecked() if not clean else False
    }
   
    with open(self.config_file, 'w') as f:
      json.dump(self.config, f, indent=2)

  def clear_config(self):
    """
    Limpia la configuración
    """
    self.save_config(clean=True)

  def accept_credentials(self):
    """
    Valida y acepta las credenciales
    """
    username = self.username_input.text().strip()
    password = self.password_input.text()
    cert_password = self.cert_password_input.text()
    cert_path = self.cert_input.text().strip()
    use_dnie = self.dnie_checkbox.isChecked()
    
    if not username or not password or \
       not cert_password or (not use_dnie and not cert_path):
      QMessageBox.warning(
          self,
          "Campos incompletos",
          "Por favor completa todos los campos"
      )
      return
    
    self.credentials = {
      'username': username,
      'password': password,
      'cert_password': cert_password,
      'cert_path': cert_path,
      'use_dnie': use_dnie
    }

    self.save_config()
    
    self.accept()

  def on_dnie_changed(self, state):
    """
    Habilita/deshabilita campo de certificado
    """

    self.cert_input.setEnabled(state == 0)

  def browse_certificate(self):
    """
    Abre diálogo para seleccionar certificado
    """
    file_path, _ = QFileDialog.getOpenFileName(
      self,
      "Seleccionar certificado",
      str(Path.home()),
      "Certificados (*.p12 *.pfx);;Todos los archivos (*.*)"
    )

    if file_path:
      self.cert_input.setText(file_path)

  def show_status(self, message: str, status_type: str):
    """
    Muestra un mensaje de estado
    
    Args:
      message: Texto a mostrar
      status_type: 'info', 'success', 'error', 'warning'
    """
    colors = {
        'info': '#2196F3',
        'success': '#4CAF50',
        'error': '#F44336',
        'warning': '#FF9800'
    }
    
    color = colors.get(status_type, colors['info'])
    
    self.status_label.setText(message)
    self.status_label.setStyleSheet(f"""
        color: {color};
        border: 1px solid {color};
        border-radius: 4px;
        padding: 8px;
        font-size: 11px;
    """)

  def update_progress(self):
    """
    Actualiza la barra de progreso cada segundo
    """
    now = datetime.now()
    
    # Calcular tiempo restante
    remaining = (self.expiry_time - now).total_seconds()
    
    if remaining <= 0:
      # Tiempo expirado
      self.timer.stop()
      self.timeout_label.setText("Tiempo expirado")
      self.timeout_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #F44336;")
      self.progress_bar.setValue(0)
      self.progress_bar.setStyleSheet("""
          QProgressBar {
              border: 1px solid #ddd;
              border-radius: 5px;
              background-color: #f5f5f5;
              height: 8px;
          }
          QProgressBar::chunk {
              background-color: #F44336;
              border-radius: 4px;
          }
      """)
      
      QMessageBox.warning(
          self,
          "Tiempo expirado",
          "El tiempo de firma ha expirado. Debes iniciar el proceso nuevamente desde Odoo."
      )
      self.reject()
      return
    
    # Actualizar barra
    self.progress_bar.setValue(int(remaining))
    
    # Actualizar etiqueta
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    self.timeout_label.setText(f"Tiempo restante: {minutes}:{seconds:02d}")
    
    # Cambiar color según tiempo restante
    if remaining < 60:  # Menos de 1 minuto
      self.timeout_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #F44336;")
      self.progress_bar.setStyleSheet("""
          QProgressBar {
              border: 1px solid #ddd;
              border-radius: 5px;
              background-color: #f5f5f5;
              height: 8px;
          }
          QProgressBar::chunk {
              background-color: #F44336;
              border-radius: 4px;
          }
      """)
    elif remaining < 180:  # Menos de 3 minutos
      self.timeout_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FF9800;")
      self.progress_bar.setStyleSheet("""
          QProgressBar {
              border: 1px solid #ddd;
              border-radius: 5px;
              background-color: #f5f5f5;
              height: 8px;
          }
          QProgressBar::chunk {
              background-color: #FF9800;
              border-radius: 4px;
          }
      """)

  def test_connection(self):
    """
    Prueba la conexión con Odoo en un thread separado
    """
    
    username = self.username_input.text().strip()
    password = self.password_input.text()
    
    if not username or not password:
      self.show_status(
          "Son necesarios el usuario y contraseña de Odoo",
          "warning"
      )
      return
    
    # Deshabilitar botón durante la prueba
    self.test_btn.setEnabled(False)
    self.test_btn.setText("Probando...")
    self.show_status("Conectando con Odoo...", "info")

    logger.info("Probando conexión con Odoo...")
    
    # Cero un thread para no bloquear la UI
    from PySide6.QtCore import QThread, Signal
    
    class TestConnectionThread(QThread):
      """
      Thread para probar conexión sin bloquear UI
      """
      finished = Signal(bool, str)  # success, message
      
      def __init__(self, url, database, username, password):
        super().__init__()

        self.url = url
        self.database = database
        self.username = username
        self.password = password
        
      def run(self):
        """
        Ejecuta el test en background
        """
        try:
          from odoo_client import OdooClient
            
          client = OdooClient(self.url,self.database,self.username,self.password)

          # Test de conexión
          result = client.test_connection()
              
          if result['success']:
            # Test de autenticación
            if client.authenticate():
                msg = f"Conectado a Odoo {result.get('server_version', '')}"
                self.finished.emit(True, msg)
            else:
                self.finished.emit(False, "Credenciales inválidas")
          else:
            error = result.get('error', 'Error desconocido')
            self.finished.emit(False, f"Error: {error}")
              
        except Exception as e:
          self.finished.emit(False, f"Error: {str(e)}")
          logger.error(f"Error en TestConnectionThread: {str(e)}")
  
    # Crear y conectar thread
    self.test_thread = TestConnectionThread(self.url, self.database, username, password)
    self.test_thread.finished.connect(self.on_test_finished)
    self.test_thread.start()

  def on_test_finished(self, success: bool, message: str):
    """
    Callback cuando termina el test de conexión
    """
    
    # activo botón
    self.test_btn.setEnabled(True)
    self.test_btn.setText("Probar Conexión")
    
    if success:
        self.show_status(message, "success")
    else:
        self.show_status(message, "error")
    
    # Limpio thread
    if self.test_thread:
      self.test_thread.deleteLater()
      self.test_thread = None