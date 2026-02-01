# Linux

Guía completa de **Maya | Signer** en Linux.

## Distribuciones Soportadas

| Distribución | Versión Mínima | Estado |
|--------------|----------------|--------|
| Ubuntu | 20.04 LTS | Probado |
| Debian | 10 (Buster) | Probado |
| Linux Mint | 20 | Probado |
| Fedora | 33+ | Sin paquete oficial |
| Arch Linux | Reciente | Sin paquete oficial |

::: warning Distribuciones no soportadas
En distribuciones que no usan `.deb` (Fedora, Arch, etc.) puedes intentar instalar desde fuente, pero no está garantizado que funcione.
:::

## Instalación

### Método estándar

```bash
# 1. Descargar
wget https://github.com/tu-usuario/maya-signer/releases/download/vX.X.X/maya-signer_X.X.X_amd64.deb

# 2. Instalar
sudo dpkg -i maya-signer_X.X.X_amd64.deb

# 3. Resolver dependencias si aparecen
sudo apt-get install -f
```

### Dependencias del sistema

Se instalan automáticamente con el paquete:

- `libxcb-cursor0`
- `libxcb-icccm4`
- `libxcb-image0`
- `libxcb-keysyms1`
- `libxcb-randr0`
- `libxcb-render-util0`
- `libxcb-shape0`
- `libxcb-xinerama0`
- `libxcb-xfixes0`

### Para DNIe

Si vas a usar DNIe necesitas instalar paquetes adicionales:

```bash
# Instalar OpenSC y pcscd
sudo apt-get install opensc pcscd pcsc-tools

# Habilitar e iniciar el servicio
sudo systemctl enable pcscd
sudo systemctl start pcscd

# Verificar que el lector está conectado
pcsc_scan
```

::: tip Verificación del lector
`pcsc_scan` debe mostrar tu lector y el DNIe cuando lo introduces. Si no aparece, revisa el cable o prueba con otro puerto USB.
:::

## Ubicación de Archivos

| Elemento | Ruta |
|----------|------|
| Ejecutable principal | `/opt/maya-signer/maya-signer` |
| Servicio | `/opt/maya-signer/maya-signer-service` |
| Enlace en PATH | `/usr/bin/maya-signer` |
| Archivo .desktop | `/usr/share/applications/maya-signer.desktop` |
| Configuración usuario | `~/.maya_signer/` |
| Logs | `~/.local/state/maya_signer/` |

## Protocolo `maya://`

El protocolo se registra automáticamente durante la instalación mediante el script `postinst` del paquete.

### Verificar registro

```bash
xdg-mime query default x-scheme-handler/maya
# Debe mostrar: maya-signer.desktop
```

### Re-registrar si falla

```bash
xdg-mime default maya-signer.desktop x-scheme-handler/maya
update-desktop-database ~/.local/share/applications
```

### Probar manualmente

```bash
xdg-open "maya://sign?batch=1&url=https://maya.example.com&token=test"
```

## Arrancar el Servicio

El servicio se arranca automáticamente cuando se necesita. Si por algún motivo no está activo:

```bash
# Arrancar manualmente
maya-signer --start-service

# Verificar que está corriendo
curl http://127.0.0.1:50304/health
# Debe retornar: {"status": "running"}
```

## Entornos Especiales

### Entornos corporativos

Si tu empresa tiene restricciones de seguridad:

- Asegúrate de que el puerto `50304` (localhost) no está bloqueado
- El protocolo `maya://` debe estar permitido en el navegador
- Los certificados corporativos deben ser accesibles desde tu usuario

## Desinstalación

```bash
# Desinstalar paquete
sudo apt remove maya-signer

# Limpiar configuración (opcional, preserve si quieres mantener tus preferencias)
rm -rf ~/.maya_signer

# Limpiar logs (opcional)
rm -rf ~/.local/state/maya_signer
```

## Solución de Problemas

### El icono no aparece en la bandeja

Algunos entornos de escritorio (como GNOME puro) no soportan iconos de bandeja nativamente. Necesitas una extensión:

```bash
# En GNOME
sudo apt-get install gnome-shell-extensions
# Activa la extensión "System Tray Icons" desde Extensions
```

### Error: "Segmentation fault" al arrancar

Probablemente un problema con las librerías Qt. Prueba:

```bash
export QT_QPA_PLATFORM=offscreen
maya-signer --start-service
```

Si funciona, el problema es con tu servidor de visualización.

### DNIe no se detecta

```bash
# 1. Verificar servicio pcscd
sudo systemctl status pcscd

# 2. Verificar lector
pcsc_scan

# 3. Listar certificados del DNIe
pkcs11-tool --module /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so --list-objects --type cert
```
