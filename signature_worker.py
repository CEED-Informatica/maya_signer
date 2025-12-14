# -*- coding: utf-8 -*-

import logging
import multiprocessing 

from hanko_signer import PyHankoSigner 

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

logger = logging.getLogger(__name__)

class SignatureWorker(multiprocessing.Process):
  """
  Worker para procesar firma en segundo plano
  """

  def __init__(self, documents, cert_password: str = None):
    multiprocessing.Process.__init__(self)
    self.cert_password = cert_password
    self.documents = documents

  def run(self):
    """
    Proceso de firma
    """
    try:
      documents = self.documents
      logger.info(f"Descargados {len(documents)} documentos")
      
      signer = PyHankoSigner(
        cert_password=self.cert_password,
      )
      
      # Firmo cada PDF
      signed_documents = []
      total = len(documents)
      
      for i, doc in enumerate(documents):
        
        if not doc['pdf_bytes']:
          logger.warning(f"Documento {doc['id']} sin contenido")
          continue
      
        try:
          signed_pdf = signer.sign_pdf(
              doc['pdf_bytes'],
              reason="Firmado digitalmente desde Maya | Signer",
              location="España"
          )
          
          signed_documents.append({
              'signed_pdf_bytes': signed_pdf,
              'signed_filename': doc['pdf_filename'].replace('.pdf', '_firmado.pdf')
          })
          
          logger.info(f"Firmado: {doc['pdf_filename']}")
          
        except Exception as e:
          logger.error(f"Error firmando {doc['pdf_filename']}: {e}")
          continue

        for i,d in enumerate(signed_documents):
          with open(d['signed_filename'], 'wb') as f:  
            f.write(d['signed_pdf_bytes'])

          
    except Exception as e:
      logger.error(f"Error en proceso de firma: {e}", exc_info=True)

    finally:
      # Cierro la sesión
      if signer:
        signer.close()
          
      logger.info("Proceso de firma finalizado y recursos liberados.")
