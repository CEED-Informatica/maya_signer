# -*- coding: utf-8 -*-

from pathlib import Path
import json
from typing import Dict
from PySide6.QtWidgets import (QWidget, QFileDialog, QVBoxLayout, QLabel, QPushButton,
                               QLineEdit, QMessageBox,QCheckBox)

from maya_client import MayaClient

class MayaSignerService(QWidget):
  """
  Servicio principal con interfaz gráfica
  """
    
  def __init__(self):
    super().__init__()

    self.config_file = Path.home() / '.odoo_signer' / 'config.json'
    self.config_file.parent.mkdir(exist_ok=True)
        
    self.config = self.load_config()
        
    self.init_ui()
    
 
  def init_ui(self):
    """
    Inicializa interfaz gráfica
    """
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
    """
    Carga configuración
    """
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
    """
    Guarda configuración
    """
    with open(self.config_file, 'w') as f:
      json.dump(self.config, f, indent=2)
 
  def save_settings(self):
    """
    Guarda configuración
    """
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
    """
    Habilita/deshabilita campo de certificado
    """
    self.cert_input.setEnabled(state == 0)
    
  def test_connection(self):
    """
    Prueba conexión con Odoo
    """
    try:
      odoo_client = MayaClient(
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
      