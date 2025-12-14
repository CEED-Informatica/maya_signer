# -*- coding: utf-8 -*-

import logging

# pyHanko
from pyhanko.sign import pkcs11
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec

from io import BytesIO
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
  
  def __init__(self, cert_password: Optional[str] = None, cert_label: Optional[str] = None):
    
    self.cert_label = cert_label
    self.cert_password = cert_password
    self.signer = None

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
      session = pkcs11.open_pkcs11_session(lib_location=pkcs11_lib, slot_no=0, user_pin=self.cert_password)
        
      # Intento detectar etiqueta del certificado
      if self.cert_label is None:
        possible_labels = [
          "CertFirmaDigital",
          "CertAutenticacion", 
        ]
          
        for label in possible_labels:
          try:
            logger.info(f"   Probando etiqueta: {label}")
            _ = pkcs11.PKCS11Signer(pkcs11_session=session, cert_label=label)
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
        self.signer = pkcs11.PKCS11Signer(pkcs11_session=session, cert_label=self.cert_label,
                                          key_label="KprivFirmaDigital")
        
        logger.info(f"DNIe configurado con certificado: {self.cert_label}")
        
    except Exception as e:
      logger.error(f"Error configurando DNIe: {str(e)}")
      raise


  def sign_pdf(self, pdf_bytes: bytes, reason: str = "Firmado digitalmente",
      location: str = "España", contact_info: Optional[str] = None) -> bytes:
    """
    Firma un PDF usando pyHanko
    
    Args:
        pdf_bytes:      Contenido del PDF en bytes
        reason:         Razón de la firma
        location:       Ubicación
        contact_info:   Información de contacto
    
    Returns:
        PDF firmado en bytes
    """
    try:
      if self.signer is None:
          raise ValueError("No hay firmante configurado")
      
      # Cargo PDF en memoria
      pdf_stream = BytesIO(pdf_bytes)
      writer = IncrementalPdfFileWriter(pdf_stream)
      
      # Calculo donde irá la firma... ultima página la final
      page_count = len(writer.root['/Pages']['/Kids'])
      last_page_ref = writer.root['/Pages']['/Kids'][page_count - 1]
      last_page = last_page_ref.get_object()
      
      media_box = last_page['/MediaBox']
      page_width = float(media_box[2])
      page_height = float(media_box[1])
      
      margin = 15
      signature_height = 50
      
      sig_field_spec = SigFieldSpec(
        sig_field_name='Signature',
        box=(margin, margin, page_width - margin, margin + signature_height),
        on_page=page_count - 1
      )
      
      # Metadatos de la firma
      signature_meta = signers.PdfSignatureMetadata(
        field_name='Signature',
        location=location, reason=reason,
        contact_info=contact_info, md_algorithm='sha256',
      )
      
      # Se firma el documento
      signed_pdf = signers.sign_pdf(
        writer,
        signature_meta=signature_meta, signer=self.signer,
        existing_fields_only=False, new_field_spec=sig_field_spec
      )
      
      signed_data = signed_pdf.getvalue()
      
      logger.info("PDF firmado correctamente")
      return signed_data
        
    except Exception as e:
      logger.error(f"Error firmando PDF: {e}")
      raise

