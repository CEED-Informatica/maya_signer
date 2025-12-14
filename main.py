from hanko_signer import PyHankoSigner 

if __name__ == '__main__':
    signer = PyHankoSigner(cert_password='XXXXXXXXXX')

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