# Windows

Guía completa de **Maya | Signer** en Windows.

## Versiones Soportadas

| Versión | Estado |
|---------|--------|
| Windows 11 | Probado (Recomendado) |
| Windows 10 (1903+) | Probado |
| Windows 8.1 | No soportado |
| Windows 7 | No soportado |

## Instalación

### Método estándar

1. Descarga `maya-signer_X.X.X_x64.msi` desde [GitHub Releases](https://github.com/tu-usuario/maya-signer/releases)
2. Doble clic en el archivo `.msi`
3. Si aparece el control de cuentas de usuario (UAC), haz clic en **Sí**
4. Sigue el asistente: Siguiente → Aceptar licencia → Instalar → Finalizar

### Instalación silenciosa

Para despliege masivo en entornos corporativos:

```powershell
# Instalación completamente silenciosa
msiexec /i "maya-signer_X.X.X_x64.msi" /quiet /qn

# Instalación con barra de progreso (sin diálogos)
msiexec /i "maya-signer_X.X.X_x64.msi" /qb

# Instalación con log para debugging
msiexec /i "maya-signer_X.X.X_x64.msi" /quiet /L*v "C:\Logs\maya-signer-install.log"
```

## Ubicación de Archivos

| Elemento | Ruta |
|----------|------|
| Ejecutable principal | `C:\Program Files\Maya Signer\maya-signer.exe` |
| Servicio | `C:\Program Files\Maya Signer\maya-signer-service.exe` |
| Acceso directo | Menú Inicio → Maya Signer |
| Configuración usuario | `%APPDATA%\MayaSigner\` |
| Logs | `%APPDATA%\MayaSigner\` |

::: tip Expandir variables
En PowerShell: `echo $env:APPDATA`  
En CMD: `echo %APPDATA%`
:::

## Protocolo `maya://`

Se registra automáticamente durante la instalación en el registro de Windows.

### Verificar registro

```powershell
# Ver las claves del protocolo
reg query "HKCR\maya"

# Ver el comando asociado
reg query "HKCR\maya\shell\open\command"
```

### Re-registrar si falla

```powershell
# Registrar protocolo manualmente
reg add "HKCR\maya" /ve /d "URL:Maya Protocol" /f
reg add "HKCR\maya" /v "URL Protocol" /t REG_SZ /d "" /f
reg add "HKCR\maya\shell\open\command" /ve /d "\"C:\Program Files\Maya Signer\maya-signer.exe\" \"%1\"" /f
```

### Probar manualmente

```powershell
start "maya://sign?batch=1&url=https://maya.example.com&token=test"
```

## Arrancar el Servicio

El servicio se arranca automáticamente cuando se necesita. Si no está activo:

```powershell
# Arrancar manualmente
"C:\Program Files\Maya Signer\maya-signer.exe" --start-service

# Verificar que está corriendo
curl http://127.0.0.1:50304/health
```

El icono aparecerá en la **bandeja del sistema** (esquina inferior derecha de la barra de tareas).

## Entornos Corporativos

### Firewall

El servicio solo usa `localhost:50304`. No necesita acceso a internet directo, pero sí necesita conectar al servidor Odoo.

### Antivirus

Algunos antivirus pueden bloquear la ejecución. Si ves alertas:

1. Añade `C:\Program Files\Maya Signer\` a las excepciones del antivirus
2. Marca los ejecutables como permitidos

### Política de grupo (GPO)

Si tu empresa controla las aplicaciones via GPO, necesitas que un administrador añada **Maya | Signer** a la lista de aplicaciones permitidas.

## Desinstalación

### Desde Panel de Control

1. **Panel de Control** → **Programas** → **Desinstalar un programa**
2. Selecciona **Maya Signer**
3. Haz clic en **Desinstalar**

### Desde PowerShell

```powershell
# Desinstalar silenciosamente
msiexec /x "maya-signer_X.X.X_x64.msi" /quiet

# Limpiar configuración (opcional)
Remove-Item -Path "$env:APPDATA\MayaSigner" -Recurse -Force
```

## Solución de Problemas

### "El instalador no se ejecuta"

- Desactiva temporalmente el antivirus
- Verifica que tienes permisos de administrador
- Prueba ejecutar desde CMD como administrador:
  ```cmd
  msiexec /i "maya-signer_X.X.X_x64.msi" /L*v install.log
  ```
  Revisa `install.log` para ver el error exacto.

### El protocolo no funciona en el navegador

Algunos navegadores (Chrome, Firefox) cachean las asociaciones de protocolo. Prueba:

1. Cerrar y reabrir el navegador
2. En Chrome: `chrome://apps` → verificar que maya:// está registrado
3. Si no funciona, reinstalar el paquete

### "maya-signer-service.exe ha dejado de funcionar"

```powershell
# Ver el log para encontrar el error
notepad "$env:APPDATA\MayaSigner\service.log"
```