# -*- coding: utf-8 -*-

import logging

from pyhanko.sign import pkcs11
import os

from typing import Optional

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

logger = logging.getLogger(__name__)

class PyHankoSigner:
  """
  Wrapper para pyHanko que firma PDFs
  """
  
  def __init__(self):
    self._setup_dnie()


  def _setup_dnie(self):
    """
    Configura firma con DNIe usando PKCS#11
    """
    try:
          
      # Busco el módulo PKCS#11
      pkcs11_lib = os.environ.get('PKCS11_MODULE')
          
      if not pkcs11_lib or not os.path.exists(pkcs11_lib):
        alternatives = [
            "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so",
            "/usr/lib/opensc-pkcs11.so",
            "/usr/local/lib/opensc-pkcs11.so",
            "C:\\Windows\\System32\\opensc-pkcs11.dll",  # Windows
        ]
              
        for alt in alternatives:
          if os.path.exists(alt):
              pkcs11_lib = alt
              break
        else:
          raise FileNotFoundError(
              "No se encontró el módulo PKCS#11 del DNIe.\n"
              "Linux: sudo apt-get install opensc\n"
              "Windows: Instala el software del DNIe"
          )
          
      logger.info(f"Módulo PKCS#11: {pkcs11_lib}")
          
      # Abro sesión PKCS#11
      # user_pin None ya que se pedirá interactivamente
      session = pkcs11.open_pkcs11_session(lib_location=pkcs11_lib, slot_no=0, user_pin=None)
        
      # Intento detectar etiqueta del certificado
      if self.cert_label is None:
        possible_labels = [
            "KprivFirmaDigital",
            "CertFirmaDigital",
            "CITIZEN SIGNATURE KEY",
            "Firma Digital",
        ]
          
        for label in possible_labels:
          try:
            logger.info(f"   Probando etiqueta: {label}")
            test_signer = pkcs11.PKCS11Signer(pkcs11_session=session, cert_label=label)
            self.cert_label = label
            logger.info(f"Certificado encontrado: {label}")
            break
          except Exception:
            continue
          
        if self.cert_label is None:
            raise ValueError(
                "No se encontró certificado de firma en el DNIe.\n"
                "Ejecuta: pkcs11-tool --list-objects --type cert"
            )
      
        # Crear firmante
        self.signer = pkcs11.PKCS11Signer(pkcs11_session=session, cert_label=self.cert_label)
        
        logger.info(f"DNIe configurado con certificado: {self.cert_label}")
        
    except Exception as e:
      logger.error(f"Error configurando DNIe: {str(e)}")
      raise
