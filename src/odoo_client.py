# -*- coding: utf-8 -*-

import logging
import base64

import xmlrpc.client

from typing import Dict, List

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

logger = logging.getLogger(__name__)

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
    
    # Endpoints XML-RPC
    try:
      self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', allow_none=True)
      self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', allow_none=True)
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
            
      logger.info(f"Autenticación correcta (UID: {self.uid})")
      return True
            
    except xmlrpc.client.Fault as e:
      raise OdooAuthenticationError(f"Error XML-RPC: {e.faultString}")
    
  def execute(self, model: str, method: str, *args, **kwargs):
    """
    Ejecuta un método en Odoo
    """
    if not self.uid:
      raise OdooAuthenticationError("No autenticado. Hay que ejecutar previamente authenticate()")
    
    try:
      logger.info(f"Ejecutando {model}.{method}")
      
      result = self.models.execute_kw(
          self.database,
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
            [batch_id],
            {'fields': ['name', 'document_ids', 'state']}
      )
      if batch:
        logger.info(f"Lote {batch_id}: {batch[0]['name']} - Estado: {batch[0]['state']}")
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
    logger.info(f"Descargando PDFs del lote {batch_id}...")

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
      document_ids,
      {'fields': ['id', 'pdf_content', 'pdf_filename', 'model', 'record_id','is_signed']}
    )
        
    # Decodifico los PDFs
    unsigned_docs = []
    for doc in documents:
      if doc.get('is_signed'):
        logger.warning(f"Documento {doc['id']} ya está firmado, omitiendo...")
        continue
    
      if not doc.get('pdf_content'):
        logger.warning(f"Documento {doc['id']} no tiene contenido PDF")
        continue
      
      try:
        doc['pdf_bytes'] = base64.b64decode(doc['pdf_content'])
        unsigned_docs.append(doc)
        logger.debug(f"PDF descargado: {doc['pdf_filename']} ({len(doc['pdf_bytes'])} bytes)")
      except Exception as e:
        logger.error(f"Error decodificando PDF {doc['id']}: {e}")
        
    logger.info(f"✓ Descargados {len(unsigned_docs)} PDFs del lote {batch_id}")

    return unsigned_docs