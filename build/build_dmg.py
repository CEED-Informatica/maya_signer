#!/usr/bin/env python3
"""
Crea un instalador DMG para Maya Signer en macOS
Requiere: pyinstaller, create-dmg (brew install create-dmg)
Generado por Claude Sonnet 4.5 (adaptado por aoltra)
"""

import os
import sys
import shutil
import subprocess
import plistlib
from pathlib import Path

# Añadir el directorio raíz al path para importar version
sys.path.insert(0, str(Path(__file__).parent.parent))
from manifest import __version__, __maintainer__, __description__, __package_name__

VERSION = __version__
PACKAGE_NAME = __package_name__
AUTHOR = __maintainer__
DESCRIPTION = __description__
APP_NAME = "MayaSigner"

def run_command(cmd, cwd=None):
    """Ejecuta un comando y retorna el resultado"""
    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def compile_executables():
    """Compila los ejecutables con PyInstaller"""
    print("\n" + "="*60)
    print("COMPILANDO EJECUTABLES PARA macOS")
    print("="*60)
    
    build_dir = Path(__file__).parent
    spec_file = build_dir / "maya-signer.spec"
    
    if not spec_file.exists():
        print(f"❌ Error: No se encontró {spec_file}")
        return False
    
    # Limpiar dist anterior
    root_dir = build_dir.parent
    dist_dir = root_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Ejecutar PyInstaller
    if not run_command(["pyinstaller", str(spec_file)], cwd=build_dir):
        print("❌ Error compilando con PyInstaller")
        return False
    
    # Los ejecutables estarán en build/dist/
    exe_dir = build_dir / "dist"
    
    # Verificar que se crearon
    if not (exe_dir / "maya-signer").exists() or not (exe_dir / "maya-signer-service").exists() \
        or not (exe_dir / "maya-signer-worker").exists():
        print("❌ No se encontraron los ejecutables compilados")
        print(f"   Buscando en: {exe_dir}")
        return False
    
    print("✓ Ejecutables compilados correctamente")
    return True

def create_app_bundle():
    """Crea el bundle .app de macOS"""
    print("\n" + "="*60)
    print("CREANDO APP BUNDLE")
    print("="*60)
    
    build_dir = Path(__file__).parent
    dist_dir = build_dir / "dist"
    app_bundle = dist_dir / f"{APP_NAME}.app"
    
    # Estructura del bundle
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Crear directorios
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Copiar ejecutables
    print("Copiando ejecutables...")
    shutil.copy(dist_dir / "maya-signer", macos_dir / "maya-signer")
    shutil.copy(dist_dir / "maya-signer-service", macos_dir / "maya-signer-service")
    shutil.copy(dist_dir / "maya-signer-worker", macos_dir / "maya-signer-worker")
    
    # Dar permisos de ejecución
    (macos_dir / "maya-signer").chmod(0o755)
    (macos_dir / "maya-signer-service").chmod(0o755)
    (macos_dir / "maya-signer-worker").chmod(0o755)

    # Copiar icono si existe
    icon_src = build_dir.parent / "src" / "icon.icns"
    if icon_src.exists():
        shutil.copy(icon_src, resources_dir / "icon.icns")
        icon_file = "icon.icns"
    else:
        print("⚠️  No se encontró icon.icns, usando icono por defecto")
        icon_file = None
    
    # Crear Info.plist
    print("Creando Info.plist...")
    create_info_plist(contents_dir, icon_file)
    
    # Crear script de arranque que registra el protocolo
    print("Creando launcher script...")
    create_launcher_script(macos_dir)
    
    print(f"✓ App bundle creado: {app_bundle}")
    return app_bundle

def create_info_plist(contents_dir, icon_file):
    """Crea el archivo Info.plist"""
    
    plist_dict = {
        'CFBundleDevelopmentRegion': 'en',
        'CFBundleExecutable': 'launcher.sh',
        'CFBundleIdentifier': f'com.{AUTHOR.lower().replace(" ", "")}.mayasigner',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': 'Maya Signer',
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'Maya Protocol',
                'CFBundleURLSchemes': ['maya']
            }
        ]
    }
    
    if icon_file:
        plist_dict['CFBundleIconFile'] = icon_file
    
    plist_file = contents_dir / 'Info.plist'
    with open(plist_file, 'wb') as f:
        plistlib.dump(plist_dict, f)
    
    print(f"✓ Info.plist creado")

def create_launcher_script(macos_dir):
    """Crea un script launcher que registra el protocolo al arrancar"""
    
    launcher_script = macos_dir / "launcher.sh"
    
    script_content = f'''#!/bin/bash

# Obtener el directorio del bundle
BUNDLE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MACOS_DIR="$BUNDLE_DIR/MacOS"

# Registrar el protocolo maya:// si no está registrado
register_protocol() {{
    # Verificar si ya está registrado
    CURRENT_HANDLER=$(defaults read com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers 2>/dev/null | grep -A 2 "maya" | grep "LSHandlerRoleAll" | cut -d'"' -f4)
    
    if [ "$CURRENT_HANDLER" != "com.{AUTHOR.lower().replace(" ", "")}.mayasigner" ]; then
        echo "Registrando protocolo maya://"
        
        # Usar lsregister para registrar la aplicación
        /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$BUNDLE_DIR/.."
        
        # Establecer como handler por defecto
        defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add '{{
            LSHandlerContentType = "public.url";
            LSHandlerPreferredVersions = {{ LSHandlerRoleAll = "-"; }};
            LSHandlerRoleAll = "com.{AUTHOR.lower().replace(" ", "")}.mayasigner";
            LSHandlerURLScheme = "maya";
        }}'
    fi
}}

# Registrar protocolo en primer arranque
if [ ! -f "$HOME/.maya_signer/protocol_registered" ]; then
    mkdir -p "$HOME/.maya_signer"
    register_protocol
    touch "$HOME/.maya_signer/protocol_registered"
fi

# Ejecutar la aplicación real
exec "$MACOS_DIR/maya-signer" "$@"
'''
    
    launcher_script.write_text(script_content)
    launcher_script.chmod(0o755)
    
    print(f"✓ Launcher script creado")

def create_dmg(app_bundle):
    """Crea el DMG usando create-dmg"""
    print("\n" + "="*60)
    print("CREANDO DMG")
    print("="*60)
    
    build_dir = Path(__file__).parent
    dist_dir = build_dir / "dist"
    dmg_file = build_dir.parent / f"maya-signer_{VERSION}_macOS.dmg"
    
    # Verificar que create-dmg está instalado
    if not shutil.which("create-dmg"):
        print("❌ create-dmg no encontrado.")
        print("\nPara instalar:")
        print("  brew install create-dmg")
        return False
    
    # Limpiar DMG anterior si existe
    if dmg_file.exists():
        dmg_file.unlink()
    
    # Crear DMG temporal
    temp_dmg = dist_dir / "temp.dmg"
    if temp_dmg.exists():
        temp_dmg.unlink()
    
    # Comandos de create-dmg
    cmd = [
        "create-dmg",
        "--volname", f"Maya Signer {VERSION}",
        "--volicon", str(build_dir.parent / "src" / "icon.icns") if (build_dir.parent / "src" / "icon.icns").exists() else "",
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "175", "190",
        "--hide-extension", f"{APP_NAME}.app",
        "--app-drop-link", "425", "190",
        "--no-internet-enable",
        str(dmg_file),
        str(dist_dir)
    ]
    
    # Filtrar opciones vacías
    cmd = [c for c in cmd if c]
    
    if not run_command(cmd, cwd=build_dir):
        print("❌ Error creando DMG")
        return False
    
    print(f"\n✓ DMG creado: {dmg_file}")
    
    # Información del DMG
    run_command(["hdiutil", "info", str(dmg_file)])
    
    return True

def create_simple_readme():
    """Crea un README para el DMG"""
    build_dir = Path(__file__).parent
    dist_dir = build_dir / "dist"
    readme_file = dist_dir / "README.txt"
    
    readme_content = f"""Maya Signer v{VERSION}
{"="*60}

INSTALACIÓN:
1. Arrastra "MayaSigner.app" a tu carpeta Applications
2. Abre MayaSigner desde Applications
3. Permite los permisos cuando macOS lo solicite
4. El protocolo maya:// se registrará automáticamente

DESINSTALACIÓN:
1. Arrastra MayaSigner.app a la Papelera
2. Elimina la carpeta ~/.maya_signer (opcional)

NOTA IMPORTANTE:
En el primer arranque, macOS puede mostrar:
"MayaSigner.app no puede abrirse porque proviene de un desarrollador no identificado"

Para solucionarlo:
1. Haz clic derecho en MayaSigner.app
2. Selecciona "Abrir"
3. Confirma "Abrir" en el diálogo

O en Preferencias del Sistema:
Seguridad y Privacidad → General → "Abrir de todas formas"

SOPORTE:
- GitHub: https://github.com/Maya-AQSS/maya-signer
- Email: {AUTHOR}

{DESCRIPTION}
"""
    
    readme_file.write_text(readme_content)
    print(f"✓ README creado: {readme_file}")

def main():
    print("="*60)
    print(f"MAYA SIGNER v{VERSION} - CREADOR DE DMG PARA macOS")
    print("="*60)
    
    # Verificar que estamos en macOS
    if sys.platform != 'darwin':
        print("❌ Este script solo funciona en macOS")
        return 1
    
    # Cambiar al directorio build
    build_dir = Path(__file__).parent
    os.chdir(build_dir.parent)
    
    # 1. Compilar ejecutables
    if not compile_executables():
        return 1
    
    # 2. Crear app bundle
    app_bundle = create_app_bundle()
    if not app_bundle:
        return 1
    
    # 3. Crear README
    create_simple_readme()
    
    # 4. Crear DMG
    if not create_dmg(app_bundle):
        return 1
    
    print("\n" + "="*60)
    print("¡DMG CREADO EXITOSAMENTE!")
    print("="*60)
    print(f"\nPara instalar:")
    print(f"  1. Abre: maya-signer_{VERSION}_macOS.dmg")
    print(f"  2. Arrastra MayaSigner.app a Applications")
    print(f"\nPara desinstalar:")
    print(f"  Arrastra MayaSigner.app a la Papelera")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
