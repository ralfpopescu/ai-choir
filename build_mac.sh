#!/bin/bash

# Build script for AI Choir Generator - macOS
# Sets up a virtual environment, installs dependencies, and builds the app

set -e

echo "Building ai_choir for macOS..."

cd "$(dirname "$0")"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements_gui.txt

# Clean previous build artifacts
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Build the application
echo "Running PyInstaller..."
pyinstaller ai_choir.spec

# Deactivate virtual environment
deactivate

echo ""
echo "Build complete!"
echo "App bundle: dist/ai_choir.app"
