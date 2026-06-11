#!/bin/bash

# Build script for AI Choir Generator - macOS
# This script creates a working macOS app bundle using PyInstaller

set -e

echo "Building ai_choir for macOS..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
elif [ -d "env3.8" ]; then
    echo "Activating virtual environment (env3.8)..."
    source env3.8/bin/activate
fi

# Clean previous build artifacts
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Install PyInstaller if not already installed
pip install pyinstaller

# Build the application using the spec file
echo "Running PyInstaller..."
pyinstaller ai_choir.spec

echo ""
echo "Build complete!"
echo "App bundle: dist/ai_choir.app"
echo ""
echo "To create a DMG for distribution, run: ./create_dmg.sh"
echo "To sign the app, run: ./sign_mac.sh"
