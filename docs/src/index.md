---
layout: home

hero:
  name: "Maya | Signer"
  text: "Firma electrónica para Maya"
  tagline: Firma documentos PDF desde Maya (Odoo) con certificados digitales o DNIe
  image:
    src: /hero-logo.png
    alt: Maya Signer
  actions:
    - theme: brand
      text: Comenzar
      link: /user/getting-started
    - theme: alt
      text: Ver en GitHub
      link: https://github.com/Maya-AQSS/maya-signer/

features:
  - icon: 🔒
    title: Firma Segura
    details: Utiliza certificados digitales .p12/.pfx o DNIe para firmar documentos con validez legal
  
  - icon: 🔗
    title: Integración Perfecta
    details: Se integra nativamente con Maya (Odoo) mediante protocolo personalizado maya://
  
  - icon: 🖥️
    title: Multiplataforma
    details: Funciona en Linux, Windows y macOS con instaladores nativos para cada plataforma
  
  - icon: 🎨
    title: Fácil de Usar
    details: Interfaz gráfica intuitiva para gestionar credenciales y ver el estado de las firmas
  
  - icon: 🔄
    title: Firma por Lotes
    details: Firma múltiples documentos de una sola vez de forma eficiente
  
  - icon: 🚀
    title: Servicio en Background
    details: El servicio corre en segundo plano, siempre listo para firmar cuando lo necesites
---

## Instalación Rápida

::: code-group

```bash [Linux]
# Descargar e instalar
sudo dpkg -i maya-signer_X.X.X_amd64.deb
sudo apt-get install -f

# Para DNIe
sudo apt-get install opensc pcscd
```

```powershell [Windows]
# Descargar maya-signer_X.X.X_x64.msi
# Doble clic → Siguiente → Instalar
```

```bash [macOS]
# Abrir maya-signer_X.X.X_macOS.dmg
# Arrastrar MayaSigner.app a Applications
# Abrir desde Applications
```

:::

## ¿Cómo Funciona?

<center>

```mermaid
graph LR
    A[Maya/Odoo] -->|maya://| B[Maya Signer]
    B -->|Solicita| C[Credenciales]
    C -->|Certificado/DNIe| B
    B -->|Firma| D[Documentos PDF]
    D -->|Devuelve| A
```

</center>

1. **Usuario hace clic en "Firmar"** en _Maya_ (Odoo)
2. **Se abre el protocolo `maya://`** que lanza _Maya | Signer_
3. **Se solicitan credenciales** (solo primera vez)
4. **Se firman los documentos** con el certificado o DNIe
5. **Se devuelven firmados** a Maya automáticamente

## Características Principales

### Seguridad

- Credenciales almacenadas solo en memoria durante la sesión
- Validación de tokens de sesión con expiración
- Firma en proceso aislado sin acceso a red

### Facilidad de Uso

- Registro automático del protocolo `maya://`
- Interfaz gráfica sencilla e intuitiva
- Notificaciones en bandeja del sistema
- Sin configuración manual necesaria

### Flexibilidad

- Soporte para certificados .p12/.pfx
- Soporte para DNIe (Documento Nacional de Identidad electrónico)
- Múltiples servidores Maya simultáneos

## Próximos Pasos

<div class="vp-doc" style="margin-top: 2rem;">

**Para Usuarios:**
- [Instalación detallada](/user/installation)
- [Primer uso](/user/first-use)
- [Firmar documentos](/user/signing)

**Para Desarrolladores:**
- [Configurar entorno](/dev/setup)
- [Arquitectura](/dev/architecture)
- [Compilar instaladores](/dev/building/overview)

</div>

## Soporte

¿Necesitas ayuda? Tenemos varias opciones:

- 📖 [Documentación completa](/user/getting-started)
- 🐛 [Reportar un bug](https://github.com/Maya-AQSS/maya-signer/issues)