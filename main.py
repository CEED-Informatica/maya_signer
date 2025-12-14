from signature_worker import SignatureWorker 

import os

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
  carpeta = "./prueba_pdf"

  pdfs = leer_pdfs_de_carpeta(carpeta)

  worker = SignatureWorker(pdfs, 'XXXXXXXXXX')
  worker.start()


  worker.join()