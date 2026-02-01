# macOS

Guía completa de **Maya | Signer** en macOS.

## Versiones Soportadas

| Versión | Estado |
|---------|--------|
| macOS Sonoma (14) | Probado |
| macOS Ventura (13) | Probado |
| macOS Monterey (12) | Probado |
| macOS Big Sur (11) | No probado |
| macOS Catalina (10.15) | No probado |
| macOS < 10.15 | No soportado |

## Instalación

### Método estándar

1. Descarga `maya-signer_X.X.X_macOS.dmg`
2. Doble clic en el archivo `.dmg`
3. Se abre una ventana con la aplicación y un acceso directo a Applications
4. **Arrastra** `MayaSigner.app` hacia la carpeta `Applications`
5. Expulsa el DMG (arrastra a la papelera o clic derecho → Expulsar)
6. Abre _MayaSigner_ desde Applications

### Primera ejecución: Gatekeeper

macOS mostrará un aviso de seguridad la primera vez:

> *"MayaSigner no puede abrirse porque proviene de un desarrollador no identificado"*

**Solución:**

```
Haz clic derecho sobre MayaSigner.app → Abrir → Confirmar "Abrir"
```

Si eso no funciona:

```bash
# Remover atributo de quarantine
xattr -cr /Applications/MayaSigner.app

# Luego abre normalmente
open /Applications/MayaSigner.app
```

::: warning Seguridad
Remover el atributo de quarantine es seguro en este caso porque el DMG lo has descargado directamente desde el repositorio oficial de GitHub.
:::

## Ubicación de Archivos

| Elemento | Ruta |
|----------|------|
| Aplicación | `/Applications/MayaSigner.app` |
| Ejecutables | `/Applications/MayaSigner.app/Contents/MacOS/` |
| Info.plist | `/Applications/MayaSigner.app/Contents/Info.plist` |
| Configuración usuario | `~/.maya_signer/` |
| Logs | `~/Library/Logs/MayaSigner/` |

## Protocolo `maya://`

En macOS el protocolo se registra **automáticamente la primera vez que se abre la aplicación**, sin necesidad de permisos de administrador.

### Cómo funciona

1. Al abrir MayaSigner por primera vez, el `launcher.sh` interno detecta que el protocolo no está registrado
2. Usa `lsregister` para registrar la app como handler de `maya://`
3. Crea el archivo `~/.maya_signer/protocol_registered` para no repetir el proceso

### Verificar registro

```bash
# Buscar maya en los handlers registrados
defaults read com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers | grep -A 3 maya
```

### Re-registrar si falla

```bash
# Forzar re-registro
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/MayaSigner.app

# Eliminar el marcador para que se registre de nuevo al arrancar
rm ~/.maya_signer/protocol_registered

# Reiniciar Finder y Dock
killall Finder
killall Dock
```

### Probar manualmente

```bash
open "maya://sign?batch=1&url=https://maya.example.com&token=test"
```

## Arrancar el Servicio

El servicio se arranca automáticamente cuando se necesita. Si no está activo:

```bash
# Arrancar manualmente
open /Applications/MayaSigner.app

# Verificar que está corriendo
curl http://127.0.0.1:50304/health
```

El icono aparecerá en la **barra de menú** (parte superior derecha de la pantalla).

## Permisos de macOS

macOS puede solicitar permisos adicionales la primera vez:

- **Acceso a red**: Necesario para conectar al servidor Maya
- **Acceso al portapapeles**: Puede ser necesario en algunos flujos
- **Archivos**: Para acceder al certificado .p12

Para gestionar estos permisos:

```
Preferencias del Sistema → Seguridad y Privacidad → Privacidad
```

## Desinstalación

```bash
# Eliminar aplicación
rm -rf /Applications/MayaSigner.app

# Limpiar configuración (opcional)
rm -rf ~/.maya_signer

# Limpiar logs (opcional)
rm -rf ~/Library/Logs/MayaSigner
```

## Solución de Problemas

### "La aplicación está dañada"

```bash
xattr -cr /Applications/MayaSigner.app
```

Si sigue fallando, en **Preferencias del Sistema → Seguridad y Privacidad → General**, marca *"Permitir aplicaciones descargadas de: Cualquier lugar"*.

### El protocolo no se abre correctamente

```bash
# Forzar re-registro
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/MayaSigner.app

# Reiniciar Launch Services
killall Finder
```

### El servicio se cierra solo

Revisa los logs:

```bash
cat ~/Library/Logs/MayaSigner/service.log
```