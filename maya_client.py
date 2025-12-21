# -*- coding: utf-8 -*-

import logging

import xmlrpc.client
import console_message_color as cmc


logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

logger = logging.getLogger(__name__)

class MayaClient(object):
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
    self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
    self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
    
  def authenticate(self) -> bool:
    """
    Autentica con Odoo
    """
    try:
      self.uid = self.common.authenticate(
        self.db,  
        self.username, 
        self.password, 
        {}
      )  
      return self.uid is not None
  
    except Exception as e:
      logger.error(f"Error autenticando: {str(e)}")
      return False

  