# Instalación

## Descargar

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
