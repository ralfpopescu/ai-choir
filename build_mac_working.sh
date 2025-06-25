#!/bin/bash

# Build script for AI Choir Generator - macOS
# This script creates a working macOS app bundle using PyInstaller

echo "Building ai_choir for macOS..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "env3.8" ]; then
    echo "Activating virtual environment..."
    source env3.8/bin/activate
fi

# Build the application using the working configuration
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
    --name "ai_choir" \
    app_gui.py

echo "Build complete! App bundle is available at: dist/ai_choir.app"

# Optional: Create DMG if create-dmg is available
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG..."
    create-dmg \
        --volname "ai_choir" \
        --volicon "icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "ai_choir.app" 200 190 \
        --hide-extension "ai_choir.app" \
        --app-drop-link 600 185 \
        "ai_choir.dmg" \
        "dist/ai_choir.app"
    echo "DMG created: ai_choir.dmg"
else
    echo "create-dmg not found. Install with: brew install create-dmg"
fi 