#!/usr/bin/env python3
"""
Desinstalador del protocolo maya://

Desarrollado por Claude Sonnet 4.5
"""
import sys
import platform
import subprocess
from pathlib import Path


def uninstall_windows():
    """Elimina el protocolo del registro de Windows"""
    import winreg
    
    protocol = "maya"
    
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open\\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\DefaultIcon")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}")
        
        print(f"✓ Protocolo {protocol}:// eliminado correctamente")
        return True
        
    except FileNotFoundError:
        print(f"⚠ El protocolo {protocol}:// no estaba registrado")
        return True
    except Exception as e:
        print(f"✗ Error al eliminar el protocolo: {e}")
        return False


def uninstall_macos():
    """Elimina la aplicación .app en macOS"""
    home = Path.home()
    app_dir = home / "Applications" / "MayaSigner.app"
    
    try:
        if app_dir.exists():
            import shutil
            shutil.rmtree(app_dir)
            print(f"✓ Aplicación eliminada: {app_dir}")
        else:
            print(f"⚠ La aplicación no estaba instalada")
        
        return True
        
    except Exception as e:
        print(f"✗ Error al eliminar la aplicación: {e}")
        return False


def uninstall_linux():
    """Elimina el archivo .desktop en Linux"""
    home = Path.home()
    desktop_file = home / ".local" / "share" / "applications" / "maya-signer.desktop"
    
    try:
        if desktop_file.exists():
            desktop_file.unlink()
            print(f"✓ Archivo desktop eliminado: {desktop_file}")
            
            # Actualizar base de datos
            desktop_dir = desktop_file.parent
            subprocess.run(["update-desktop-database", str(desktop_dir)], check=False)
        else:
            print(f"⚠ El archivo desktop no estaba instalado")
        
        return True
        
    except Exception as e:
        print(f"✗ Error al eliminar el archivo desktop: {e}")
        return False


def main():
    system = platform.system()
    
    print("=" * 60)
    print("  DESINSTALADOR DE PROTOCOLO MAYA://")
    print("=" * 60)
    
    if system == "Windows":
        success = uninstall_windows()
    elif system == "Darwin":
        success = uninstall_macos()
    elif system == "Linux":
        success = uninstall_linux()
    else:
        print(f"✗ Sistema operativo no soportado: {system}")
        success = False
    
    print("=" * 60)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())