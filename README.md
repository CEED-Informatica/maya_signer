# Maya | Signer

Servicio local de firma digital automática para _Maya_ (Odoo). Permite firmar documentos PDF con certificados digitales o DNIe directamente desde el navegador, sin descargas ni subidas manuales.

Su objetivo es permitir la firma electrónica desde dentro de _Maya_, teniendo en cuenta que tanto los certificados digitales como el DNIe están en el PC del usuario y que, por seguridad, el navegador no puede acceder al hardware local (lector DNIe, certificados).

**Maya | Signer**  actúa como puente entre _Maya_ (Odoo, es decir la web) y el hardware de firma (local)

## Descripción

**Maya | Signer** es una aplicación de escritorio que:

1. **Descarga PDFs** automáticamente desde Maya.
2. **Firma localmente** con DNIe o certificado digital.
3. **Sube los PDFs firmados** de vuelta a Maya.