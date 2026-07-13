#!/usr/bin/env python3
"""
gallery_sync.py
───────────────
Generates or updates a gallery JSON file from a folder of images.

Usage:
    python gallery_sync.py                        # guided mode (prompts you)
    python gallery_sync.py designers/dieter-rams  # pass folder directly

The JSON it produces/updates looks like:
    {
      "images": [
        { "file": "../images/dieter-rams/t3-radio.jpg", "caption": "T3 radio" },
        ...
      ]
    }

Place this script in the root of your id-history site folder.
"""

import os
import json
import sys
import re

# ── Config ────────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}

# Where images live relative to the site root
IMAGES_ROOT = "images"

# Where JSON files live (same folder as the HTML files)
DESIGNERS_DIR = "designers"
COMPANIES_DIR = "companies"


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """Turn a folder name into a readable caption."""
    name = os.path.splitext(name)[0]          # strip extension
    name = re.sub(r"[-_]", " ", name)         # dashes/underscores → spaces
    name = re.sub(r"\s+", " ", name).strip()  # collapse whitespace
    return name.title()


def find_image_folder() -> str:
    """List available image folders and let the user pick one."""
    if not os.path.isdir(IMAGES_ROOT):
        print(f"\n  ✗ Could not find an '{IMAGES_ROOT}/' folder here.")
        print(f"    Make sure you're running this script from your site root.\n")
        sys.exit(1)

    folders = sorted([
        f for f in os.listdir(IMAGES_ROOT)
        if os.path.isdir(os.path.join(IMAGES_ROOT, f))
    ])

    if not folders:
        print(f"\n  ✗ '{IMAGES_ROOT}/' exists but has no subfolders yet.")
        print(f"    Create a folder like '{IMAGES_ROOT}/dieter-rams/' and add images.\n")
        sys.exit(1)

    print("\n  Available image folders:\n")
    for i, f in enumerate(folders, 1):
        count = len([
            x for x in os.listdir(os.path.join(IMAGES_ROOT, f))
            if os.path.splitext(x)[1].lower() in IMAGE_EXTENSIONS
        ])
        print(f"    [{i}] {f}  ({count} image{'s' if count != 1 else ''})")

    print()
    choice = input("  Enter a number, or type a folder name: ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(folders):
            return folders[idx]
        else:
            print("  ✗ Invalid number.\n")
            sys.exit(1)
    elif choice in folders:
        return choice
    else:
        print(f"  ✗ '{choice}' not found in {IMAGES_ROOT}/.\n")
        sys.exit(1)


def find_json_path(folder_name: str) -> str:
    """
    Work out where the JSON file should live.
    Checks designers/ first, then companies/, then asks if neither has a match.
    """
    designer_json = os.path.join(DESIGNERS_DIR, f"{folder_name}.json")
    company_json  = os.path.join(COMPANIES_DIR,  f"{folder_name}.json")

    if os.path.exists(designer_json):
        return designer_json
    if os.path.exists(company_json):
        return company_json

    # Neither exists yet — ask where to create it
    print(f"\n  No existing JSON found for '{folder_name}'.")
    print("  Where should it be created?\n")
    print("    [1] designers/")
    print("    [2] companies/")
    choice = input("\n  Enter 1 or 2: ").strip()
    if choice == "1":
        return designer_json
    elif choice == "2":
        return company_json
    else:
        print("  ✗ Invalid choice.\n")
        sys.exit(1)


def build_file_path(folder_name: str, filename: str, json_path: str) -> str:
    """
    Build the relative path from the JSON file's location to the image.
    e.g. JSON lives at designers/dieter-rams.json
         image lives at images/dieter-rams/t3.jpg
         → relative path: ../images/dieter-rams/t3.jpg
    """
    json_dir   = os.path.dirname(json_path)              # e.g. "designers"
    image_path = os.path.join(IMAGES_ROOT, folder_name, filename)
    # Compute relative path from json_dir to image_path
    rel = os.path.relpath(image_path, json_dir)
    # Normalise to forward slashes for web use
    return rel.replace("\\", "/")


def load_existing_json(json_path: str) -> list:
    """Load existing images array from JSON, or return empty list."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("images", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_image_files(folder_name: str) -> list:
    """Return sorted list of image filenames in the folder."""
    folder_path = os.path.join(IMAGES_ROOT, folder_name)
    return sorted([
        f for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Gallery JSON Sync")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 1. Determine which folder to process
    if len(sys.argv) > 1:
        folder_name = sys.argv[1].strip().rstrip("/\\")
        # Strip images/ prefix if user passed the full path
        if folder_name.startswith(IMAGES_ROOT + "/") or folder_name.startswith(IMAGES_ROOT + "\\"):
            folder_name = folder_name[len(IMAGES_ROOT)+1:]
        if not os.path.isdir(os.path.join(IMAGES_ROOT, folder_name)):
            print(f"\n  ✗ Folder '{IMAGES_ROOT}/{folder_name}' not found.\n")
            sys.exit(1)
    else:
        folder_name = find_image_folder()

    image_files = get_image_files(folder_name)
    print(f"\n  Found {len(image_files)} image(s) in '{IMAGES_ROOT}/{folder_name}/'")

    if not image_files:
        print("  Nothing to do — add images to the folder first.\n")
        sys.exit(0)

    # 2. Find or create the JSON file
    json_path = find_json_path(folder_name)

    # 3. Load existing entries so we can merge rather than overwrite
    existing = load_existing_json(json_path)
    existing_files = {entry["file"] for entry in existing}

    # 4. Build new entries for any images not already in the JSON
    new_entries = []
    for filename in image_files:
        file_ref = build_file_path(folder_name, filename, json_path)
        if file_ref not in existing_files:
            caption = slugify(filename)
            new_entries.append({"file": file_ref, "caption": caption})

    # 5. Report what we found
    if not new_entries:
        print("  ✓ JSON is already up to date — no new images to add.\n")
        print(f"    JSON: {json_path}")
        print(f"    Images: {len(existing)} entries\n")
        sys.exit(0)

    print(f"\n  {len(existing)} existing entr{'ies' if len(existing) != 1 else 'y'} in JSON")
    print(f"  {len(new_entries)} new image(s) to add:\n")
    for e in new_entries:
        print(f"    + {e['file']}")
        print(f"      Caption: \"{e['caption']}\"")

    # 6. Confirm before writing
    print()
    confirm = input("  Write to JSON? [Y/n]: ").strip().lower()
    if confirm not in ("", "y", "yes"):
        print("  Cancelled — nothing written.\n")
        sys.exit(0)

    # 7. Merge and write
    merged = existing + new_entries
    os.makedirs(os.path.dirname(json_path) if os.path.dirname(json_path) else ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"images": merged}, f, indent=2, ensure_ascii=False)

    print(f"\n  ✓ Written to {json_path}")
    print(f"    Total entries: {len(merged)}")
    print()
    print("  Tip: open the JSON and edit captions to be more descriptive,")
    print("  e.g. 'T3 Pocket Radio, Braun, 1958' instead of 'T3 Pocket Radio'")
    print()


if __name__ == "__main__":
    main()
