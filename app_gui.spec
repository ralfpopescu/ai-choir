# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the site-packages directory from the virtual environment
venv_site_packages = os.path.join('venv', 'lib', 'python{}.{}'.format(sys.version_info.major, sys.version_info.minor), 'site-packages')

a = Analysis(
    ['app_gui.py'],
    pathex=[venv_site_packages],  # Add virtual environment site-packages to path
    binaries=[],
    datas=collect_data_files('your_main_package'),  # Replace with your main package name
    hiddenimports=collect_submodules('your_main_package'),  # Replace with your main package name
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
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.name == 'nt' else 'icon.icns',
) 