#!/usr/bin/env python3
"""Reshape the source icon art into a macOS-style rounded icon and build the
.icns. macOS app icons are a rounded square ("squircle") inset with transparent
padding (~83% of the canvas, ~22% corner radius) -- without this the icon shows
sharp corners and visually sticks out next to native apps.

Usage: python make_rounded_icns.py [source.png]   (default: icon.png)
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

CANVAS = 1024
MARGIN = 88                       # ~8.6% padding each side -> body ~82.8%
BODY = CANVAS - 2 * MARGIN        # 848
RADIUS = round(BODY * 0.2237)     # ~190, Apple's corner-radius ratio


def make_rounded(src):
    art = Image.open(src).convert("RGBA").resize((BODY, BODY), Image.LANCZOS)

    mask = Image.new("L", (BODY, BODY), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, BODY - 1, BODY - 1], radius=RADIUS, fill=255)
    # combine with any existing alpha so internal transparency is preserved
    art.putalpha(ImageChops.multiply(art.getchannel("A"), mask))

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(art, (MARGIN, MARGIN), art)
    return canvas


def build_icns(master, out_path):
    iconset = "icon.iconset"
    if os.path.exists(iconset):
        shutil.rmtree(iconset)
    os.makedirs(iconset)
    # Apple iconset: base size + @2x for each
    for base in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = base * scale
            name = f"icon_{base}x{base}{'@2x' if scale == 2 else ''}.png"
            master.resize((px, px), Image.LANCZOS).save(os.path.join(iconset, name))
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out_path], check=True)
    shutil.rmtree(iconset)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "icon.png"
    master = make_rounded(src)
    master.save("icon_rounded.png")
    build_icns(master, "icon.icns")
    print("Wrote icon_rounded.png and rounded icon.icns")


if __name__ == "__main__":
    main()
