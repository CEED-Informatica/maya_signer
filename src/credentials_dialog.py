#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialogo PySide6 que solicita las credenciales
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,QCheckBox,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog,
    QFrame)
from PySide6.QtCore import Qt

from pathlib import Path

class CredentialsDialog(QDialog):
  """
  Diálogo para solicitar credenciales
  """
    
  def __init__(self, odoo_url: str, database: str, parent=None):
    super().__init__(parent)

    # Resultado
    self.credentials = None
        
    self.setWindowTitle('Maya Signer - Credenciales')
    self.setModal(True)
    
    self.setGeometry(300, 300, 750, 300)
    self.setMinimumWidth(550)
    self.setMinimumHeight(300)
    self.setMaximumHeight(300)

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
    
    url_label = QLabel(f"URL: {odoo_url}")
    url_label.setStyleSheet("color: #999;")
    info_layout.addWidget(url_label)
  
    db_label = QLabel(f"Base de datos: {database}")
    db_label.setStyleSheet("color: #999;")
    info_layout.addWidget(db_label)
        
    left_layout.addLayout(info_layout)

    ### Campo usuario
    layout1 = QVBoxLayout()
    layout1.setSpacing(5)
    layout1.addWidget(QLabel("Usuario de Maya:"))
    self.username_input = QLineEdit()
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
    self.dnie_checkbox = QCheckBox('Usar DNIe')
    self.dnie_checkbox.stateChanged.connect(self.on_dnie_changed)
    header_layout.addWidget(self.dnie_checkbox)

    right_layout.addLayout(header_layout)

    ### Datos certificado
    layout3 = QVBoxLayout()
    layout3.setSpacing(5)
    layout3.addWidget(QLabel('Ruta certificado .p12 (solo si no usas DNIe):'))
    cert_layout = QHBoxLayout()
    self.cert_input = QLineEdit()
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

    # Nota informativa
    note_label = QLabel("Las credenciales se guardan en memoria solo durante esta sesión")
    note_label.setStyleSheet("color: #999; font-size: 12px;")
    note_label.setAlignment(Qt.AlignCenter)

    # Botones
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    
    cancel_btn = QPushButton("Cancelar")
    cancel_btn.clicked.connect(self.reject)
    button_layout.addWidget(cancel_btn)
      
    accept_btn = QPushButton("Conectar")
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
    main_layout.addWidget(note_label)
    main_layout.addLayout(button_layout) 
        
    self.setLayout(main_layout)
        
    self.username_input.setFocus()
    
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