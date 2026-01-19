#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Worker de firma 
Se ejecuta como subproceso separado sin Qt ni threading que 
dan problemas de colisiones
Comunicación realizadavía archivos JSON
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
import traceback

# Configurar logging ANTES de importar cualquier otra cosa
def setup_worker_logging(work_dir: Path):
  """
  Configura logging del worker 
  """
  log_file = work_dir / "worker.log"

  logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
  )

  return logging.getLogger("sign_worker")


class SignatureWorker:
  """
  Worker de firma sin dependencias de Qt ni threading
  """
    
  def __init__(self, work_dir: Path):
    self.work_dir = Path(work_dir)
    self.logger = setup_worker_logging(self.work_dir)
    
    self.status_file = self.work_dir / "status.json"
    self.input_file = self.work_dir / "input.json"
    self.output_file = self.work_dir / "output.json"
        
  def update_status(self, status: str, progress: int = 0, 
                     total: int = 0, message: str = ""):
    """
    Actualiza archivo de estado
    """
    try:
      status_data = {
        'status': status,  # 'working', 'success', 'error'
        'progress': progress,
        'total': total,
        'message': message
      }
            
      with open(self.status_file, 'w') as f:
        json.dump(status_data, f, indent=2)
                
    except Exception as e:
      self.logger.error(f"Error actualizando status: {str(e)}")
    
  def load_input(self) -> Dict:
    """
    Carga datos de entrada
    """
    try:
      with open(self.input_file, 'r') as f:
        return json.load(f)
    except Exception as e:
      self.logger.error(f"Error cargando input: {str(e)}")
      raise
    
  def save_output(self, results: List[Dict]):
    """
    Guarda resultados
    """
    try:
      with open(self.output_file, 'w') as f:
        json.dump({'results': results}, f, indent=2)
    except Exception as e:
      self.logger.error(f"Error guardando output: {e}")
      raise
    
  def sign_documents(self):
    """
    Proceso principal de firma
    """
    
    self.logger.info("=" * 60)
    self.logger.info("WORKER DE FIRMA INICIADO")
    self.logger.info(f"PID: {sys.platform} - {id(self)}")
    self.logger.info("=" * 60)

    print("=" * 60, file=sys.stderr, flush=True)
    print("WORKER EJECUTÁNDOSE", file=sys.stderr, flush=True)
    print(f"Work dir: {self.work_dir}", file=sys.stderr, flush=True)
    print("=" * 60, file=sys.stderr, flush=True)
    
    try:  
      self.update_status('working', message='Cargando configuración...')
        
        
      self.logger.info("Cargando configuración...")
      input_data = self.load_input()
        
      cert_path = input_data.get('cert_path')
      cert_password = input_data.get('cert_password')
      use_dnie = input_data.get('use_dnie', False)
      documents = input_data.get('documents', [])
        
      if not documents:
        raise ValueError("No hay documentos para firmar")
        
      self.logger.info(f"Documentos a firmar: {len(documents)}")
      self.logger.info(f"Modo: {'DNIe' if use_dnie else 'Certificado'}")
         
      self.update_status('working', message='Inicializando firmador...')
      self.logger.info("Importando módulos de firma...")
        
      try:
        from hanko_signer import PyHankoSigner, PKCS11Error, CertificateError
        self.logger.info("Módulos importados correctamente")
      except ImportError as e:
        self.logger.error(f"Error importando hanko_signer: {e}")
        self.update_status('error', message=f"Error importando módulos: {str(e)}")
        return 1
        
      self.logger.info("Creando firmador...")
        
      try:
        signer = PyHankoSigner(
          cert_path=cert_path,
          cert_password=cert_password,
          use_dnie=use_dnie
        )
        self.logger.info("Firmador creado correctamente")
     
      except PKCS11Error as e:
        self.logger.error(f"Error PKCS11: {e}")
        self.update_status('error', message=f"Error DNIe: {str(e)}")
        return 1
        
      except CertificateError as e:
        self.logger.error(f"Error certificado: {str(e)}")
        self.update_status('error', message=f"Error certificado: {str(e)}")
        return 1
        
        
      results = []
      failed_count = 0
    
      for i, doc in enumerate(documents, 1):
        try:
          doc_id = doc['document_id']
          filename = doc['filename']
          pdf_path = self.work_dir / f"unsigned_{doc_id}.pdf"
            
          self.logger.info(f"Firmando {i}/{len(documents)}: {filename}")
          self.update_status(
            'working', 
            progress=i, 
            total=len(documents),
            message=f"Firmando {filename}..."
          )
            
          if not pdf_path.exists():
            self.logger.error(f"Archivo no encontrado: {pdf_path}")
            failed_count += 1
            continue
            
          with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            
          # Firmo
          signed_pdf = signer.sign_pdf(
            pdf_bytes,
            reason="Firmado electrónicamente desde Maya Signer",
            location="España"
          )   
            
          signed_filename = f"signed_{doc_id}.pdf"
          signed_path = self.work_dir / signed_filename
        
          with open(signed_path, 'wb') as f:
            f.write(signed_pdf)
        
          results.append({
            'document_id': doc_id,
            'res_model': doc.get('res_model', ''),
            'res_id': doc.get('res_id', ''),
            'signed_filename': signed_filename,
            'original_filename': filename,
            'success': True
          })
        
          self.logger.info(f"Firmado: {filename}")
            
        except Exception as e:
          self.logger.error(f"Error firmando {filename}: {e}")
          failed_count += 1
            
          results.append({
            'document_id': doc.get('document_id'),
            'original_filename': doc.get('filename'),
            'success': False,
            'error': str(e)
          })
        
      try:
        self.logger.info("Cerrando firmador...")
        signer.close()
        self.logger.info("Firmador cerrado")
      except Exception as e:
        self.logger.warning(f"Error cerrando firmador: {e}")
        
      self.logger.info("Guardando resultados...")
      self.save_output(results)
      
      success_count = len([r for r in results if r.get('success')])
      
      self.logger.info("=" * 60)
      self.logger.info(f"FIRMA COMPLETADA")
      self.logger.info(f"  Éxitos: {success_count}/{len(documents)}")
      self.logger.info(f"  Fallos: {failed_count}")
      self.logger.info("=" * 60)
      
      if success_count > 0:
        self.update_status(
          'success',
          progress=len(documents),
          total=len(documents),
          message=f"Firmados {success_count} de {len(documents)} documentos"
        )
        return 0
      else:
        self.update_status(
          'error',
          message="No se firmó ningún documento"
        )
        return 1
            
    except Exception as e:
      self.logger.error(f"ERROR CRÍTICO: {str(e)}")
      self.logger.error(traceback.format_exc())
      
      self.update_status(
        'error',
        message=f"Error crítico: {str(e)}"
      )
      return 1


def main():
     
  import sys
    
  print(f"Worker iniciado - PID: {id(sys.modules)}", file=sys.stderr, flush=True)
    
  if len(sys.argv) != 2:
    print("Uso: signer_worker.py <work_directory>", file=sys.stderr)
    return 1
    
  work_dir = Path(sys.argv[1])
    
  print(f"Work dir: {work_dir}", file=sys.stderr, flush=True)
    
  if not work_dir.exists():
    print(f"Directorio no existe: {work_dir}", file=sys.stderr)
    return 1
    
  try:
    worker = SignatureWorker(work_dir)
    print("Worker creado", file=sys.stderr, flush=True)
    return worker.sign_documents()
  except Exception as e:
    print(f"ERROR FATAL: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
    return 1


if __name__ == "__main__":
  sys.exit(main())
