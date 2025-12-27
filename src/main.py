#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Punto de entrada al servicio de firma
Es un cliente muy sencillo de http

Se encarga de:
- redirigir las peticiones al servicio de firma
- instalar/desinstalar el protocolo maya://
"""

from custom_logging import setup_logger  # logging local
import requests
import sys
import argparse

from urllib.parse import urlparse, parse_qs

import subprocess
import time
from maya_signer_service import main as service_main

from pathlib import Path

SERVICE_PORT = 50304                    ## inventado
SERVICE_URL = f"http://127.0.0.1:{SERVICE_PORT}"

logger = setup_logger("client.log", __name__)

def is_service_running():
  """
  Verifica si el servicio está ejecutándose
  """
  try:
    response = requests.get(f"{SERVICE_URL}/health", timeout=2)
    return response.status_code == 200
  except:
    return False

def parse_protocol_url(url):
  """
  Parsea una URL del protocolo maya://
  """
  parsed = urlparse(url)
  params = parse_qs(parsed.query)
  
  return {
    'batch': params.get('batch', [None])[0],
    'url': params.get('url', [None])[0],
    'database': params.get('db', [''])[0],
  }

def handle_protocol_call(url):
  """
  Gestiona la llamada del protocolo
  """
  logger.info(f"Procesando: {url}")
    
  params = parse_protocol_url(url)
    
  if not params['batch'] or not params['url']:
    logger.error("Faltan parámetros requeridos (batch, url)")
    return 1
    
  # compruebo si el servicio está corriendo
  if not is_service_running():
    logger.info("Servicio no encontrado, iniciando...")
    if not start_service():
      logger.error("No se pudo iniciar el servicio")
      return 1
    
  # Envio la petición al servicio
  if send_signature_request(params):
    logger.info("Petición procesada correctamente")
    return 0
  else:
    return 1
  
def send_signature_request(data):
  """
  Envía petición de firma al servicio
  """
  try:
    response = requests.post(
        SERVICE_URL,
        json=data,
        timeout=10
    )
    
    if response.status_code == 200:
      logger.info("Petición enviada al servicio")
      return True
    else:
      logger.error(f"Error del servicio: {response.status_code}")
      return False
        
  except Exception as e:
    logger.error(f"Error al comunicar con el servicio: {str(e)}")
    return False

   
def start_service():
  """
  Inicia el servicio persistente en background
  """
  logger.info("Iniciando Maya Signer Service...")
    
  # Buscar el ejecutable del servicio
  if getattr(sys, 'frozen', False):
    # Ejecutable compilado
    base_path = Path(sys.executable).parent
    service_exe = base_path / "maya-signer-service"
    if sys.platform == 'win32':
      service_exe = base_path / "maya-signer-service.exe"
  else:
    # Modo desarrollo
    base_path = Path(__file__).parent
    service_exe = base_path / "maya_signer_service.py"
  
  if not service_exe.exists():
    logger.error(f"Servicio no encontrado: {service_exe}")
    return False
  
  try:
    # Iniciar en background
    if sys.platform == 'win32':
      # Windows: usar subprocess sin ventana
      DETACHED_PROCESS = 0x00000008
      subprocess.Popen(
          [str(service_exe)],
          creationflags=DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL
      )
    else:
      # Unix: usar nohup
      subprocess.Popen(
          [sys.executable, str(service_exe)],
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          start_new_session=True
      )
  
    # Espero a que inicie
    for _ in range(10):
      time.sleep(0.5)
      if is_service_running():
        logger.info("Servicio iniciado correctamente")
        return True
  
    logger.info("El servicio tardó demasiado en iniciar")
    return False
        
  except Exception as e:
    logger.error(f"Error al iniciar servicio: {str(e)}")
    return False
    
def install_protocol():
  """
  Instala el protocolo maya://
  Creado por Claude Sonnet 4.5
  """
  # Buscar el script de instalación
  if getattr(sys, 'frozen', False):
      # Ejecutable compilado
      base_path = Path(sys._MEIPASS)
  else:
      # Modo desarrollo
      base_path = Path(__file__).parent.parent
  
  install_script = base_path / "installer" / "install_protocol.py"
  
  if not install_script.exists():
      print(f"✗ Script de instalación no encontrado: {install_script}")
      return 1
  
  # Ejecutar el instalador
  import subprocess
  return subprocess.call([sys.executable, str(install_script)])

def uninstall_protocol():
  """
  Desinstala el protocolo maya://
  Creado por Claude Sonnet 4.5
  """
  if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
  else:
    base_path = Path(__file__).parent.parent
  
  uninstall_script = base_path / "installer" / "uninstall.py"
  
  if not uninstall_script.exists():
    print(f"✗ Script de desinstalación no encontrado: {uninstall_script}")
    return 1
  
  import subprocess
  return subprocess.call([sys.executable, str(uninstall_script)])

def start_service_command():
  """
  Inicia el servicio manualmente
  ¡¡Usado para pruebas!!
  """
  return service_main()

def main():  
  parser = argparse.ArgumentParser(description='Maya Signer - Servicio de firma electrónica para Maya')

  parser.add_argument('url', nargs='?', help='URL del protocolo maya://')
  parser.add_argument('--install-protocol', action='store_true', help='Instala el protocolo maya:// en el sistema')
  parser.add_argument('--uninstall-protocol', action='store_true', help='Desinstala el protocolo maya:// del sistema')
  parser.add_argument('--start-service', action='store_true', help='Inicia el servicio')
  parser.add_argument('--version', action='version', version='Maya Signer 1.0')     

  args = parser.parse_args()

  logger.info(f"Arrancando Maya Signer")

  if args.install_protocol:
    return install_protocol()
    
  if args.uninstall_protocol:
    return uninstall_protocol()
  
  if args.start_service:
    return start_service_command()
  
  # Si no hay argumentos, arranco servicio por defecto
  if not args.url:
    logger.info("Iniciando Maya Signer Service (Modo desarrollo)...")
    return start_service_command()
    
  # Gestiona la llamada del protocolo
  if args.url.startswith('maya://'):
    return handle_protocol_call(args.url)
    
  logger.error(f"URL no reconocida: {args.url}")

  return 1

if __name__ == '__main__':
  sys.exit(main())  # entra, ejecuta el servidor y sale