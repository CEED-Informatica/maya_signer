# -*- coding: utf-8 -*-

import logging
import base64

import xmlrpc.client

from typing import Dict, List

logger = logging.getLogger("maya_signer")

import xmlrpc.client
from datetime import datetime

class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=30):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        conn.timeout = self.timeout
        return conn

class OdooConnectionError(Exception):
    """
    Error de conexión con Odoo
    """
    pass

class OdooAuthenticationError(Exception):
    """
    Error de autenticación
    """
    pass

class OdooClient(object):
  """
  Cliente para comunicación con Maya (Odoo) vía XML-RPC
  """
    
  def __init__(self, url: str, db: str, username: str, password: str):
    self.url = url.rstrip('/')
    self.db = db
    self.username = username
    self.password = password
    self.uid = None

    transport = TimeoutTransport(timeout=60)
    
    # Endpoints XML-RPC
    try:
      self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common',  transport=transport, allow_none=True)
      self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', transport=transport, allow_none=True)
    except Exception as e:
      raise OdooConnectionError(f"No se pudo conectar a {self.url}: {str(e)}")
    
  def authenticate(self) -> bool:
    """
    Autentica con Odoo y obtiene el uid del usuario
    """
    try:
      self.uid = self.common.authenticate(
        self.db,  
        self.username, 
        self.password, 
        {}
      ) 

      if not self.uid:
        raise OdooAuthenticationError(
            f"Credenciales inválidas para {self.username} en {self.db}"
        )
            
      logger.info(f"\tAutenticación correcta (UID: {self.uid})")
      return True
            
    except xmlrpc.client.Fault as e:
      raise OdooAuthenticationError(f"Error XML-RPC: {e.faultString}")
    
  def execute(self, model: str, method: str, args = None, kwargs = None):
    """
    Ejecuta un método en Odoo
    """
    if not self.uid:
      raise OdooAuthenticationError("No autenticado. Hay que ejecutar previamente authenticate()")
    
    args = args or []
    kwargs = kwargs or {}
    
    try:
      #logger.info(f"Ejecutando {self.db} {model}.{method}  args: {args} ({type(args)}), kwargs: {kwargs}")
     
      result = self.models.execute_kw(
          self.db,
          self.uid,
          self.password,
          model,
          method,
          args,
          kwargs
      )
   
      return result
      
    except xmlrpc.client.Fault as e:
      logger.error(f"Error XML-RPC en {model}.{method}: {e.faultString}")
      raise
    except Exception as e:
      logger.error(f"Error ejecutando {model}.{method}: {e}")
      raise

  def get_batch_info(self, batch_id: int) -> Dict | None:
    """
    Obtiene información del lote de firma
    """
    try:
      batch = self.execute(
            'maya_core.signature.batch',
            'read',
            args = [[batch_id]],
            kwargs = {'fields': ['name', 'document_ids', 'state']}
      )
      if batch:
        logger.info(f"\tLote {batch_id}: {batch[0]['name']} - Estado: {batch[0]['state']}")
        return batch[0]
            
      return None
            
    except Exception as e:
      logger.error(f"Error obteniendo info del lote {batch_id}: {str(e)}")
    
    return batch[0] if batch else None
    
  def download_unsigned_pdfs(self, batch_id: int) -> List[Dict]:
    """
    Descarga los PDFs sin firmar del lote

    Args:
      batch_id: ID del lote

    Returns:
      Lista de diccionarios con información de documentos:
      [
          {
              'id': int,
              'pdf_content': str (base64),
              'pdf_bytes': bytes,
              'pdf_filename': str,
              'model': str,
              'record_id': int
          },
          ...
      ]
    """
    logger.info(f"\tDescargando PDFs del lote {batch_id}...")

    # obtebno info del lote
    batch = self.get_batch_info(batch_id)
    if not batch:
      raise ValueError(f"Lote {batch_id} no encontrado")
    
    if batch['state'] == 'done':
      raise ValueError(f"Lote {batch_id} ya está firmado")
    
    document_ids = batch.get('document_ids', [])
    if not document_ids:
      raise ValueError(f"Lote {batch_id} no tiene documentos")
    
    documents = self.execute(
      'maya_core.signature.batch_document',
      'read',
      args = [document_ids],
      kwargs = {'fields': ['id', 'filename', 'state','res_model', 'pdf_content']}
    )
        
    # Decodifico los PDFs
    unsigned_docs = []
    for doc in documents:
      if doc['state'] == 'signed':
        logger.warning(f"\tDocumento {doc['id']} ya está firmado, omitiendo...")
        continue
    
      if not doc.get('pdf_content'):
        logger.warning(f"\tDocumento {doc['id']} no tiene contenido PDF")
        continue
      
      try:
        doc['pdf_bytes'] = base64.b64decode(doc['pdf_content'])
        unsigned_docs.append(doc)
        logger.debug(f"\tPDF descargado: {doc['filename']} ({len(doc['pdf_bytes'])} bytes)")
      except Exception as e:
        logger.error(f"\tError decodificando PDF {doc['id']}: {e}")
        
    logger.info(f"\tDescargados {len(unsigned_docs)} PDFs del lote {batch_id}")

    return unsigned_docs
  
  def upload_signed_pdf(self, document_id: int, signed_pdf_bytes: bytes, 
                          signed_filename: str) -> bool:
    """
    Sube un PDF firmado individual
    
    Args:
      document_id: ID del documento en el lote
      signed_pdf_bytes: Bytes del PDF firmado
      signed_filename: Nombre del archivo firmado
        
    Returns:
      bool: True si se subió correctamente
    """
    try:
      # Lo paso a base64
      signed_content = base64.b64encode(signed_pdf_bytes).decode('utf-8')
      
      # Actualizo documento en el lote
      self.execute(
        'maya_core.signature.batch_document',
        'write',
        args=[[document_id], {  # ← Lista con [ids, valores]
                'signed_pdf': signed_content,
                'signed_pdf_filename': signed_filename,
                'state': 'signed',
                'sign_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }],
        kwargs={}
      )
        
      logger.debug(f"\tPDF firmado subido: {signed_filename}")
      return True
        
    except Exception as e:
      logger.error(f"\tError subiendo PDF firmado {document_id}: {e}")
      return False
    
  def upload_signed_pdfs(self, batch_id: int, signed_documents: List[Dict]) -> bool:
    """
    Sube múltiples PDFs firmados a Odoo
    
    Args:
      batch_id: ID del lote
      signed_documents: Lista de diccionarios:
        [
            {
                'document_id': int,
                'signed_pdf_bytes': bytes,
                'signed_filename': str,
                'model': str (opcional),
                'record_id': int (opcional)
            },
            ...
        ]
            
    Returns:
      bool: True si todos se subieron correctamente
    """
    logger.info(f"Subiendo {len(signed_documents)} PDFs firmados al lote {batch_id}...")
    
    success_count = 0
    failed_count = 0
    
    for doc in signed_documents:
      try:
        document_id = doc['document_id']
        signed_pdf_bytes = doc['signed_pdf_bytes']
        signed_filename = doc.get('signed_filename', f'signed_{document_id}.pdf')
        
        # Subir PDF firmado
        if self.upload_signed_pdf(document_id, signed_pdf_bytes, signed_filename):
          success_count += 1
          
          # Si se proporciona modelo y record_id, actualizar el registro original
          if doc.get('model') and doc.get('document_id'):
            try:
              self.execute(
                doc['model'],
                'write',
                # los datos se añaden al registro principal a traves de SignatureMixin
                args=[[doc['document_id']], { 
                  'signed_pdf': base64.b64encode(signed_pdf_bytes).decode(),
                  'signed_pdf_filename': signed_filename,
                  'signature_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  'signature_user_id': self.uid
                }],   
                kwargs={},
              )
            except Exception as e:
              logger.warning(f"\tNo se pudo actualizar registro original: {str(e)}")
        else:
            failed_count += 1
              
      except Exception as e:
        logger.error(f"\tError procesando documento: {str(e)}")
        failed_count += 1
    
    # Actualizo el estado del lote si todos se firmaron
    if failed_count == 0:
      self.update_batch_state(batch_id, 'done')
    else:
      self.update_batch_state(batch_id, 'error')
    
    logger.info(f"\tSubidos {success_count}/{len(signed_documents)} PDFs")
    
    return failed_count == 0
    
  def update_batch_state(self, batch_id: int, state: str) -> bool:
    """
    Actualiza el estado del lote
    
    Args:
        batch_id: ID del lote
        state: Nuevo estado ('draft', 'done', 'error')
        
    Returns:
        bool: True si se actualizó correctamente
    """
    try:
      self.execute(
          'maya_core.signature.batch',
          'write',
          args=[[batch_id], {'state': state}] ,
          kwargs={}
      )
      logger.info(f"\tLote {batch_id} -> {state}")
      return True
    except Exception as e:
      logger.error(f"Error actualizando estado del lote: {e}")
      return False
  

  def test_connection(self) -> Dict:
    """
    Prueba la conexión con Odoo
    
    Returns:
      Dict con información de la conexión
    """
    try:
      version_info = self.common.version()
      
      result = {
          'success': True,
          'server_version': version_info.get('server_version'),
          'protocol_version': version_info.get('protocol_version'),
          'url': self.url,
          'database': self.db
      }
      
      logger.info(f"Conexión realizada con éxito a {self.url}")
      return result
      
    except Exception as e:
      logger.error(f"Error de conexión: {e}")
      return {
        'success': False,
        'error': str(e)
      }
