

import logging

from email import parser
import sys
import os
from pathlib import Path
import argparse

from signature_worker import SignatureWorker 
from maya_signer_service import MayaSignerService

import console_message_color as cmc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.odoo_signer' / 'service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
  from PySide6.QtWidgets import QApplication
  HAS_GUI = True
except ImportError:
  HAS_GUI = False
  print(f"{cmc.error()} PySide6 no instalado. Modo consola únicamente.")
  print(f"        Instala con una de estas dos opciones:\n          - pip install PySide6\n          - {cmc.info('[RECOMENDADA]')} pip install -r requirements.txt")


def leer_pdfs_de_carpeta(ruta_carpeta: str):
    """
    Generadao por Grok
    """
    lista_pdfs = []    

    if not os.path.isdir(ruta_carpeta):
        raise ValueError(f"La carpeta '{ruta_carpeta}' no existe o no es un directorio.")
    
    # Recorre todos los archivos de la carpeta
    for nombre_archivo in os.listdir(ruta_carpeta):
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        
        # Solo procesamos archivos (no subcarpetas) que terminen en .pdf
        if os.path.isfile(ruta_completa) and nombre_archivo.lower().endswith('.pdf'):
            try:
                with open(ruta_completa, 'rb') as f:
                    pdf_bytes = f.read()
                
                lista_pdfs.append({
                    'pdf_filename': nombre_archivo,           # ej: "certificado_123.pdf"
                    'pdf_bytes': pdf_bytes,                   # bytes del PDF
                })
                
                print(f"✓ Leído: {nombre_archivo}")
                
            except Exception as e:
                print(f"✗ Error leyendo {nombre_archivo}: {e}")
    
    print(f"\nTotal de PDFs leídos: {len(lista_pdfs)}")

    return lista_pdfs

if __name__ == '__main__':
  """ signer = PyHankoSigner(cert_password='XXXXXXXXXX')

    ruta = "Prueba.pdf"
    ruta_firmado = "Prueba_signed.pdf"

    with open(ruta, 'rb') as f:
        pdf_bytes = f.read()

    signed_pdf = signer.sign_pdf(
        pdf_bytes,
        reason="Firmado digitalmente desde Maya | Signer",
        location="España"
    )

    with open(ruta_firmado, 'wb') as f:  
      f.write(signed_pdf)
 """
"""   carpeta = "./prueba_pdf"

  pdfs = leer_pdfs_de_carpeta(carpeta)

  worker = SignatureWorker(pdfs, use_dnie = True, cert_password = 'XXXXXXXXXX')
  worker.start()


  worker.join() """

def install_protocol():
  """
  Instala el protocolo maya://
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


def main():  
  parser = argparse.ArgumentParser(description='Maya Signer - Servicio de firma electrónica para Maya')

  parser.add_argument('url', nargs='?', help='URL del protocolo maya://')
  parser.add_argument('--install-protocol', action='store_true', help='Instala el protocolo maya:// en el sistema')
  parser.add_argument('--uninstall-protocol', action='store_true', help='Desinstala el protocolo maya:// del sistema')
  parser.add_argument('--version', action='version', version='Maya Signer 1.0')     

  args = parser.parse_args()

  logger.info(f"Arrancando Maya Signer")

  if args.install_protocol:
    return install_protocol()
    
  if args.uninstall_protocol:
    return uninstall_protocol()
    
  if HAS_GUI:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    service = MayaSignerService()
    
    # Si se pasa URL como argumento, procesarla
    if len(sys.argv) > 1:
      service.handle_protocol(sys.argv[1])
    else:
      service.show()
        
    sys.exit(app.exec())
  else:
    print(f"{cmc.error()} Se requiere PySide6 para GUI")
    sys.exit(1)


if __name__ == '__main__':
    main()