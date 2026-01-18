#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestor de firma mediante subprocesos externos al servidor
"""

import logging
import subprocess
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from tempfile import mkdtemp

logger = logging.getLogger("maya_signer")

class SubprocessSignatureManager:
  """
  Gestiona la firma de documentos mediante subproceso independiente
  """
    
  def __init__(self, worker_script: Optional[Path] = None):
    """
    Args:
        worker_script: Ruta al script signer_worker.py
                       Si es None, busca en el mismo directorio
    """
    if worker_script is None:
      # Busco signer_worker.py en el mismo directorio
      worker_script = Path(__file__).parent / "signer_worker.py"
    
    self.worker_script = Path(worker_script)
    
    if not self.worker_script.exists():
      raise FileNotFoundError(f"Worker script no encontrado: {self.worker_script}")
    
    self.work_dir = None
    self.process = None
    
  def prepare_work_directory(self, documents: List[Dict]) -> Path:
    """
    Prepara directorio temporal con los documentos
        
    Args:
        documents: Lista con 'document_id', 'pdf_bytes', 'filename'
            
    Returns:
        Path al directorio de trabajo
    """
    # Creo el directorio temporal donde almacenaré los ficheros a firmar
    work_dir = Path(mkdtemp(prefix="maya_signer_"))
        
    logger.info(f"\tDirectorio de trabajo: {work_dir}")
        
    try:
      # Guardo los PDFs sin firmar
      for doc in documents:
        doc_id = doc['id']
              
        pdf_path = work_dir / f"unsigned_{doc_id}.pdf"
                
        with open(pdf_path, 'wb') as f:
          f.write(doc['pdf_bytes'])
        
        logger.debug(f"\tGuardado: {pdf_path.name}")
            
      logger.info(f"\t{len(documents)} documentos guardados")
            
      return work_dir
            
    except Exception as e:
      # Lo elimino si hay error
      shutil.rmtree(work_dir, ignore_errors=True)
      raise Exception(f"  Error preparando directorio: {str(e)}")
    
  def create_input_file(self, work_dir: Path, documents: List[Dict],
                         cert_path: Optional[str], cert_password: str,
                         use_dnie: bool):
    """
    Crea archivo de entrada para el worker
    
    Args:
      work_dir: Directorio de trabajo
      documents: Documentos a firmar
      cert_path: Ruta al certificado
      cert_password: Contraseña
      use_dnie: Si usar DNIe
    """

    input_data = {
      'cert_path': cert_path,
      'cert_password': cert_password,
      'use_dnie': use_dnie,
      'documents': [
        # por cada documento una tupla con su id, res_modelo, id del modelo vinculado (res_model) y el nombre del fichero
        { 'document_id': doc['id'], 'res_model': doc.get('res_model', ''), 
          'res_id': doc.get('res_id', ''), 'filename': doc.get('filename', f"doc_{doc['id']}.pdf") } for doc in documents
        ]
    }
    
    input_file = work_dir / "input.json"
    with open(input_file, 'w') as f:
      json.dump(input_data, f, indent=2)
    
    logger.info(f"\tArchivo de entrada creado: {input_file}")
    
  def start_worker(self, work_dir: Path) -> subprocess.Popen:
    """
    Inicia el subproceso worker
    
    Args:
      work_dir: Directorio de trabajo
        
    Returns:
      Proceso iniciado
    """
    import sys
    
    cmd = [sys.executable, str(self.worker_script), str(work_dir)]
    
    logger.info(f"  Iniciando worker: {' '.join(cmd)}")
    
    # Fichero de log para debug
    stdout_log = work_dir / "worker_stdout.log"
    stderr_log = work_dir / "worker_stderr.log"
    
    stdout_file = open(stdout_log, 'w')
    stderr_file = open(stderr_log, 'w')

    # Inicio del proceso independiente
    process = subprocess.Popen(
      cmd,
      stdout=stdout_file,
      stderr=stderr_file,
      cwd=work_dir,
      # No heredar nada del proceso padre!!!
      close_fds=False,  #  False para permitir logs
      # En Windows => crear proceso independiente : subprocess.CREATE_NEW_PROCESS_GROUP
      creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )

    process._stdout_file = stdout_file
    process._stderr_file = stderr_file
    
    logger.info(f"  Worker iniciado (PID: {process.pid})")
    logger.info(f"  Logs: {stdout_log} || {stderr_log}")
    
    return process
    
  def monitor_progress(self, work_dir: Path, 
                        progress_callback: Optional[Callable] = None,
                        timeout: int = 300) -> Dict:
    """
    Monitorea el progreso del worker
    
    Args:
      work_dir: Directorio de trabajo
      progress_callback: Función callback(current, total, message)
      timeout: Timeout en segundos
        
    Returns:
      Estado final
    """
    status_file = work_dir / "status.json"
    start_time = time.time()
    last_status = None
    
    logger.info("\tMonitoreando progreso del worker...")
        
    while True:
      # Compruebo  timeout
      elapsed = time.time() - start_time
      if elapsed > timeout:
        logger.error(f"\ŧTimeout alcanzado ({timeout}s)")
        return {
          'success': False,
          'error': f'Timeout después de {timeout}s',
          'status': 'timeout'
        }
        
      # Leo el fichero de  estado
      try:
        if status_file.exists():
          with open(status_file, 'r') as f:
            status = json.load(f)
        
          # si hay cambios llamo al callback
          if status != last_status:
            logger.info(
              f"\tEstado: {status.get('status')} - "
              f"{status.get('message', '')} "
              f"({status.get('progress', 0)}/{status.get('total', 0)})"
            )
                
            if progress_callback and status.get('progress'):
              progress_callback(
                status.get('progress', 0),
                status.get('total', 0),
                status.get('message', '')
              )
            
            last_status = status
            
          # ha acabado? 
          if status.get('status') in ['success', 'error']:
            return status
                
      except json.JSONDecodeError:
        pass
      except Exception as e:
        logger.error(f"\ŧError leyendo status: {e}")

        # espero un poco antes de la siguiente comprobación
        time.sleep(0.5)
    
  def read_results(self, work_dir: Path) -> List[Dict]:
    """
    Lee los resultados del worker
    
    Args:
      work_dir: Directorio de trabajo
        
    Returns:
      Lista de documentos firmados
    """
    output_file = work_dir / "output.json"
        
    if not output_file.exists():
      logger.error("\tArchivo de salida no encontrado")
      return []
    
    try:
      with open(output_file, 'r') as f:
        output_data = json.load(f)
        
      results = output_data.get('results', [])
        
      # Leer PDFs firmados
      signed_documents = []
        
      for result in results:
        if not result.get('success'):
          logger.warning(
            f"\tDocumento en lote {result.get('document_id')} ha fallado: "
            f"{result.get('error')}"
          )
          continue
        
        signed_filename = result['signed_filename']
        signed_path = work_dir / signed_filename
        
        if not signed_path.exists():
          logger.error(f"\tPDF firmado no encontrado: {signed_path}")
          continue
        
        with open(signed_path, 'rb') as f:
          signed_pdf_bytes = f.read()
        
        signed_documents.append({
          'document_id': result['document_id'],
          'res_model': result.get('res_model', ''),
          'res_id': result.get('res_id', ''), # documento vinculado
          'signed_pdf_bytes': signed_pdf_bytes,
          'signed_filename': result['original_filename'].replace('.pdf', '_firmado.pdf')
        })
        
        logger.info(f"\tLeído PDF firmado: {result['original_filename']}")
        
      return signed_documents
        
    except Exception as e:
      logger.error(f"\tError leyendo resultados: {str(e)}")
      return []
    
  def cleanup(self, work_dir: Path):
    """
    Elimina el directorio temporal
    
    Args:
      work_dir: Directorio a limpiar
    """
    try:
      if work_dir and work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
        logger.info(f"\tDirectorio eliminado: {work_dir}")
    except Exception as e:
      logger.warning(f"\tError limpiando directorio: {e}")
    
  def sign_documents(self, documents: List[Dict],
                      cert_path: Optional[str] = None,
                      cert_password: Optional[str] = None,
                      use_dnie: bool = False,
                      progress_callback: Optional[Callable] = None,
                      cleanup: bool = True) -> Dict:
    """
    Firma documentos usando un subproceso
    
    Args:
        documents: Lista con 'id', 'pdf_bytes', 'filename'
        cert_path: Ruta al certificado
        cert_password: Contraseña
        use_dnie: Si hay que usar DNIe
        progress_callback: Callback de progreso
        cleanup: Si limpiar archivos temporales al terminar
        
    Returns:
        Dict con 'success', 'signed_documents', 'error'
    """
    work_dir = None
    
    try:
      logger.info("=" * 60)
      logger.info("INICIANDO FIRMA CON SUBPROCESO")
      logger.info(f"  Documentos: {len(documents)}")
      logger.info(f"  Modo: {'DNIe' if use_dnie else 'Certificado'}")
      logger.info("=" * 60)
        
      logger.info("***** Preparando directorio de trabajo... *****")
      work_dir = self.prepare_work_directory(documents)
      self.work_dir = work_dir
        
      logger.info("***** Creando configuración... *****")
      self.create_input_file(work_dir, documents, cert_path, cert_password, use_dnie)
        
      logger.info("***** Iniciando worker... *****")
      self.process = self.start_worker(work_dir)
        
      logger.info("****** Monitoreando progreso... *****")
      final_status = self.monitor_progress(work_dir, progress_callback, timeout=300)
        
      logger.info("***** Esperando fin del proceso... *****")
      try:
        self.process.wait(timeout=10)
        returncode = self.process.returncode
        logger.info(f"\tWorker terminado (código: {returncode})")
      except subprocess.TimeoutExpired:
        logger.warning("\tWorker no terminó en 10s, forzando...")
        self.process.kill()
        returncode = -1
        
      if final_status.get('status') == 'success':
        logger.info("***** Leyendo documentos firmados... *****")
        signed_documents = self.read_results(work_dir)
        
        logger.info("=" * 60)
        logger.info(f"   FIRMA COMPLETADA")
        logger.info(f"   Firmados: {len(signed_documents)}/{len(documents)}")
        logger.info("=" * 60)
        
        return {
          'success': True,
          'signed_documents': signed_documents,
          'total_signed': len(signed_documents),
          'total_failed': len(documents) - len(signed_documents),
          'error': None
        }
      else:
        error_msg = final_status.get('message', 'Error desconocido')
        logger.error(f"\tError en firma: {error_msg}")
        
        return {
          'success': False,
          'signed_documents': [],
          'error': error_msg
        }
        
    except Exception as e:
      logger.error(f"Error crítico en SubprocessSignatureManager: {str(e)}")
        
      # Intentar matar proceso si existe
      if self.process and self.process.poll() is None:
        try:
          self.process.kill()
        except:
          pass
        
        return {
          'success': False,
          'signed_documents': [],
          'error': str(e)
        }
        
    finally:
        # Limpieza
        if cleanup and work_dir:
          self.cleanup(work_dir)

