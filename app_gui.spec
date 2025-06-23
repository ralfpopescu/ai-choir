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

a = Analysis(
    ['app_gui.py'],
    pathex=[venv_site_packages],  # Add virtual environment site-packages to path
    binaries=[],
    datas=[
        ('models', 'models'),
        ('config.json', '.'),
        ('gen.py', '.'),
        ('gen_process.py', '.'),
        ('gen_curve.py', '.'),
        ('gen_combine.py', '.'),
        ('gen_convolve.py', '.'),
        ('util.py', '.'),
        ('font.ttf', '.'),
        ('bg.png', '.'),
        ('bg-button.png', '.'),
        ('icon.png', '.'),
        ('icon.icns', '.'),
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.support',
        'PySide6.support.signature',
        'PySide6.support.signature.typing',
        'PySide6.support.signature.lib',
        'PySide6.support.signature.mapping',
        'PySide6.support.signature.qtcore',
        'PySide6.support.signature.qtgui',
        'PySide6.support.signature.qtwidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'Carbon', 'QuickTime', 'QTKit', 'Carbon.Framework', 'QuickTime.Framework', 'QTKit.Framework',
        'win32api', 'win32com', 'win32gui', 'win32ui', 'win32con', 'win32clipboard',
        'com', 'java', 'org', 'nt', 'ntpath', '_winapi', '_winreg', 'msvcrt',
        'vms_lib', 'java.lang', 'com.sun'
    ],
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
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='AI_Choir_Generator.app',
        icon='icon.icns',
        bundle_identifier='com.offwhite.aichoir',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSRequiresAquaSystemAppearance': 'False',
            'NSPrincipalClass': 'NSApplication',
        },
    )
