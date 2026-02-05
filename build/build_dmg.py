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

ORGANIZATION = "CEEDCV"

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
    print("CREANDO APP BUNDLE CON APPLESCRIPT")
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
    icon_src = build_dir.parent / "src" / "assets" / "icon.icns"
    if icon_src.exists():
        shutil.copy(icon_src, resources_dir / "icon.icns")
        icon_file = "icon.icns"
    else:
        print("⚠️  No se encontró icon.icns, usando icono por defecto")
        icon_file = None
    
    # Crear Info.plist
    print("Creando Info.plist...")
    create_info_plist(contents_dir, icon_file)
    
    # Crear AppleScript app que maneja URLs
    print("Creando AppleScript URL handler...")
    create_applescript_handler(resources_dir, macos_dir)
    
    print(f"✓ App bundle creado: {app_bundle}")
    return app_bundle

def create_info_plist(contents_dir, icon_file):
    """Crea el archivo Info.plist"""
    
    plist_dict = {
        'CFBundleDevelopmentRegion': 'es',
        'CFBundleExecutable': 'applet',  # ← CAMBIADO: AppleScript crea un ejecutable llamado "applet"
        'CFBundleIdentifier': f'com.{ORGANIZATION.lower().replace(" ", "")}.mayasigner',
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
        ],
        # IMPORTANTE: Esto indica que la app maneja Apple Events
        'NSAppleEventsUsageDescription': 'Maya Signer necesita manejar URLs del protocolo maya://',
    }
    
    if icon_file:
        plist_dict['CFBundleIconFile'] = icon_file
    
    plist_file = contents_dir / 'Info.plist'
    with open(plist_file, 'wb') as f:
        plistlib.dump(plist_dict, f)
    
    print(f"✓ Info.plist creado")

def create_applescript_handler(resources_dir, macos_dir):
    """
    Crea un AppleScript compilado que maneja las URLs del protocolo maya://
    
    En macOS, cuando se hace clic en maya://..., el sistema envía un Apple Event
    a la aplicación registrada. Este evento debe ser capturado con AppleScript.
    """
    
    # Script AppleScript que captura las URLs
#     applescript_source = f'''-- Maya Signer URL Handler
# -- Maneja las URLs del protocolo maya://

# on open location this_URL
#     -- Log para debugging (se puede ver en Console.app)
#     log "Maya Signer recibió URL: " & this_URL
    
#     -- Ruta al ejecutable real
#     set bundlePath to path to me as text
#     set executablePath to POSIX path of (bundlePath & "Contents:MacOS:maya-signer")
    
#     -- Ejecutar el comando con la URL como argumento
#     try
#         do shell script quoted form of executablePath & " " & quoted form of this_URL & " > /dev/null 2>&1 &"
#         log "Maya Signer ejecutado correctamente"
#     on error errMsg
#         log "Error ejecutando Maya Signer: " & errMsg
#         display dialog "Error al ejecutar Maya Signer: " & errMsg buttons {{"OK"}} default button "OK" with icon caution
#     end try
# end open location

# -- Handler para cuando se abre la app sin URL (doble clic)
# on run
#     log "Maya Signer abierto sin URL"
    
#     set bundlePath to path to me as text
#     set executablePath to POSIX path of (bundlePath & "Contents:MacOS:maya-signer")
    
#     -- Arrancar el servicio en modo background
#     try
#         do shell script quoted form of executablePath & " --start-service > /dev/null 2>&1 &"
        
#         -- Mostrar notificación opcional
#         display notification "Maya Signer está ejecutándose en segundo plano" with title "Maya Signer"
#     on error errMsg
#         log "Error iniciando servicio: " & errMsg
#         display dialog "Error al iniciar Maya Signer: " & errMsg buttons {{"OK"}} default button "OK" with icon caution
#     end try
    
#     -- Terminar la app AppleScript (el servicio sigue corriendo)
#     quit
# end run
# '''

    applescript_source = f'''-- Maya Signer URL Handler (Standalone para testing)
-- Este script maneja las URLs del protocolo maya://
-- 
-- Para probar:
-- 1. Compila con: osacompile -o MayaSigner.app MayaSignerHandler.applescript
-- 2. Prueba con: open "maya://sign?batch=123&url=https://test.com&token=abc"

-- Handler principal: se ejecuta cuando se hace clic en una URL maya://
on open location this_URL
    -- Log para debugging (visible en Console.app)
    log "================================"
    log "Maya Signer recibió URL: " & this_URL
    log "================================"
    
    -- Obtener la ruta al ejecutable maya-signer
    set bundlePath to path to me as text
    set executablePath to POSIX path of (bundlePath & "Contents:MacOS:maya-signer")
    
    log "Ejecutable: " & executablePath
    
    -- Verificar que el ejecutable existe
    try
        do shell script "test -f " & quoted form of executablePath
    on error
        log "ERROR: Ejecutable no encontrado en " & executablePath
        display dialog "Error: No se encontró el ejecutable maya-signer" buttons {"OK"} default button "OK" with icon stop
        return
    end try
    
    -- Ejecutar el comando con la URL como argumento
    -- El & al final hace que se ejecute en background
    try
        set cmd to quoted form of executablePath & " " & quoted form of this_URL & " > /tmp/maya-signer.log 2>&1 &"
        
        log "Ejecutando comando: " & cmd
        
        do shell script cmd
        
        log "✓ Maya Signer ejecutado correctamente"
        
        -- Opcional: mostrar notificación
        display notification "Procesando solicitud de firma..." with title "Maya Signer" subtitle this_URL
        
    on error errMsg number errNum
        log "ERROR ejecutando Maya Signer: " & errMsg & " (código: " & errNum & ")"
        
        display dialog "Error al ejecutar Maya Signer:" & return & return & errMsg buttons {"Ver Log", "OK"} default button "OK" with icon caution
        
        if button returned of result is "Ver Log" then
            do shell script "open -a Console /tmp/maya-signer.log"
        end if
    end try
end open location

-- Handler secundario: se ejecuta cuando se abre la app sin URL (doble clic)
on run
    log "================================"
    log "Maya Signer abierto sin URL (doble clic)"
    log "================================"
    
    -- Obtener ruta al ejecutable
    set bundlePath to path to me as text
    set executablePath to POSIX path of (bundlePath & "Contents:MacOS:maya-signer")
    
    log "Ejecutable: " & executablePath
    
    -- Arrancar el servicio en modo background
    try
        set cmd to quoted form of executablePath & " --start-service > /tmp/maya-signer-service.log 2>&1 &"
        
        log "Iniciando servicio: " & cmd
        
        do shell script cmd
        
        log "✓ Servicio iniciado correctamente"
        
        -- Mostrar notificación
        display notification "Maya Signer está ejecutándose en segundo plano" with title "Maya Signer" sound name "Glass"
        
        -- Opcional: mostrar diálogo informativo
        display dialog "Maya Signer está ejecutándose en segundo plano." & return & return & ¬
            "El servicio procesará automáticamente las solicitudes desde el navegador." buttons {"OK"} default button "OK" with icon note giving up after 5
        
    on error errMsg number errNum
        log "ERROR iniciando servicio: " & errMsg & " (código: " & errNum & ")"
        
        display dialog "Error al iniciar Maya Signer:" & return & return & errMsg buttons {"Ver Log", "OK"} default button "OK" with icon stop
        
        if button returned of result is "Ver Log" then
            do shell script "open -a Console /tmp/maya-signer-service.log"
        end if
    end try
    
    -- Terminar la app AppleScript (el servicio sigue corriendo)
    quit
end run

-- Handler para cuando la app ya está corriendo y recibe una nueva URL
on reopen
    log "Maya Signer ya estaba abierto (reopen)"
    -- No hacer nada, el servicio ya está corriendo
end reopen
'''
    
    # Guardar el script fuente
    script_source_file = resources_dir / "MayaSignerHandler.applescript"
    script_source_file.write_text(applescript_source)
    applet_path = macos_dir / "applet"
    
    print("✓ AppleScript fuente creado")
    
    # Compilar el AppleScript a una aplicación
    print("Compilando AppleScript...")
    
    # osacompile crea el ejecutable "applet" dentro de MacOS/
    compile_cmd = [
        "osacompile",
        "-o", str(applet_path),  # Output es el Contents/ del bundle
        str(script_source_file)
    ]
    
    if not run_command(compile_cmd):
        print("❌ Error compilando AppleScript")
        return False
    
    print("✓ AppleScript compilado correctamente")
    
    # El ejecutable compilado debería estar en MacOS/applet
    if applet_path.exists():
        applet_path.chmod(0o755)
        print(f"✓ Ejecutable AppleScript: {applet_path}")
    else:
        print(f"⚠️  Advertencia: No se encontró el ejecutable applet en {applet_path}")
    
    return True

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
        "--volicon", str(build_dir.parent / "src" / "assets" / "icon.icns") if (build_dir.parent / "src" / "assets" / "icon.icns").exists() else "",
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

    # Añadir icono del volumen si existe
    icon_path = build_dir.parent / "src" / "assets" / "icon.icns"
    if icon_path.exists():
        cmd.insert(2, "--volicon")
        cmd.insert(3, str(icon_path))
    
    if not run_command(cmd, cwd=build_dir):
        print("❌ Error creando DMG")
        return False
    
    print(f"\n✓ DMG creado: {dmg_file}")
    
    # Información del DMG
    run_command(["hdiutil", "verify", str(dmg_file)])
    
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
2. Abre MayaSigner desde Applications (primera vez)
3. Permite los permisos cuando macOS lo solicite
4. El protocolo maya:// se registrará automáticamente

USO:
- Al hacer clic en un enlace maya:// en el navegador, se abrirá Maya Signer
- La aplicación procesará la solicitud de firma automáticamente
- También puedes iniciar el servicio manualmente desde Applications

DESINSTALACIÓN:
1. Arrastra MayaSigner.app a la Papelera
2. Elimina la carpeta ~/.maya_signer (opcional)

NOTA IMPORTANTE SOBRE SEGURIDAD:
En el primer arranque, macOS puede mostrar:
"MayaSigner.app no puede abrirse porque proviene de un desarrollador no identificado"

Para solucionarlo:
1. Haz clic derecho (Control+clic) en MayaSigner.app
2. Selecciona "Abrir"
3. Confirma "Abrir" en el diálogo

O en Preferencias del Sistema:
Seguridad y Privacidad → General → "Abrir de todas formas"

PERMISOS:
macOS puede solicitar permisos para:
- Accesibilidad (para firma con DNIe)
- Eventos de Apple (para manejar URLs maya://)

DEBUGGING:
Los logs se encuentran en:
~/Library/Logs/MayaSigner/

Para ver logs en tiempo real:
tail -f ~/Library/Logs/MayaSigner/client.log

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
    print(f"  3. Abre MayaSigner.app (primera vez con clic derecho → Abrir)")
    print(f"\nPara probar el protocolo:")
    print(f"  Abre en Safari: maya://sign?batch=123&url=https://test.com&token=abc")
    print(f"\nPara desinstalar:")
    print(f"  Arrastra MayaSigner.app a la Papelera")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())