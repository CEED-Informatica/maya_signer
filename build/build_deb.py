#!/usr/bin/env python3
"""
Crea un paquete .deb para Maya Signer en Linux
Generado por Claude Sonnet 4.5
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from manifest import __version__, __maintainer__, __description__, __package_name__

VERSION = __version__
PACKAGE_NAME = __package_name__
MAINTAINER = __maintainer__
DESCRIPTION = __description__

def run_command(cmd, cwd=None):
    """Ejecuta un comando y retorna el resultado"""
    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def create_deb_structure():
    """Crea la estructura de directorios para el .deb"""
    root_dir = Path(__file__).parent
    deb_root = Path(f"{root_dir}/dist/{PACKAGE_NAME}_{VERSION}")
    
    # Limpiar si existe
    if deb_root.exists():
        shutil.rmtree(deb_root)
    
    # Crear estructura
    dirs = [
        deb_root / "DEBIAN",
        deb_root / "opt" / "maya-signer",
        deb_root / "usr" / "share" / "applications",
        deb_root / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps",
        deb_root / "usr" / "bin",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Establecer permisos correctos para DEBIAN (debe ser 0755)
    (deb_root / "DEBIAN").chmod(0o755)
    
    return deb_root

def compile_executables():
    """Compila los ejecutables con PyInstaller"""
    print("\n" + "="*60)
    print("COMPILANDO EJECUTABLES")
    print("="*60)
    
    # Directorio build
    build_dir = Path(__file__).parent
    spec_file = build_dir / "maya-signer.spec"
    
    if not spec_file.exists():
        print(f"❌ Error: No se encontró {spec_file}")
        return False
    
    # Limpiar dist anterior (solo en el directorio raíz)
    root_dir = build_dir.parent
    dist_dir = root_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Ejecutar PyInstaller desde el directorio build
    if not run_command(["pyinstaller", str(spec_file)], cwd=build_dir):
        print("❌ Error compilando con PyInstaller")
        return False
    
    # Los ejecutables estarán en build/dist/
    exe_dir = build_dir / "dist"
    
    # Verificar que se crearon los ejecutables
    if not (exe_dir / "maya-signer").exists() or not (exe_dir / "maya-signer-service").exists() \
        or not (exe_dir / "maya-signer-worker").exists():
        print("❌ No se encontraron los ejecutables compilados")
        print(f"   Buscando en: {exe_dir}")
        return False
    
    print("✓ Ejecutables compilados correctamente")
    return True

def copy_executables(deb_root):
    """Copia los ejecutables al paquete"""
    print("\nCopiando ejecutables...")
    
    build_dir = Path(__file__).parent
    exe_dir = build_dir / "dist"
    opt_dir = deb_root / "opt" / "maya-signer"
    
    # Copiar ejecutables
    shutil.copy(exe_dir / "maya-signer", opt_dir / "maya-signer")
    shutil.copy(exe_dir / "maya-signer-service", opt_dir / "maya-signer-service")
    shutil.copy(exe_dir / "maya-signer-worker", opt_dir / "maya-signer-worker")

    # Dar permisos de ejecución
    (opt_dir / "maya-signer").chmod(0o755)
    (opt_dir / "maya-signer-service").chmod(0o755)
    (opt_dir / "maya-signer-worker").chmod(0o755)

    # Crear enlaces simbólicos en /usr/bin
    bin_dir = deb_root / "usr" / "bin"
    os.symlink("/opt/maya-signer/maya-signer", bin_dir / "maya-signer")
    
    print("✓ Ejecutables copiados")

def create_desktop_file(deb_root):
    """Crea el archivo .desktop para el registro del protocolo"""
    print("\nCreando archivo .desktop...")
    
    desktop_file = deb_root / "usr" / "share" / "applications" / "maya-signer.desktop"
    
    content = f"""[Desktop Entry]
Version={VERSION}
Encoding=UTF-8
Type=Application
Name=Maya Signer
Comment=Servicio de firma electrónica para Maya
Exec=/opt/maya-signer/maya-signer %u
Icon=maya-signer
Terminal=false
MimeType=x-scheme-handler/maya;
Categories=Utility;Office;
StartupNotify=false
"""
    
    desktop_file.write_text(content, encoding='utf-8')
    desktop_file.chmod(0o755)
    
    print("✓ Archivo .desktop creado")

def create_icon(deb_root):
    """Copia o crea el icono de la aplicación"""
    print("\nCreando icono...")
    
    # Buscar icon.png en src/assets
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    icon_src = root_dir / "src" / "assets" / "icon.png"
    icon_dest = deb_root / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps" / "maya-signer.png"
    
    if icon_src.exists():
        shutil.copy(icon_src, icon_dest)
        print("✓ Icono copiado")
    else:
        print("⚠ No se encontró icon.png, usando icono genérico")

def create_postinst_script(deb_root):
    """Crea el script post-instalación"""
    print("\nCreando script postinst...")
    
    postinst = deb_root / "DEBIAN" / "postinst"
    
    content = """#!/bin/bash
set -e

# Actualizar base de datos de aplicaciones
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi

# Registrar el protocolo maya://
if command -v xdg-mime &> /dev/null; then
    xdg-mime default maya-signer.desktop x-scheme-handler/maya || true
fi

# Actualizar caché de iconos
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi

echo "Maya Signer instalado correctamente"
echo "El protocolo maya:// ha sido registrado"

exit 0
"""
    
    postinst.write_text(content)
    postinst.chmod(0o755)
    
    print("✓ Script postinst creado")

def create_postrm_script(deb_root):
    """Crea el script post-desinstalación"""
    print("\nCreando script postrm...")
    
    postrm = deb_root / "DEBIAN" / "postrm"
    
    content = """#!/bin/bash
set -e

# Limpiar configuración de usuario si se purga
if [ "$1" = "purge" ]; then
    for home_dir in /home/*; do
        if [ -d "$home_dir/.maya_signer" ]; then
            rm -rf "$home_dir/.maya_signer"
        fi
    done
fi

# Actualizar base de datos de aplicaciones
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi

exit 0
"""
    
    postrm.write_text(content)
    postrm.chmod(0o755)
    
    print("✓ Script postrm creado")

def create_control_file(deb_root):
    """Crea el archivo control del paquete"""
    print("\nCreando archivo control...")
    
    control = deb_root / "DEBIAN" / "control"
    
    # Calcular tamaño instalado
    size = 0
    counted_files = set()  # Para evitar contar el mismo archivo dos veces
    
    for root, dirs, files in os.walk(deb_root):
      for name in files:
        file_path = os.path.join(root, name)
        
        # Si es un enlace simbólico, obtener el archivo real
        if os.path.islink(file_path):
          # Resolver el enlace a la ruta real
          real_path = os.path.realpath(file_path)
          # Si el archivo real está dentro de deb_root, lo contaremos cuando lo encontremos
          # Si está fuera (enlace externo), contar el tamaño del destino
          if not real_path.startswith(str(deb_root)):
            try:
                if real_path not in counted_files:
                    size += os.path.getsize(real_path)
                    counted_files.add(real_path)
            except OSError:
                pass
        else:
          # Archivo normal
          try:
            abs_path = os.path.abspath(file_path)
            if abs_path not in counted_files:
                size += os.path.getsize(file_path)
                counted_files.add(abs_path)
          except OSError:
            pass
    
    installed_size = size // 1024  # Convertir a KB
    
    content = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-shape0, libxcb-xinerama0, libxcb-xfixes0
Recommends: opensc, pcscd
Maintainer: {MAINTAINER}
Homepage: https://maya-aqss.github.io/maya-signer/
Description: {DESCRIPTION}
 Maya Signer es un servicio de firma electrónica que permite
 firmar documentos PDF desde el sistema Maya (Odoo) usando
 certificados digitales o DNIe.
 .
 Características:
  - Soporte para certificados .p12/.pfx
  - Soporte para DNIe (requiere opensc)
  - Integración con Maya vía protocolo maya://
  - Interfaz gráfica para gestión de credenciales
Installed-Size: {installed_size}
"""
    
    control.write_text(content, encoding='utf-8')
    control.chmod(0o755)
    
    print("✓ Archivo control creado")

def create_copyright_file(deb_root):
    """Crea el archivo de copyright"""
    print("\nCreando archivo copyright...")
    
    copyright_dir = deb_root / "usr" / "share" / "doc" / PACKAGE_NAME
    copyright_dir.mkdir(parents=True, exist_ok=True)
    
    copyright_file = copyright_dir / "copyright"
    
    content = f"""Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {PACKAGE_NAME}
Source: https://github.com/Maya-AQSS/maya-signer

Files: *
Copyright: 2025 {MAINTAINER}
License: GPL 3.0
"""
    
    copyright_file.write_text(content)
    
    print("✓ Archivo copyright creado")

def build_deb_package(deb_root):
    """Construye el paquete .deb"""
    print("\n" + "="*60)
    print("CONSTRUYENDO PAQUETE .DEB")
    print("="*60)
    
    deb_file = f"{PACKAGE_NAME}_{VERSION}_amd64.deb"
    
    # Construir con dpkg-deb
    if not run_command(["dpkg-deb", "--build", "--root-owner-group", str(deb_root), deb_file]):
        print("❌ Error construyendo el paquete .deb")
        return False
    
    print(f"\n✓ Paquete creado: {deb_file}")
    
    # Verificar el paquete
    print("\nVerificando paquete...")
    run_command(["dpkg-deb", "--info", deb_file])
    run_command(["dpkg-deb", "--contents", deb_file])
    
    return True

def main():
    print("="*60)
    print(f"MAYA SIGNER v{VERSION} - CREADOR DE PAQUETE .DEB")
    print("="*60)
    
    # Cambiar al directorio build
    build_dir = Path(__file__).parent
    os.chdir(build_dir.parent)  # Ir a la raíz del proyecto
    
    # 1. Compilar ejecutables
    if not compile_executables():
        return 1
    
    # 2. Crear estructura del .deb
    print("\n" + "="*60)
    print("CREANDO ESTRUCTURA DEL PAQUETE")
    print("="*60)
    deb_root = create_deb_structure()
    
    # 3. Copiar archivos
    copy_executables(deb_root)
    create_desktop_file(deb_root)
    create_icon(deb_root)
    
    # 4. Crear scripts de mantenimiento
    create_postinst_script(deb_root)
    create_postrm_script(deb_root)
    
    # 5. Crear archivos de control
    create_control_file(deb_root)
    create_copyright_file(deb_root)
    
    # 6. Construir el paquete
    if not build_deb_package(deb_root):
        return 1
    
    # 7. Limpiar archivos temporales (opcional)
    print("\nLimpiando archivos temporales...")
    # shutil.rmtree(deb_root)  # Comentado para inspección
    
    print("\n" + "="*60)
    print("¡PAQUETE .DEB CREADO EXITOSAMENTE!")
    print("="*60)
    print(f"\nPara instalar:\n  sudo dpkg -i {PACKAGE_NAME}_{VERSION}_amd64.deb")
    print(f"\nPara desinstalar:\n  sudo apt remove {PACKAGE_NAME}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())