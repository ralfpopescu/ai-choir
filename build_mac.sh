#!/bin/bash
# Build, sign, and package ai_choir for macOS distribution.
#
# Usage:
#   ./build_mac.sh                        # build + sign with auto-detected Developer ID + DMG
#   CODESIGN_IDENTITY="" ./build_mac.sh   # unsigned dev build
#   NOTARY_PROFILE=ai-choir ./build_mac.sh  # also notarize + staple
#     (one-time setup: xcrun notarytool store-credentials ai-choir \
#        --apple-id you@example.com --team-id JY7MWPBBYW --password <app-specific-pw>)

set -e
cd "$(dirname "$0")"

# --- signing identity -------------------------------------------------------
if [ -z "${CODESIGN_IDENTITY+x}" ]; then
    CODESIGN_IDENTITY=$(security find-identity -v -p codesigning \
        | sed -n 's/.*"\(Developer ID Application: [^"]*\)".*/\1/p' | head -1)
fi
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Signing with: $CODESIGN_IDENTITY"
else
    echo "No signing identity — building unsigned (dev only)."
fi
export CODESIGN_IDENTITY

# --- build ------------------------------------------------------------------
source venv/bin/activate

echo "Cleaning previous builds..."
# Rename before deleting: if dist/ is open in Finder, it rewrites .DS_Store
# mid-delete and plain `rm -rf` fails with "Directory not empty". The rename
# is atomic, so the delete can't race with Finder, and PyInstaller gets a
# fresh dist/ immediately.
for d in build dist; do
    if [ -d "$d" ]; then
        mv "$d" ".$d.old.$$"
        rm -rf ".$d.old.$$" || rm -rf ".$d.old.$$"
    fi
done

echo "Running PyInstaller (this takes a few minutes)..."
pyinstaller --noconfirm ai_choir.spec

APP="dist/ai_choir.app"

if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Verifying signature..."
    codesign --verify --deep --strict "$APP"
    echo "Signature OK."
fi

# --- DMG --------------------------------------------------------------------
DMG="dist/ai_choir.dmg"
echo "Creating DMG..."
rm -f "$DMG"
STAGING=$(mktemp -d)
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "ai_choir" -srcfolder "$STAGING" -ov -format UDZO "$DMG" -quiet
rm -rf "$STAGING"

if [ -n "$CODESIGN_IDENTITY" ]; then
    codesign --force --sign "$CODESIGN_IDENTITY" "$DMG"
fi

# --- notarization (optional) ------------------------------------------------
if [ -n "$NOTARY_PROFILE" ] && [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Submitting for notarization (profile: $NOTARY_PROFILE)..."
    xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
    xcrun stapler staple "$DMG"
    echo "Notarized and stapled."
else
    echo ""
    echo "NOTE: not notarized. Recipients will need to right-click > Open the"
    echo "first time they run the app. To notarize, store credentials once:"
    echo "  xcrun notarytool store-credentials ai-choir --apple-id <apple-id> --team-id JY7MWPBBYW --password <app-specific-password>"
    echo "then rebuild with: NOTARY_PROFILE=ai-choir ./build_mac.sh"
fi

echo ""
echo "Build complete!"
echo "  App: $APP"
echo "  DMG: $DMG"
