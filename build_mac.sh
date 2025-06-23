#!/bin/bash

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install -r requirements_gui.txt

# Build the application
pyinstaller app_gui.spec

# Deactivate virtual environment
deactivate

# Create DMG
create-dmg \
    --volname "AI Choir Generator" \
    --volicon "icon.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "AI_Choir_Generator.app" 200 190 \
    --hide-extension "AI_Choir_Generator.app" \
    --app-drop-link 600 185 \
    "AI_Choir_Generator.dmg" \
    "dist/AI_Choir_Generator.app"

# Clean up virtual environment
rm -rf venv 