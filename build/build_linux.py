#!/usr/bin/env python3
"""
Script de compilación para Linux
Genera un AppImage o paquete .deb

Desarrollado por Claude Sonnet 4.5
"""
import subprocess
import sys
from pathlib import Path


def build_executable():
    """Compila la aplicación con PyInstaller"""
    print("=" * 60)
    print("  COMPILANDO EJECUTABLE PARA LINUX")
    print("=" * 60)
    
    # ojo! nombre del fichero con - no con _
    # el nombre de la carpeta de compilación es el nombre del fichero spec
    # el código con _ pero el ejecutable con - por estandarizar
    try:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "maya-signer.spec",
            "--clean",
            "--noconfirm"
        ], check=True)
        
        print("\n✓ Ejecutable compilado correctamente")
        print("  Ubicación: dist/maya-signer")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error al compilar: {e}")
        return False


def create_deb_package():
    """Crea un paquete .deb para Debian/Ubuntu"""
    print("\n" + "=" * 60)
    print("  CREANDO PAQUETE .DEB")
    print("=" * 60)
    
    # Estructura del paquete
    pkg_dir = Path("maya-signer_1.0")
    debian_dir = pkg_dir / "DEBIAN"
    usr_bin = pkg_dir / "usr" / "bin"
    usr_share = pkg_dir / "usr" / "share" / "applications"
    
    try:
        # Crear directorios
        debian_dir.mkdir(parents=True, exist_ok=True)
        usr_bin.mkdir(parents=True, exist_ok=True)
        usr_share.mkdir(parents=True, exist_ok=True)
        
        # Archivo control
        control_content = """Package: maya-signer
Version: 1.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3
Maintainer: Tu Nombre <tu@email.com>
Description: Servicio de firma digital para Odoo
 Cliente de firma digital que se integra con Odoo
 a través del protocolo maya://
"""
        (debian_dir / "control").write_text(control_content)
        
        # Script postinst (se ejecuta después de instalar)
        postinst_content = """#!/bin/bash
set -e
/usr/bin/maya-signer --install-protocol
exit 0
"""
        postinst_file = debian_dir / "postinst"
        postinst_file.write_text(postinst_content)
        postinst_file.chmod(0o755)
        
        # Script prerm (se ejecuta antes de desinstalar)
        prerm_content = """#!/bin/bash
set -e
/usr/bin/maya-signer --uninstall-protocol
exit 0
"""
        prerm_file = debian_dir / "prerm"
        prerm_file.write_text(prerm_content)
        prerm_file.chmod(0o755)
        
        # Copiar ejecutable
        import shutil
        shutil.copy2("dist/maya-signer", usr_bin / "maya-signer")
        (usr_bin / "maya-signer").chmod(0o755)
        
        # Crear archivo .desktop
        desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Maya Signer
Comment=Servicio de firma digital para Odoo
Exec=/usr/bin/maya-signer %u
Icon=document-sign
Terminal=false
Categories=Office;
MimeType=x-scheme-handler/maya;
"""
        (usr_share / "maya-signer.desktop").write_text(desktop_content)
        
        # Construir paquete
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir)], check=True)
        
        print("\n✓ Paquete .deb creado correctamente")
        print("  Ubicación: maya-signer_1.0.deb")
        return True
        
    except Exception as e:
        print(f"\n✗ Error al crear paquete: {e}")
        return False


def main():
    if not build_executable():
        return 1
    
    create_deb_package()
    
    print("\n" + "=" * 60)
    print("✓ PROCESO COMPLETADO")
    print("=" * 60)
    print("\nPara instalar:")
    print("  Ubuntu/Debian: sudo dpkg -i maya-signer_1.0.deb")
    print("  Otras distros: ./dist/maya-signer --install-protocol")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())