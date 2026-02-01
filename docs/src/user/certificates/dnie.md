# DNIe (Documento Nacional de Identidad electrónico)

Guía para firmar con tu DNIe físico.

## ¿Qué es el DNIe?

El [DNIe](https://www.dnielectronico.es/PortalDNIe/) es tu Documento Nacional de Identidad con un **chip electrónico** que contiene:

- Un certificado de firma digital
- Tu clave privada (no se puede extraer del chip)
- Tu información personal verificada por el Estado

::: info Ventaja del DNIe
Como la clave privada está en el chip físico, es **más seguro** que un certificado .p12 guardado en el disco.
:::

## Requisitos

### Hardware

- **DNIe** (versión 3.0 o superior)
- **Lector de tarjetas** compatible (Smart Card Reader)

Lectores recomendados:

| Lector | Compatibilidad | Precio aproximado (01/26) |
|--------|----------------|-------------------|
| ACR38U-I | Windows/Linux/macOS | ~15€ |
| Identive SCM3811 | Windows/Linux/macOS | ~20€ |
| Cualquier lector PC/SC | Varía | 10-30€ |

### Software por Plataforma

::: code-group

```bash [Linux]
# Instalar OpenSC y pcscd
sudo apt-get install opensc pcscd pcsc-tools

# Habilitar e iniciar pcscd
sudo systemctl enable pcscd
sudo systemctl start pcscd
```

```powershell [Windows]
# Windows incluye soporte PC/SC nativo
# Solo necesitas instalar el driver del lector
# Descárgalo desde la página del fabricante del lector
```

```bash [macOS]
# macOS incluye soporte PC/SC nativo
# Solo necesitas instalar el driver del lector
# Si no funciona con el driver nativo:
brew install pcsc-lite
brew services start pcsc-lite
```

:::

## Verificar que Todo Está Preparado

### 1. Verificar que el lector está conectado

::: code-group

```bash [Linux]
# Escanear lectores
pcsc_scan
# Debe mostrar tu lector y "Card present" cuando metes el DNIe
```

```powershell [Windows]
# Ver lectores conectados
sc query "Smart Card" state= all
```

```bash [macOS]
# Ver lectores
pcsctest
```

:::

### 2. Verificar certificados en el DNIe

```bash
# Solo Linux/macOS - listar certificados del DNIe
pkcs11-tool --module /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so --list-objects --type cert

# Debe mostrar:
#   CKA_LABEL: CertAutenticacion
#   CKA_LABEL: CertFirmaDigital   ← Este es el que usa Maya Signer
#   CKA_LABEL: CertDigitalIdentity
```

## Usar DNIe en Maya | Signer

### En el diálogo de credenciales

1. **Conecta** tu lector con el DNIe dentro
2. **Marca** la casilla "Usar DNIe"
3. Introduce tu **PIN del DNIe**
4. Haz clic en **Firmar**

::: warning PIN del DNIe
El PIN es un código que te dieron cuando activaste tu DNIe. 

Si lo has perdido/olviado o el certificado está caducado/bloqueado puedes ir a una Comisaría de Policia donde expidan el DNI y recuperarlo desde las máquinas existentes en las oficinas.
:::

### Proceso de firma con DNIe

A diferencia del certificado .p12, con DNIe necesitas **confirmar cada firma individualmente**:

1. **Maya | Signer** intenta firmar el primer documento
2. El sistema operativo muestra un diálogo pidiendo tu PIN
3. Introduces el PIN
4. El documento se firma
5. Se solicita confirmación para cada documento del lote

::: tip Lotes grandes
Si tienes que firmar muchos documentos, considera usar un **certificado .p12** en lugar del DNIe. Es mucho más rápido porque no necesita confirmación individual.
:::

## Problemas Comunes

### "DNIe no detectado"

1. Verifica que el lector está conectado y funciona
2. Prueba con otro puerto USB
3. Asegúrate de que el DNIe está bien insertado en el lector

En Linux:
```bash
# Verificar pcscd
sudo systemctl status pcscd

# Si no está activo
sudo systemctl start pcscd

# Escanear
pcsc_scan
```

### "Error PKCS#11"

En Linux, el módulo PKCS#11 puede estar en diferentes ubicaciones:

```bash
# Buscar el módulo
find / -name "opensc-pkcs11.so" 2>/dev/null

# Ubicaciones habituales:
# /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so
# /usr/lib/opensc-pkcs11.so
# /usr/local/lib/opensc-pkcs11.so
```

Si no lo encuentra automáticamente, define la variable de entorno:

```bash
export PKCS11_MODULE=/ruta/a/opensc-pkcs11.so
```

### "PIN incorrecto"

- Verifica que estás introduciendo el PIN correcto.
- Después de varios intentos (3) fallidos el DNIe puede bloquearse.
- Para desbloquearlo, ve a una Comisaría de Policía.

### "Certificado no encontrado en el DNIe"

El DNIe debe tener activado el certificado de firma. Si es un DNIe nuevo:

1. Ve a una Comisaría de Policía.
2. Solicita la activación del certificado de firma.
3. Es un trámite gratuito y rápido.