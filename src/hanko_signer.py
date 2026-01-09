# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger("signer_worker")

# pyHanko
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat import backends

from io import BytesIO
import os

from typing import Optional


class PKCS11Error(Exception):
  """
  Error específico de PKCS#11
  """
  pass

class CertificateError(Exception):
  """
  Error relacionado con certificados
  """
  pass

class PyHankoSigner:
  """
  Wrapper para pyHanko que firma PDFs
  """
  
  def __init__(self,  cert_path: Optional[str] = None, cert_password: Optional[str] = None, 
               cert_label: Optional[str] = None, use_dnie: bool = False):
    
    self.cert_path = cert_path
    self.cert_label = cert_label
    self.cert_password = cert_password
    self.use_dnie = use_dnie
    self.signer = None

    # sesion pkcs11 para controlar su cierre
    self._pkcs11_session = None
    
    if not use_dnie and cert_path:
      self._load_certificate()
    elif use_dnie:
      self._setup_dnie()

  def _setup_dnie(self):
    """
    Configura firma con DNIe usando PKCS#11
    """
    try:
      from pyhanko.sign import pkcs11

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
              "- Linux: sudo apt-get install opensc\n"
              "- Windows: Instala el software del DNIe"
          )
          
      logger.info(f"Módulo PKCS#11: {pkcs11_lib}")
          
      # Abro sesión PKCS#11
      session= pkcs11.open_pkcs11_session(lib_location=pkcs11_lib, slot_no=0, user_pin=self.cert_password)
      self._pkcs11_session = session
        
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

  def _load_certificate(self):
    """
    Carga certificado .p12/.pfx
    """
    try:
      from pyhanko.sign import signers

      with open(self.cert_path, 'rb') as f:
        cert_data = f.read()
      
      # Cargar PKCS12
      private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
          cert_data,
          self.cert_password.encode() if self.cert_password else None,
          backend=backends.default_backend()
      )
      
      # Creo el firmante
      self.signer = signers.SimpleSigner(
        signing_cert=certificate,
        signing_key=private_key,
        cert_registry=signers.SimpleCertificateStore.from_certs(
            additional_certs or []
        )
      )
      
      logger.info(f"Certificado cargado: {self.cert_path}")
      
    except Exception as e:
      logger.error(f"Error cargando certificado: {str(e)}")
      raise

  def sign_pdf(self, pdf_bytes: bytes, reason: str = "Firmado electrónicamente",
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
      from pyhanko.sign import signers
      
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

  def close(self):
    """
    Cierra la sesión de PKCS#11.
    """
    if self._pkcs11_session:
      try:
        self._pkcs11_session.close()
        logger.info("Sesión PKCS#11 cerrada explícitamente.")
      except Exception as e:
        logger.warning(f"Error al cerrar la sesión PKCS#11: {e}")
      finally:
        self._pkcs11_session = None