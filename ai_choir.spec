# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'models'),
        ('config.json', '.'),
        ('impulse.wav', '.'),
        ('gen.py', '.'),
        ('gen_process.py', '.'),
        ('gen_curve.py', '.'),
        ('gen_combine.py', '.'),
        ('gen_convolve.py', '.'),
        ('util.py', '.'),
        ('cleanup.py', '.'),
        ('so-vits-svc', 'so-vits-svc'),
        ('font.ttf', '.'),
        ('bg.png', '.'),
        ('bg-button.png', '.'),
        ('icon.png', '.'),
        ('icon.icns', '.'),
        ('icon.ico', '.'),
    ] + collect_data_files('torch') + collect_data_files('torchaudio') + collect_data_files('librosa') + collect_data_files('transformers'),
    hiddenimports=[
        # PySide6 / Qt
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # PyTorch
        'torch',
        'torch.nn',
        'torch.nn.functional',
        'torch.utils',
        'torch.utils.data',
        'torchaudio',
        'torchaudio.transforms',
        'torchaudio.functional',
        # Audio processing
        'pydub',
        'pydub.effects',
        'librosa',
        'librosa.core',
        'librosa.util',
        'soundfile',
        'scipy',
        'scipy.signal',
        'scipy.io',
        'scipy.io.wavfile',
        # ML / AI
        'fairseq',
        'transformers',
        'faiss',
        'sklearn',
        'sklearn.cluster',
        'numpy',
        'numba',
        # Voice processing
        'pyworld',
        'torchcrepe',
        'parselmouth',
        # Utilities
        'appdirs',
        'json',
        'importlib',
        'PIL',
        'resampy',
        'einops',
        'local_attention',
        # App modules
        'gen',
        'gen_process',
        'gen_curve',
        'gen_combine',
        'gen_convolve',
        'cleanup',
        'util',
    ] + collect_submodules('torch') + collect_submodules('torchaudio') + collect_submodules('fairseq') + collect_submodules('PySide6'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'Carbon', 'QuickTime', 'QTKit',
        'Carbon.Framework', 'QuickTime.Framework', 'QTKit.Framework',
        'tkinter', '_tkinter',
        'gradio', 'fastapi', 'uvicorn', 'flask',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ai_choir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ai_choir',
)

app = BUNDLE(
    coll,
    name='ai_choir.app',
    icon='icon.icns',
    bundle_identifier='com.offwhite.aichoir',
    info_plist={
        'CFBundleName': 'ai_choir',
        'CFBundleDisplayName': 'AI Choir',
        'CFBundleExecutable': 'ai_choir',
        'CFBundleIconFile': 'icon.icns',
        'CFBundleIdentifier': 'com.offwhite.aichoir',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
        'NSRequiresAquaSystemAppearance': False,
        'NSPrincipalClass': 'NSApplication',
        'LSMinimumSystemVersion': '10.15',
    },
)
