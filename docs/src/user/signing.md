# Firmar documentos

Guía paso a paso para usar **Maya | Signer**

## Frimando desde _Odoo_

**Desde Maya (Odoo)**

1. **Haz clic** en el botón _Firmar_ el documento o el lote de documentos

![Botón Firmar en Maya](/screenshots/maya-sign-button.png)

## Comprobación del arranque del servicio (opcional)

Este paso es opcional. Si el servicio no está arrancado, la petición a través de `maya://` lo arrancará automáticamente. Si quieres, es posible verificarlo de varias maneras:

::: code-group

```bash [Linux]
# Debería ver el icono en la bandeja del sistema
# O verificar manualmente:
ps aux | grep maya-signer-service
```

```powershell [Windows]
# Verificar en la bandeja del sistema (system tray)
# O buscar el proceso:
tasklist | findstr maya-signer-service
```

```bash [macOS]
# Abrir la aplicación desde Applications
open /Applications/MayaSigner.app

# Se mostrará un icono en la barra de menú
```

:::

## Icono en Bandeja del Sistema

Cuando el servicio está activo, verás un icono en:

- **Linux**: Barra superior (GNOME) o bandeja del sistema
- **Windows**: System tray (esquina inferior derecha)
- **macOS**: Barra de menú superior

![Icono Maya Signer](/screenshots/icon-tray.png)

### Menú del Icono

Haz clic derecho en el icono para ver:

![Menu bandeja](/screenshots/menu-tray.png)

- **Maya Signer X.X.X** (versión)
- **Servicio Listo** (estado actual)
- **Conexiones activas: X** (servidores conectados)
- **Borrar credenciales** (limpiar memoria)
- **Salir** (cerrar servicio)

## Diálogo de Credenciales

### Configurar Credenciales

En el caso de que las credenciales no estén almacenadas, se abrirá el diálogo de credenciales/configuración automáticamente:

![Diálogo de Credenciales](/screenshots/credentials-dialog.png)

::: warning Seguridad
Por motivos de seguridad, es necesario introducir las credenciales en un tiempo máximo de 2 minutos.
:::

#### Credenciales de Maya

- **Usuario de Maya**: Tu email de acceso a Maya
- **Contraseña de Maya**: Tu contraseña de Maya

::: warning Seguridad
Estas credenciales se guardan **solo en memoria** durante la sesión. No se escriben en disco.
:::

### Credenciales Firma Electrónica

Elige **una** de estas opciones:

**Opción A: Certificado .p12/.pfx**

1. **Deselecciona** "Usar DNIe"
2. **Examinar**: Selecciona tu archivo `.p12` o `.pfx`
3. **Contraseña del certificado**: La contraseña de tu certificado

**Opción B: DNIe**

1. **Marca** "Usar DNIe"
2. **Conecta** tu lector de tarjetas con el DNIe
3. **Contraseña del DNIe**: Tu PIN del DNIe

::: danger Importante con DNIe
Si usas DNIe, se te pedirá confirmar **cada documento** individualmente. Para lotes grandes, es más rápido usar certificado .p12.
:::

### Guardar Preferencias

Las preferencias se guardan automáticamente:
- Ruta del certificado
- Si usas DNIe o certificado
- Usuario de Maya

**NO se guarda:**
- Contraseña de Maya
- Contraseña del certificado/DNIe

## Proceso de Firma

Una vez introducidas las credenciales, **Maya | Signer**:

1. **Descarga** de documentos desde Maya
2. **Firma** de cada documento
3. **Subida** de documentos firmados
4. **Notificación** de éxito

Verás el progreso en:

- **Notificación del sistema**
- **Estado en el icono de bandeja**
- **Mensaje en Maya**

## Firmas Siguientes

En firmas posteriores:

- **NO se pedirán** credenciales de Maya (en esta sesión)
- **NO se pedirá** ruta del certificado
- **SÍ se pedirá** la contraseña del certificado/DNIe cada vez

::: tip Gestión de Sesión
Para limpiar las credenciales almacenadas en memoria:
Clic derecho en el icono → "_Borrar credenciales_"
:::

## Múltiples Servidores

Si trabajas con varios servidores Maya:

- Cada servidor tendrá **sus propias credenciales**
- Se guardan **separadas** en memoria
- Puedes ver cuántos están activos en el menú

## Verificar Firma

Después de firmar, puedes verificar:

### En Maya

- El documento mostrará "Firmado electrónicamente"
- Fecha y usuario de firma
- Botón para descargar PDF firmado (esta opción puede no ser de acceso directo y que dependa de los permisos del usuario)

### En el PDF

Abre el PDF firmado con un lector compatible:

- **Firma**: Verás el panel de firmas
- **Validación**: Estado "Firmado y todas las firmas son válidas"
- **Detalles**: Información del certificado



