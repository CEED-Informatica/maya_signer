# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Archivos de datos adicionales
added_files = [
    ('installer/install_protocol.py', 'installer'),
    ('installer/uninstall.py', 'installer'),
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'xmlrpc.client',
        'cryptography',
        'pyhanko',
        'pyhanko.sign',
        'pyhanko.pdf_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='maya-signer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False para app GUI, True para ver logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if sys.platform == 'win32' else 'assets/icon.icns',
)

# En macOS, crear bundle .app
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='MayaSigner.app',
        icon='assets/icon.icns',
        bundle_identifier='com.maya.signer',
        info_plist={
            'CFBundleURLTypes': [{
                'CFBundleURLName': 'Maya Protocol',
                'CFBundleURLSchemes': ['maya']
            }],
            'LSBackgroundOnly': False,
        },
    )