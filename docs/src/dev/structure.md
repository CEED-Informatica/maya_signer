# Estructura del proyecto

Mapa completo del proyecto y la función de cada archivo.

## Árbol de Directorios

```
maya-signer/
│
├── src/                                   # Código fuente principal
│   ├── main.py                            # Cliente del protocolo maya://
│   ├── maya_signer_service.py             # Servicio HTTP en background
│   ├── credentials_dialog.py              # Diálogo Qt de credenciales
│   ├── odoo_client.py                     # Cliente XML-RPC para Odoo
│   ├── subprocess_signature_manager.py    # Gestor de subprocesos de firma
│   ├── signer_worker.py                   # Worker aislado de firma
│   ├── hanko_signer.py                    # Wrapper de pyHanko
│   ├── custom_logging.py                  # Sistema de logs
│   └── assets/
│       ├── icon.png                       # Icono base (Linux)
│       ├── icon.ico                       # Icono Windows
│       └── icon.icns                      # Icono macOS
│
├── build/                                 # Scripts de compilación
│   ├── maya-signer.spec                   # PyInstaller (unificado, 3 plataformas)
│   ├── build_deb.py                       # Crear paquete .deb (Linux)
│   ├── build_msi.py                       # Crear instalador .msi (Windows)
│   └── build_dmg.py                       # Crear imagen .dmg (macOS)
│
├── tests/                                    # Tests
│   ├── conftest.py                           # Fixtures compartidos
│   ├── test_odoo_client.py                   # Unit: OdooClient
│   ├── test_subprocess_signature_manager.py  # Unit: SubprocessSignatureManager
│   ├── test_main_protocol.py                 # Unit: protocolo maya://
│   ├── test_integration_client_service.py    # Integración: Cliente ↔ Servicio
│   └── test_integration_worker.py            # Integración: Servicio → Worker
│
├── docs/                                  # Documentación (VitePress)
│   ├── .vitepress/
│   │   └── config.mts                     # Configuración del sitio
│   └── src/                               # Código de la documentación
│       ├── index.md                       # Página principal
│       ├── public/                        # Assets estáticos
│       ├── user/                          # Guía de usuario
│       └── dev/                           # Guía de desarrollo
│
├── .github/
│   └── workflows/
│       ├── test-and-build.yml             # CI/CD: tests → builds → release
│       └── deploy-docs.yml                # Despliegue de documentación
│
├── version.py                             # Versión centralizada
├── requirements.txt                       # Dependencias Python
├── Makefile                               # Comandos de build
└── README.md                              # Documentación principal
```

## Descripción de cada archivo en _src/_

### main.py

**Punto de entrada del protocolo `maya://`.**

Cuando un navegador abre un enlace `maya://sign?...`, el sistema operativo ejecuta este archivo. Sus responsabilidades:

- Parsear la URL del protocolo
- Verificar si el servicio está corriendo (puerto 50304)
- Si no está, iniciarlo
- Enviar la petición de firma al servicio

```
Navegador → maya://sign?... → main.py → POST localhost:50304
```

### maya_signer_service.py

**Servicio HTTP que corre en background.**

Es el corazón de la aplicación. Siempre activo, esperando peticiones:

- Servidor HTTP en `127.0.0.1:50304`
- Gestiona las credenciales en memoria
- Muestra el diálogo de credenciales (Qt)
- Coordina el proceso de firma
- Muestra notificaciones en bandeja del sistema

### credentials_dialog.py

**Diálogo gráfico para introducir credenciales.**

Se muestra cuando el servicio necesita credenciales que no tiene:

- Campos: usuario, contraseña Maya, certificado, PIN
- Opción DNIe vs certificado .p12
- Timer de expiración (2 minutos)
- Prueba de conexión con Odoo

### odoo_client.py

**Cliente XML-RPC para comunicarse con Maya (Odoo).**

Todo lo que tiene que ver con el servidor:

- Autenticación
- Validación de tokens de sesión
- Descarga de PDFs sin firmar
- Subida de PDFs firmados
- Actualización de estados de lotes

### subprocess_signature_manager.py

**Gestiona la ejecución del worker de firma.**

Actúa como intermediario entre el servicio y el worker:

- Prepara el directorio temporal con los PDFs
- Crea el `input.json` con la configuración
- Lanza el worker como subproceso
- Monitorea el progreso leyendo `status.json`
- Lee los resultados de `output.json`
- Limpia archivos temporales

### signer_worker.py

**Proceso aislado que ejecuta la firma real.**

Se ejecuta como subproceso separado, sin acceso a Qt ni al servicio:

- Lee `input.json`
- Carga el certificado o configura DNIe
- Firma cada PDF con pyHanko
- Escribe los PDFs firmados en disco
- Actualiza `status.json` con el progreso
- Escribe `output.json` con los resultados

### hanko_signer.py

**Wrapper de la librería pyHanko.**

Encapsula toda la lógica de firma:

- Carga certificados .p12/.pfx
- Configura sesiones PKCS#11 para DNIe
- Firma PDFs con metadatos (razón, ubicación)
- Gestiona el cierre de sesiones

### custom_logging.py

**Sistema de logs centralizado.**

Configura el logging para toda la aplicación:

- Detecta el sistema operativo
- Elige la ubicación de logs según la plataforma
- Configura formato y niveles
- Soporta archivo y consola simultáneamente