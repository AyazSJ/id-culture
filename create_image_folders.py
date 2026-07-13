#!/usr/bin/env python3
"""
create_image_folders.py
────────────────────────
Reads the data array from index.html and creates an empty folder inside
images/ for every designer, company, and studio — using the exact same
slug naming convention as generate_page.py, so the folders line up with
the gallery paths your HTML pages already expect.

Usage:
    python3 create_image_folders.py

Safe to re-run any time you add new entries to index.html — it will
only create folders that don't already exist and will never touch or
delete folders that already have images in them.

Place this script in the root of your id-history site folder.
"""

import os
import re
import sys

INDEX_FILE  = "index.html"
IMAGES_ROOT = "images"


def parse_index_data(path: str) -> list[dict]:
    """Extract the JS data array from index.html."""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    m = re.search(r"const data\s*=\s*\[(.+?)\];\s*\n", source, re.DOTALL)
    if not m:
        print("✗ Could not find 'const data = [...]' in index.html")
        sys.exit(1)

    block = m.group(1)
    entries = []

    for obj_match in re.finditer(r"\{([^{}]+)\}", block, re.DOTALL):
        obj_text = obj_match.group(1)

        def field(key):
            fm = re.search(rf'{key}\s*:\s*"([^"]*)"', obj_text)
            return fm.group(1) if fm else ""

        name  = field("name")
        etype = field("type")

        if name and etype:
            entries.append({"name": name, "type": etype})

    return entries


def name_to_slug(name: str) -> str:
    """Same slug logic as generate_page.py — keep these in sync."""
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug


def main():
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Create Image Folders")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if not os.path.exists(INDEX_FILE):
        print(f"  ✗ {INDEX_FILE} not found. Run this from your site root.\n")
        sys.exit(1)

    entries = parse_index_data(INDEX_FILE)
    print(f"  Loaded {len(entries)} entries from index.html\n")

    os.makedirs(IMAGES_ROOT, exist_ok=True)

    created = []
    skipped = []

    for entry in entries:
        slug = name_to_slug(entry["name"])
        folder_path = os.path.join(IMAGES_ROOT, slug)

        if os.path.isdir(folder_path):
            skipped.append(slug)
        else:
            os.makedirs(folder_path)
            created.append(slug)

    if created:
        print(f"  Created {len(created)} new folder(s):\n")
        for slug in created:
            print(f"    + images/{slug}/")
    else:
        print("  No new folders needed.")

    if skipped:
        print(f"\n  Skipped {len(skipped)} folder(s) that already exist.")

    print(f"\n  ✓ Done. {len(created) + len(skipped)} total folders in images/\n")


if __name__ == "__main__":
    main()
