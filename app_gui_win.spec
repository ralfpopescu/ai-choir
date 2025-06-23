# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the site-packages directory from the virtual environment
venv_site_packages = os.path.join('venv', 'lib', 'python{}.{}'.format(sys.version_info.major, sys.version_info.minor), 'site-packages')

# Collect all model files
model_files = []
for root, dirs, files in os.walk('models'):
    for file in files:
        if file.endswith(('.pth', '.json')):
            model_files.append((os.path.join(root, file), root))

# Collect all asset files
asset_files = [
    ('icon.ico', '.'),
    ('icon.png', '.'),
    ('bg.png', '.'),
    ('bg-button.png', '.'),
    ('font.ttf', '.'),
]

# Windows-specific DLLs
windows_dlls = [
    ('C:\\Windows\\System32\\vcruntime140.dll', '.'),
    ('C:\\Windows\\System32\\msvcp140.dll', '.'),
    ('C:\\Windows\\System32\\vcruntime140_1.dll', '.'),
]

a = Analysis(
    ['app_gui.py'],
    pathex=[venv_site_packages],  # Add virtual environment site-packages to path
    binaries=windows_dlls,  # Include Windows DLLs
    datas=model_files + asset_files,  # Include all model and asset files
    hiddenimports=[
        'torch',
        'torchaudio',
        'numpy',
        'librosa',
        'soundfile',
        'scipy',
        'sklearn',
        'PySide6',
        'appdirs',
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
    name='AI_Choir_Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,  # Disable argv emulation for Windows
    target_arch='x86_64',  # Target 64-bit Windows
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Use .ico for Windows
) 