# Maya | Signer

**Maya | Signer** es una aplicación de escritorio que permite firmar documentos PDF electrónicamente desde el sistema Maya (Odoo) usando certificados digitales o DNIe. 

[![License](https://img.shields.io/badge/license-GPL-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)](https://github.com/Maya-AQSS/maya-signer)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/Maya-AQSS/maya-signer)](https://github.com/Maya-AQSS/maya-signer/releases)

Su objetivo es permitir la firma electrónica de lotes de documentos desde dentro de _Maya_, teniendo en cuenta que tanto los certificados digitales como el DNIe están en el PC del usuario y que, por seguridad, el navegador no puede acceder a ellos.

**Maya | Signer**  actúa como puente entre _Maya_ (_Odoo_, es decir la web) y el hardware/software de firma (local).

## Características

- **Firma electrónica segura** con certificados .p12/.pfx o DNIe
- **Integración con Maya** vía protocolo personalizado `maya://`
- **Multiplataforma**: Linux, Windows y macOS
- **Interfaz gráfica** intuitiva para gestión de credenciales
- **Firma por lotes** de múltiples documentos
- **Servicio en background** siempre disponible
- **Instaladores nativos** para cada plataforma

## Descripción

**Maya | Signer** es una aplicación de escritorio que:

1. **Descarga PDFs** automáticamente desde Maya.
2. **Firma localmente** con DNIe o certificado digital.
3. **Sube los PDFs firmados** de vuelta a Maya.

## Instalación para Usuarios

### Descargar

Descarga el instalador para tu sistema desde [GitHub Releases](https://github.com/Maya-AQSS/maya-signer/releases/latest):

- **Linux**: `maya-signer_X.X.X_amd64.deb`
- **Windows**: `maya-signer_X.X.X_x64.msi`
- **macOS**: `maya-signer_X.X.X_macOS.dmg`

### Linux (Ubuntu/Debian)

```bash
sudo dpkg -i maya-signer_X.X.X_amd64.deb
sudo apt-get install -f  # Si hay dependencias faltantes
```

**Para DNIe:** Instala también:
```bash
sudo apt-get install opensc pcscd
sudo systemctl start pcscd
```

### Windows

1. Doble clic en `maya-signer_X.X.X_x64.msi`
2. Siguiente → Instalar

### macOS

1. Abre `maya-signer_X.X.X_macOS.dmg`
2. Arrastra `MayaSigner.app` a Applications
3. Abre desde _Applications_ (acepta permisos en primer arranque)

## Uso

1. **El servicio arranca automáticamente** en la bandeja del sistema
2. **Desde Maya (Odoo)**, haz clic en "Firmar documentos"
3. **Se abrirá Maya | Signer** automáticamente
4. **Introduce tus credenciales** (primera vez):
   - Usuario y contraseña de Maya
   - Certificado digital o selecciona "Usar DNIe"
   - Contraseña del certificado/DNIe
5. **Los documentos se firman** automáticamente.
6. **Las credenciales se guardan** en memoria durante la sesión, aunque es posible eliminarlas desde el menú que aparece a partir del icono de la bandeja.

## Desarrollo

### Requisitos

- Python 3.8+
- PyInstaller
- Dependencias específicas por plataforma:
  - **Linux**: `dpkg-dev`, `fakeroot`
  - **Windows**: [WiX Toolset](https://wixtoolset.org/)
  - **macOS**: `create-dmg` (vía Homebrew)

### Clonar repositorio

```bash
git clone https://github.com/Maya-AQSS/maya-signer.git
cd maya-signer
```

### Configurar entorno

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv     
source .venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar en modo desarrollo

```bash
# Arrancar el servicio
python src/maya_signer_service.py
```

### Compilar instaladores

```bash
# Linux
make build-deb

# Windows
make build-msi

# macOS
make build-dmg

# O genérico (detecta automáticamente tu plataforma)
make build
```

## Estructura del Proyecto

```
maya-signer/
├── src/                    # Código fuente
├── build/                  # Scripts de compilación
│   ├── maya-signer.spec    # PyInstaller
│   ├── build_deb.py        # Linux
│   ├── build_msi.py        # Windows
│   └── build_dmg.py        # macOS
├── docs/                   # Documentación (VitePress)
├── manifest.py             # Metadatos
├── Makefile                # Installer Build system
└── README.md
```

## Documentación

La documentación completa está disponible en: **https://maya-aqss.github.io/maya-signer/**

Incluye:
- Guía de usuario
- Guía de desarrollo
- Arquitectura del sistema
- Referencia de API
- Troubleshooting

## Contribuir

Las contribuciones son bienvenidas

1. Fork del proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -m 'feat: nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## Reportar Bugs

Usa [GitHub Issues](https://github.com/Maya-AQSS/maya-signer/issues) para reportar bugs.

Por favor incluye:
- Sistema operativo y versión
- Versión de Maya Signer
- Pasos para reproducir el problema
- Logs (ver documentación para ubicación)

## Licencia

Este proyecto está licenciado bajo la Licencia GNU GENERAL PUBLIC LICENSE v3.0 - ver [LICENSE](LICENSE) para detalles.

## Contribuidores

Ver la lista de [contribuidores](https://github.com/Maya-AQSS/maya-signer/contributors).

## Agradecimientos

- [pyHanko](https://github.com/MatthiasValvekens/pyHanko) - Librería de firma PDF
- [PySide6](https://www.qt.io/qt-for-python) - Framework GUI

## Soporte

- Documentación: [GitHub Pages](https://maya-aqss.github.io/maya-signer/)