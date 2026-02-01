# Solución de problemas

## Error de token expirado

**Solución**: El token de sesión tiene validez de 10 minutos. Vuelve a hacer clic en "Firmar" desde Maya.

## No se abre el diálogo

**Solución**: Verifica que el servicio está corriendo (icono en bandeja).

## DNIe no detectado

**Linux:**
```bash
# Verificar lector
pcsc_scan

# Ver certificados
pkcs11-tool --module /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so --list-objects

# Reiniciar servicio pcscd
sudo systemctl restart pcscd
```

## Error de certificado

**Solución**: Verifica que:
- El archivo .p12/.pfx es válido
- La contraseña es correcta
- El certificado no ha expirado

## Errores específicos por SO

Otros errores más específicos puden consultarse en:

* [Linux](/user/platforms/linux#solucion-de-problemas)
* [Windows](/user/platforms/windows#solucion-de-problemas)
* [macOS](/user/platforms/macos#solucion-de-problemas)
