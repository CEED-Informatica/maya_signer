#!/usr/bin/env python3
"""
Instalador del protocolo maya:// para Windows, macOS y Linux
Desarrollado por Claude Sonnet 4.5
Modificado por Alfredo Oltra
"""
import sys
import os
import platform
import subprocess
from pathlib import Path


def get_executable_path() -> list[str, str]:
    """
    Obtiene la ruta del ejecutable según si está compilado o no
    Devuelve dos cadenas:
      - La ruta del ejecutable
      - La ruta del directorio del script (solo en modo desarrollo)
    """
    if getattr(sys, 'frozen', False):
        # Ejecutable compilado con PyInstaller
        return sys.executable, None
    else:
        # Modo desarrollo: apunta a main.py
        script_dir = Path(__file__).parent.parent
        return str(script_dir / "src" / "main.py"), script_dir

def install_windows():
    """Registra el protocolo en Windows usando el registro"""
    import winreg
    
    exe_path = get_executable_path()
    protocol = "maya"
    
    try:
        # Crear clave principal del protocolo
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Crear clave del icono
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\DefaultIcon")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{exe_path},0")
        winreg.CloseKey(key)
        
        # Crear clave del comando
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open\\command")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        winreg.CloseKey(key)
        
        print(f"✓ Protocolo {protocol}:// registrado correctamente en Windows")
        print(f"  Ejecutable: {exe_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error al registrar el protocolo en Windows: {e}")
        return False


def install_macos():
    """Registra el protocolo en macOS creando una aplicación .app"""
    exe_path = get_executable_path()
    protocol = "maya"
    
    # Directorio de la aplicación
    app_name = "MayaSigner.app"
    home = Path.home()
    app_dir = home / "Applications" / app_name
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    try:
        # Crear estructura de directorios
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        # Copiar o crear enlace al ejecutable
        target_exe = macos_dir / "maya-signer"
        if Path(exe_path).is_file():
            import shutil
            shutil.copy2(exe_path, target_exe)
        else:
            # Crear script wrapper para modo desarrollo
            wrapper_script = f"""#!/bin/bash
python3 "{exe_path}" "$@"
"""
            target_exe.write_text(wrapper_script)
        
        target_exe.chmod(0o755)
        
        # Crear Info.plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>maya-signer</string>
    <key>CFBundleIdentifier</key>
    <string>com.maya.signer</string>
    <key>CFBundleName</key>
    <string>Maya Signer</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>Maya Protocol</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>{protocol}</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
"""
        plist_path = contents_dir / "Info.plist"
        plist_path.write_text(plist_content)
        
        # Registrar la aplicación
        subprocess.run([
            "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister",
            "-f", str(app_dir)
        ], check=True)
        
        print(f"✓ Protocolo {protocol}:// registrado correctamente en macOS")
        print(f"  Aplicación: {app_dir}")
        return True
        
    except Exception as e:
        print(f"✗ Error al registrar el protocolo en macOS: {e}")
        return False


def install_linux():
    """Registra el protocolo en Linux usando .desktop file"""
    exe_path, script_dir = get_executable_path()
    protocol = "maya"
    
    # Ubicación del archivo .desktop
    home = Path.home()
    desktop_dir = home / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "maya-signer.desktop"

    if script_dir: 
      python_command = script_dir / "venv" / "bin" / "python"
    else:
      python_command = "python3"
    
    try:
        # Contenido del archivo .desktop
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Maya Signer
Comment=Servicio de firma digital para Odoo
Exec="{python_command}" "{exe_path}" %u > /tmp/maya-signer.log 2>&1
Icon=document-sign
Terminal=false
Categories=Office;
MimeType=x-scheme-handler/{protocol};
"""
        desktop_file.write_text(desktop_content)
        desktop_file.chmod(0o755)
        
        # Actualizar base de datos de MIME types
        subprocess.run(["update-desktop-database", str(desktop_dir)], check=False)
        
        # Registrar el protocolo
        subprocess.run([
            "xdg-mime", "default", "maya-signer.desktop", f"x-scheme-handler/{protocol}"
        ], check=True)
        
        print(f"✓ Protocolo {protocol}:// registrado correctamente en Linux")
        print(f"  Desktop file: {desktop_file}")
        return True
        
    except Exception as e:
        print(f"✗ Error al registrar el protocolo en Linux: {e}")
        print("  Intenta ejecutar con permisos de usuario normal (no root)")
        return False


def main():
    """Instala el protocolo según el sistema operativo"""
    system = platform.system()
    
    print("=" * 60)
    print("  INSTALADOR DE PROTOCOLO MAYA://")
    print("=" * 60)
    print(f"\nSistema operativo detectado: {system}")
    
    if system == "Windows":
        success = install_windows()
    elif system == "Darwin":
        success = install_macos()
    elif system == "Linux":
        success = install_linux()
    else:
        print(f"✗ Sistema operativo no soportado: {system}")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Instalación completada correctamente")
        print("\nPrueba el protocolo abriendo en tu navegador:")
        print("  maya://test?batch_id=123&odoo_url=http://localhost:8069")
    else:
        print("✗ La instalación falló. Revisa los errores anteriores.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
