# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Set CODESIGN_IDENTITY to a "Developer ID Application: ..." identity to sign
# every binary during the build (much more reliable than codesign --deep after
# the fact). Leave it unset for an unsigned development build.
codesign_identity = os.environ.get('CODESIGN_IDENTITY') or None
entitlements_file = 'entitlements.plist' if codesign_identity else None

a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Voice models (~3.7 GB) and the hubert checkpoint (inside so-vits-svc/
        # pretrain) are bundled so the app is fully self-contained — no
        # download URLs to rot. Run download_models.py before building.
        ('models', 'models'),
        ('so-vits-svc', 'so-vits-svc'),
        ('config.json', '.'),
        ('impulse.wav', '.'),
        ('font.ttf', '.'),
        ('bg.png', '.'),
        ('bg-button.png', '.'),
        ('icon.png', '.'),
        ('icon.icns', '.'),
    ] + collect_data_files('librosa')
      # fairseq discovers its plugins (criterions, tasks, models, ...) via
      # os.listdir on the package dir, so the .py tree must exist on disk
      + collect_data_files('fairseq', include_py_files=True),
    hiddenimports=[
        # PySide6 / Qt (only the modules the app imports)
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # Audio processing
        'pydub',
        'pydub.effects',
        'librosa',
        'soundfile',
        'scipy.signal',
        'scipy.io.wavfile',
        # ML / AI (imported at runtime by the so-vits-svc data files)
        'torch',
        'torchaudio',
        'fairseq',
        'faiss',
        'sklearn',
        'sklearn.cluster',
        'numpy',
        'numba',
        'antlr4',
        'transformers',
        # Voice processing
        'pyworld',
        'torchcrepe',
        'parselmouth',
        # Utilities
        'appdirs',
        'requests',
        'PIL',
        'resampy',
        'einops',
        'local_attention',
        # App pipeline modules (imported lazily inside gen.py)
        'gen',
        'gen_process',
        'gen_curve',
        'gen_combine',
        'gen_convolve',
        'cleanup',
        'util',
        'model_manager',
    ] + collect_submodules('fairseq'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_site_builtins.py'],
    excludes=[
        'tkinter', '_tkinter',
        'gradio', 'fastapi', 'uvicorn', 'flask',
        'tensorboard', 'tensorboardX',
        'onnx', 'onnxoptimizer', 'onnxsim',
        'IPython', 'jupyter',
    ],
    noarchive=False,
    optimize=0,
)

# Don't ship .DS_Store junk or audio left behind in results/raw by dev runs.
_sovits_root = os.path.join('so-vits-svc', 'so-vits-svc-4.1-Stable')
_excluded_dirs = (
    os.path.join(_sovits_root, 'results'),
    os.path.join(_sovits_root, 'raw'),
)
a.datas = [
    d for d in a.datas
    if not d[0].endswith('.DS_Store')
    and not any(d[0].startswith(p + os.sep) for p in _excluded_dirs)
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ai_choir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=codesign_identity,
    entitlements_file=entitlements_file,
    icon='icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
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
        'LSMinimumSystemVersion': '11.0',
    },
)
