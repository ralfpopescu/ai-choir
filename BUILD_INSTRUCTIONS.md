# AI Choir Generator - Build Instructions

## Prerequisites

1. **Python 3.8** - The project is tested with Python 3.8
2. **Virtual Environment** - Create and activate a virtual environment
3. **Dependencies** - Install required packages

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3.8 -m venv env3.8
   source env3.8/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements_gui.txt
   pip install -r requirements.txt
   ```

3. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

4. **Install create-dmg (optional, for DMG creation):**
   ```bash
   brew install create-dmg
   ```

## Building for macOS

### Quick Build
Use the provided build script:
```bash
chmod +x build_mac_working.sh
./build_mac_working.sh
```

### Manual Build
If you prefer to build manually, use this command:
```bash
pyinstaller \
    --exclude-module Carbon \
    --exclude-module QuickTime \
    --exclude-module QTKit \
    --exclude-module Carbon.Framework \
    --exclude-module QuickTime.Framework \
    --exclude-module QTKit.Framework \
    --add-data "models:models" \
    --add-data "config.json:." \
    --add-data "gen.py:." \
    --add-data "gen_process.py:." \
    --add-data "gen_curve.py:." \
    --add-data "gen_combine.py:." \
    --add-data "gen_convolve.py:." \
    --add-data "util.py:." \
    --add-data "font.ttf:." \
    --add-data "bg.png:." \
    --add-data "bg-button.png:." \
    --add-data "icon.png:." \
    --add-data "icon.icns:." \
    --add-data "icon.ico:." \
    --onedir \
    --windowed \
    --name "AI_Choir_Generator" \
    app_gui.py
```

## Important Notes

### Carbon Framework Issue
The app was originally failing due to Carbon framework dependencies. This was resolved by:
1. Using `--onedir` mode instead of `--onefile`
2. Excluding Carbon-related modules
3. Using a newer version of PyInstaller

### Resource Loading
The app uses a `get_resource_path()` function to properly load resources (images, fonts, etc.) both in development and when packaged.

### Output
- **App Bundle**: `dist/AI_Choir_Generator.app`
- **DMG File**: `AI_Choir_Generator.dmg` (if create-dmg is installed)

## Troubleshooting

### Images Not Showing
If images don't appear in the packaged app:
1. Ensure the `get_resource_path()` function is used for all resource loading
2. Check that image files are included in the `--add-data` arguments
3. Verify the app bundle contains the images in `Contents/Resources/`

### Carbon Framework Error
If you get Carbon framework errors:
1. Make sure you're using the `--exclude-module Carbon` arguments
2. Use `--onedir` mode instead of `--onefile`
3. Update PyInstaller to the latest version

### Large App Size
The app bundle is large (~3.5GB) because it includes:
- All AI/ML models
- PyTorch and related libraries
- Audio processing libraries
- PySide6 GUI framework

## Distribution

The final DMG file (`AI_Choir_Generator.dmg`) can be distributed to users. They can:
1. Double-click to mount the DMG
2. Drag the app to their Applications folder
3. Run the app normally

The app is self-contained and doesn't require additional installation of Python or dependencies. 