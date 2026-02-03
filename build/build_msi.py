#!/usr/bin/env python3
"""
Crea un instalador MSI para Maya Signer en Windows
Requiere: pyinstaller, WiX Toolset 6
Generado por Claude Sonnet 4.5 (adaptado aoltra)
"""

import os
import sys
import shutil
import subprocess
import uuid
from pathlib import Path

# Añadir el directorio raíz al path para importar version
sys.path.insert(0, str(Path(__file__).parent.parent))
from manifest import __version__, __maintainer__, __description__, __package_name__


VERSION = __version__
PACKAGE_NAME = __package_name__
AUTHOR = __maintainer__.replace('>', '&gt;').replace('<', '&lt;')
DESCRIPTION = __description__

# Para MSI, la versión debe tener exactamente 3 números (X.Y.Z)
MSI_VERSION = '.'.join(VERSION.split('.')[:3])

def run_command(cmd, cwd=None):
    """Ejecuta un comando y retorna el resultado"""
    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def compile_executables():
    """Compila los ejecutables con PyInstaller"""
    print("\n" + "="*60)
    print("COMPILANDO EJECUTABLES PARA WINDOWS")
    print("="*60)
    
    build_dir = Path(__file__).parent
    spec_file = build_dir / "maya-signer.spec"  # ← Usa el spec unificado
    
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
    if not (exe_dir / "maya-signer.exe").exists() or not (exe_dir / "maya-signer-service.exe").exists() \
        or not (exe_dir / "maya-signer-worker.exe").exists():
        print("❌ No se encontraron los ejecutables compilados")
        print(f"   Buscando en: {exe_dir}")
        return False
    
    print("✓ Ejecutables compilados correctamente")
    return True

def create_wxs_file():
    """Crea el archivo WXS para WiX Toolset 6"""
    print("\n" + "="*60)
    print("CREANDO ARCHIVO WXS")
    print("="*60)
    
    build_dir = Path(__file__).parent
    wxs_file = build_dir / "maya-signer.wxs"
    
    # Generar GUIDs únicos (en producción, estos deberían ser fijos)
    upgrade_code = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'maya-signer-upgrade-{VERSION}'))
    product_id = "*"  # WiX generará uno automáticamente
    
    # WiX 6 usa el namespace actualizado
    wxs_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package Name="Maya Signer" 
           Language="1033" 
           Version="{MSI_VERSION}" 
           Manufacturer="{AUTHOR}" 
           UpgradeCode="{upgrade_code}">
    
    <SummaryInformation Description="{DESCRIPTION}"
                        Comments="Servicio de firma electrónica para Maya (Odoo)"
                        Manufacturer="{AUTHOR}" />

    <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." />
    
    <MediaTemplate EmbedCab="yes" />

    <!-- Iconos -->
    <Icon Id="icon.ico" SourceFile="dist\\maya-signer.exe" />
    <Property Id="ARPPRODUCTICON" Value="icon.ico" />

    <!-- UI -->
    <WixVariable Id="WixUILicenseRtf" Value="license.rtf" />

    <!-- Estructura de directorios -->
    <StandardDirectory Id="ProgramFilesFolder">
      <Directory Id="INSTALLFOLDER" Name="Maya Signer">
        
        <!-- Ejecutable principal -->
        <Component Id="MainExecutable" Guid="{str(uuid.uuid5(uuid.NAMESPACE_DNS, 'maya-signer-exe'))}">
          <File Id="MayaSignerEXE" 
                Source="dist\\maya-signer.exe" />
        </Component>

        <!-- Servicio -->
        <Component Id="ServiceExecutable" Guid="{str(uuid.uuid5(uuid.NAMESPACE_DNS, 'maya-signer-service'))}">
          <File Id="MayaSignerServiceEXE" 
                Source="dist\\maya-signer-service.exe" />
        </Component>

        <!-- Worker -->
        <Component Id="WorkerExecutable" Guid="{str(uuid.uuid5(uuid.NAMESPACE_DNS, 'maya-signer-worker'))}">
          <File Id="MayaSignerWorkerEXE" 
                Source="dist\\maya-signer-worker.exe" />
        </Component>

        <!-- Registro del protocolo maya:// -->
        <Component Id="ProtocolHandler" Guid="{str(uuid.uuid5(uuid.NAMESPACE_DNS, 'maya-protocol'))}">
          <RegistryKey Root="HKCR" Key="maya">
            <RegistryValue Type="string" Value="URL:Maya Protocol" />
            <RegistryValue Name="URL Protocol" Type="string" Value="" />
            
            <RegistryKey Key="DefaultIcon">
              <RegistryValue Type="string" Value="[INSTALLFOLDER]maya-signer.exe,0" />
            </RegistryKey>
            
            <RegistryKey Key="shell\\open\\command">
              <RegistryValue Type="string" Value='"[INSTALLFOLDER]maya-signer.exe" "%1"' />
            </RegistryKey>
          </RegistryKey>
        </Component>

      </Directory>
    </StandardDirectory>

    <!-- Acceso directo en menú inicio -->
    <StandardDirectory Id="ProgramMenuFolder">
      <Directory Id="ApplicationProgramsFolder" Name="Maya Signer">
        <Component Id="ApplicationShortcut" Guid="{str(uuid.uuid5(uuid.NAMESPACE_DNS, 'maya-signer-shortcut'))}">
          <Shortcut Id="ApplicationStartMenuShortcut"
                    Name="Maya Signer"
                    Description="Servicio de firma electrónica"
                    Target="[INSTALLFOLDER]maya-signer.exe"
                    Arguments="--start-service"
                    WorkingDirectory="INSTALLFOLDER"/>
          <RemoveFolder Id="CleanUpShortCut" On="uninstall"/>
          <RegistryValue Root="HKCU" 
                         Key="Software\\MayaSigner" 
                         Name="installed" 
                         Type="integer" 
                         Value="1" 
                         KeyPath="yes"/>
        </Component>
      </Directory>
    </StandardDirectory>

    <!-- Features -->
    <Feature Id="ProductFeature" Title="Maya Signer" Level="1">
      <ComponentRef Id="MainExecutable" />
      <ComponentRef Id="ServiceExecutable" />
      <ComponentRef Id="WorkerExecutable" />
      <ComponentRef Id="ApplicationShortcut" />
      <ComponentRef Id="ProtocolHandler" />
    </Feature>

    <!-- UI Reference -->
    <ui:WixUI Id="WixUI_InstallDir" 
              InstallDirectory="INSTALLFOLDER"
              xmlns:ui="http://wixtoolset.org/schemas/v4/wxs/ui" />

  </Package>
</Wix>
"""
    
    wxs_file.write_text(wxs_content, encoding='utf-8')
    print(f"✓ Archivo WXS creado: {wxs_file}")
    return wxs_file

def create_license_rtf():
    """Crea un archivo de licencia RTF simple"""
    build_dir = Path(__file__).parent
    license_file = build_dir / "license.rtf"
    
    license_content = r"""{{\rtf1\ansi\deff0
{{\fonttbl{{\f0 Arial;}}}}
{{\colortbl;\red0\green0\blue0;}}}
\f0\fs20
\par Maya Signer - Licencia GPL 3.0
\par
\par Copyright (c) 2025 """ + AUTHOR + r"""
\par
\par
}}"""
    
    license_file.write_text(license_content, encoding='utf-8')
    print(f"✓ Archivo de licencia creado: {license_file}")

def build_msi():
    """Construye el MSI usando WiX Toolset 6"""
    print("\n" + "="*60)
    print("CONSTRUYENDO MSI CON WIX TOOLSET 6")
    print("="*60)
    
    build_dir = Path(__file__).parent
    wxs_file = build_dir / "maya-signer.wxs"
    msi_file = build_dir.parent / f"maya-signer_{VERSION}_x64.msi"
    
    # Verificar que WiX 6 está instalado
    wix = shutil.which("wix.exe")
    
    if not wix:
        print("❌ WiX Toolset 6 no encontrado.")
        print("\nPara instalar WiX 6:")
        print("1. Usando dotnet tool:")
        print("   dotnet tool install --global wix")
        print("\n2. O descarga desde: https://wixtoolset.org/")
        print("\n3. Asegúrate de que 'wix.exe' está en el PATH")
        return False
    
    print(f"✓ WiX 6 encontrado: {wix}")
    
    # WiX 6 simplifica el proceso: un solo comando para compilar y linkear
    print("\nGenerando archivo MSI...")
    if not run_command([
        "wix.exe",
        "build",
        "-arch", "x64",
        "-ext", "WixToolset.UI.wixext",
        str(wxs_file),
        "-out", str(msi_file)
    ], cwd=build_dir):
        print("❌ Error generando MSI")
        return False
    
    print(f"\n✓ MSI creado: {msi_file}")
    
    return True

def main():
    print("="*60)
    print(f"MAYA SIGNER v{VERSION} - CREADOR DE INSTALADOR MSI")
    print("="*60)
    print(f"Versión MSI: {MSI_VERSION}")
    print("WiX Toolset: 6.x")
    
    # Verificar que estamos en Windows
    if sys.platform != 'win32':
        print("❌ Este script solo funciona en Windows")
        return 1
    
    # Cambiar al directorio build
    build_dir = Path(__file__).parent
    os.chdir(build_dir.parent)
    
    # 1. Compilar ejecutables
    if not compile_executables():
        return 1
    
    # 2. Crear archivos necesarios para WiX
    create_license_rtf()
    wxs_file = create_wxs_file()
    
    # 3. Construir MSI
    if not build_msi():
        return 1
    
    print("\n" + "="*60)
    print("¡INSTALADOR MSI CREADO EXITOSAMENTE!")
    print("="*60)
    print(f"\nPara instalar:")
    print(f"  maya-signer_{VERSION}_x64.msi")
    print(f"\nPara desinstalar:")
    print(f"  Panel de Control → Programas → Desinstalar Maya Signer")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
