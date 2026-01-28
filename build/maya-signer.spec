# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(SPEC).parent.parent))
from manifest import __version__

block_cipher = None

# Rutas
src_path = '../src'

# Análisis del servicio
service_a = Analysis(
    [f'{src_path}/maya_signer_service.py'],
    pathex=[src_path],
    binaries=[],
    datas=[
        (f'{src_path}/assets/icon.png', '.') if os.path.exists(f'{src_path}/assets/icon.png') else ('', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pyhanko',
        'pyhanko.sign',
        'pyhanko.sign.signers',
        'pyhanko.sign.fields',
        'pyhanko.sign.pkcs11',
        'pyhanko.pdf_utils',
        'pyhanko.pdf_utils.incremental_writer',
        'cryptography',
        'cryptography.hazmat.primitives.serialization',
        'xmlrpc.client',
        'http.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

service_pyz = PYZ(service_a.pure, service_a.zipped_data, cipher=block_cipher)

service_exe = EXE(
    service_pyz,
    service_a.scripts,
    service_a.binaries,
    service_a.zipfiles,
    service_a.datas,
    [],
    name='maya-signer-service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Análisis del cliente principal
main_a = Analysis(
    [f'{src_path}/main.py'],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=['requests', 'urllib.parse'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)

main_exe = EXE(
    main_pyz,
    main_a.scripts,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    [],
    name='maya-signer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
