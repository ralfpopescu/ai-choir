# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('models', 'models'), ('config.json', '.'), ('gen.py', '.'), ('gen_process.py', '.'), ('gen_curve.py', '.'), ('gen_combine.py', '.'), ('gen_convolve.py', '.'), ('util.py', '.'), ('font.ttf', '.'), ('bg.png', '.'), ('bg-button.png', '.'), ('icon.png', '.'), ('icon.icns', '.'), ('icon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['Carbon', 'QuickTime', 'QTKit', 'Carbon.Framework', 'QuickTime.Framework', 'QTKit.Framework'],
    noarchive=False,
    optimize=0,
)
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
    icon=None,
    bundle_identifier=None,
)
