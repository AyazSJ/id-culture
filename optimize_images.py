#!/usr/bin/env python3
"""
optimize_images.py
Resizes and compresses all images in the images/ folder for web use.

REQUIREMENTS:
    pip install Pillow

USAGE:
    python optimize_images.py              # optimize everything
    python optimize_images.py dieter-rams  # optimize one entry only
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Missing dependency. Run: pip install Pillow")
    sys.exit(1)

MAX_WIDTH    = 1200
JPEG_QUALITY = 82
PNG_COMPRESS = 6
SUPPORTED    = {".jpg", ".jpeg", ".png", ".webp"}
IMAGES_ROOT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


def format_size(b):
    if b < 1024: return f"{b}B"
    if b < 1024 * 1024: return f"{b/1024:.1f}KB"
    return f"{b/1024/1024:.1f}MB"


def optimize(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED:
        return

    size_before = os.path.getsize(path)

    img = Image.open(path)
    w, h = img.size

    if w > MAX_WIDTH:
        new_h = int(h * MAX_WIDTH / w)
        img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

    if ext in (".jpg", ".jpeg"):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    elif ext == ".png":
        img.save(path, "PNG", compress_level=PNG_COMPRESS, optimize=True)
    elif ext == ".webp":
        img.save(path, "WEBP", quality=JPEG_QUALITY)

    size_after = os.path.getsize(path)
    saved = size_before - size_after
    new_w, new_h = Image.open(path).size

    print(f"  {os.path.basename(path)}")
    print(f"    {w}x{h} → {new_w}x{new_h}  |  {format_size(size_before)} → {format_size(size_after)}  |  saved {format_size(saved)}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target:
        folders = [os.path.join(IMAGES_ROOT, target)]
    else:
        folders = [
            os.path.join(IMAGES_ROOT, d)
            for d in sorted(os.listdir(IMAGES_ROOT))
            if os.path.isdir(os.path.join(IMAGES_ROOT, d))
        ]

    for folder in folders:
        name = os.path.basename(folder)
        print(f"\n{name}/")
        for filename in sorted(os.listdir(folder)):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                optimize(filepath)

    print("\nDone.")

if __name__ == "__main__":
    main()
