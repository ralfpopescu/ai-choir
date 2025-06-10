#!/usr/bin/env python3
import os
import sys
from PIL import Image
import subprocess
import shutil

def create_ico(png_path, output_path):
    """Convert PNG to ICO format"""
    img = Image.open(png_path)
    # ICO files typically contain multiple sizes
    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save(output_path, format='ICO', sizes=sizes)

def create_icns(png_path, output_path):
    """Convert PNG to ICNS format for macOS"""
    # Create temporary iconset directory
    iconset_dir = "icon.iconset"
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir)

    # Generate different icon sizes
    img = Image.open(png_path)
    sizes = {
        "16x16": 16,
        "32x32": 32,
        "64x64": 64,
        "128x128": 128,
        "256x256": 256,
        "512x512": 512,
        "1024x1024": 1024
    }

    # Create all required sizes
    for size_name, size in sizes.items():
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f"{iconset_dir}/icon_{size_name}.png")

    # Create the ICNS file using iconutil
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", output_path])

    # Clean up
    shutil.rmtree(iconset_dir)

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_icons.py <input_png>")
        sys.exit(1)

    png_path = sys.argv[1]
    if not os.path.exists(png_path):
        print(f"Error: File {png_path} does not exist")
        sys.exit(1)

    # Create ICO file
    create_ico(png_path, "icon.ico")
    print("Created icon.ico")

    # Create ICNS file
    create_icns(png_path, "icon.icns")
    print("Created icon.icns")

if __name__ == "__main__":
    main() 