#!/bin/bash

# Check if identity is provided
if [ -z "$1" ]; then
    echo "Usage: ./sign_mac.sh <Developer ID Application: Your Name (TEAM_ID)>"
    echo "You can find your identity by running: security find-identity -v -p codesigning"
    exit 1
fi

IDENTITY="$1"
APP_PATH="dist/AI_Choir_Generator.app"
DMG_PATH="AI_Choir_Generator.dmg"

# Sign the app
echo "Signing the application..."
codesign --force --options runtime --sign "$IDENTITY" --deep "$APP_PATH"

# Verify the signature
echo "Verifying signature..."
codesign --verify --verbose=4 "$APP_PATH"

# Create DMG
echo "Creating DMG..."
create-dmg \
    --volname "AI Choir Generator" \
    --volicon "icon.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "AI_Choir_Generator.app" 200 190 \
    --hide-extension "AI_Choir_Generator.app" \
    --app-drop-link 600 185 \
    "$DMG_PATH" \
    "$APP_PATH"

# Sign the DMG
echo "Signing DMG..."
codesign --force --sign "$IDENTITY" "$DMG_PATH"

# Verify DMG signature
echo "Verifying DMG signature..."
codesign --verify --verbose=4 "$DMG_PATH"

echo "Done! Your signed DMG is ready at $DMG_PATH" 