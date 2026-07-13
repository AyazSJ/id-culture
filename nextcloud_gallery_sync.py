#!/usr/bin/env python3
"""
nextcloud_gallery_sync.py
──────────────────────────
Scans your Nextcloud public share for images and generates/updates
the .json gallery files that your detail pages use to load images.

HOW IT WORKS:
  1. Connects to your Nextcloud public share via WebDAV
  2. Lists image files in each subfolder (matching your entry slugs)
  3. Writes/updates designers/SLUG.json and companies/SLUG.json files
  4. Your site's gallery section reads these JSON files and loads the images

SETUP:
  1. In Nextcloud, share your id-history-images folder publicly (read-only, no password)
  2. Copy the share token from the URL (the part after /s/)
  3. Fill in the three config values below
  4. Run: python3 nextcloud_gallery_sync.py

REQUIREMENTS:
  pip3 install requests
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip3 install requests")
    sys.exit(1)

# ── CONFIGURE THESE THREE VALUES ─────────────────────────────────────────────

NEXTCLOUD_BASE_URL = "https://nextcloud.ayazsj.com"   # your Nextcloud URL (no trailing slash)
SHARE_TOKEN        = "KYT4SSFs69cirYB"                      # the token from your public share URL
IMAGE_FOLDER       = ""                  # root folder name in Nextcloud

# ─────────────────────────────────────────────────────────────────────────────

SITE_ROOT    = os.path.dirname(os.path.abspath(__file__))
DESIGNERS    = os.path.join(SITE_ROOT, "designers")
COMPANIES    = os.path.join(SITE_ROOT, "companies")

WEBDAV_BASE  = f"{NEXTCLOUD_BASE_URL}/public.php/webdav"
PUBLIC_BASE  = f"{NEXTCLOUD_BASE_URL}/s/{SHARE_TOKEN}/download"

IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}

def webdav_list(path=""):
    """List contents of a WebDAV path using PROPFIND."""
    url = f"{WEBDAV_BASE}/{path}".rstrip("/")
    resp = requests.request(
        "PROPFIND", url,
        headers={
            "Depth": "1",
            "Content-Type": "application/xml",
        },
        auth=(SHARE_TOKEN, ""),
        timeout=15,
    )
    if resp.status_code == 404:
        return []
    if resp.status_code not in (207, 200):
        print(f"  WebDAV error {resp.status_code} for {url}")
        return []

    # Parse the multistatus XML response
    ns = {"d": "DAV:"}
    root = ET.fromstring(resp.text)
    items = []
    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns).text
        # Decode URL encoding and strip the WebDAV prefix
        from urllib.parse import unquote
        decoded = unquote(href)
        # Strip the /public.php/webdav/ prefix
        rel = decoded.replace("/public.php/webdav/", "").lstrip("/")
        if rel == path.lstrip("/"):
            continue  # skip the folder itself
        is_collection = response.find(".//d:collection", ns) is not None
        items.append({"path": rel, "is_dir": is_collection})
    return items

def public_url(relative_path):
    """Convert a relative Nextcloud path to a public download URL."""
    # relative_path is like: id-history-images/dieter-rams/photo1.jpg
    # Strip the root image folder prefix
    parts = relative_path.split("/", 1)
    if len(parts) == 2:
        subfolder_and_file = parts[1]  # dieter-rams/photo1.jpg
        folder, filename = subfolder_and_file.rsplit("/", 1) if "/" in subfolder_and_file else ("", subfolder_and_file)
        return f"{PUBLIC_BASE}?path=/{folder}&files={filename}"
    return f"{PUBLIC_BASE}?path=/&files={relative_path}"

def slug_to_json_path(slug):
    """Find the JSON file for a slug in designers/ or companies/."""
    d_path = os.path.join(DESIGNERS, f"{slug}.json")
    c_path = os.path.join(COMPANIES, f"{slug}.json")
    if os.path.exists(d_path):
        return d_path
    if os.path.exists(c_path):
        return c_path
    return None

def update_json(json_path, slug, images):
    """Read existing JSON, merge in new images, write back."""
    existing = {"slug": slug, "images": []}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    # Build a set of existing URLs to avoid duplicates
    existing_urls = {img["file"] for img in existing.get("images", [])}

    added = 0
    for img in images:
        if img["file"] not in existing_urls:
            existing["images"].append(img)
            existing_urls.add(img["file"])
            added += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    return added

def caption_from_filename(filename):
    """Convert a filename to a readable caption."""
    stem = os.path.splitext(filename)[0]
    return stem.replace("-", " ").replace("_", " ").title()

def main():
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Nextcloud Gallery Sync")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if SHARE_TOKEN == "YOURSHARETOKEN":
        print("  ✗  Please edit the script and fill in your SHARE_TOKEN, NEXTCLOUD_BASE_URL")
        sys.exit(1)

    print(f"  Connecting to {NEXTCLOUD_BASE_URL} ...")

    # List top-level subfolders inside the image root
    root_contents = webdav_list(IMAGE_FOLDER)
    if not root_contents:
        print(f"  ✗  Could not list {IMAGE_FOLDER}/ — check your SHARE_TOKEN and NEXTCLOUD_BASE_URL")
        sys.exit(1)

    subfolders = [item for item in root_contents if item["is_dir"]]
    print(f"  Found {len(subfolders)} image folder(s)\n")

    total_images = 0
    total_updated = 0

    for folder in subfolders:
        folder_path = folder["path"]                     # e.g. id-history-images/dieter-rams
        slug = folder_path.rstrip("/").split("/")[-1]   # e.g. dieter-rams

        # List images in this folder
        contents = webdav_list(folder_path)
        images = []
        for item in contents:
            if item["is_dir"]:
                continue
            filename = item["path"].split("/")[-1]
            ext = os.path.splitext(filename)[1].lower()
            if ext not in IMAGE_EXTS:
                continue
            images.append({
                "file": public_url(item["path"]),
                "caption": caption_from_filename(filename),
            })

        if not images:
            continue

        # Find the matching JSON file
        json_path = slug_to_json_path(slug)
        if not json_path:
            print(f"  ⚠  No JSON found for slug '{slug}' — skipping")
            continue

        added = update_json(json_path, slug, images)
        total_images += len(images)
        if added:
            total_updated += 1
            print(f"  ✓  {slug} — {added} new image(s) added ({len(images)} total)")
        else:
            print(f"  –  {slug} — no new images (all already in JSON)")

    print(f"\n  Done — {total_images} images across {total_updated} updated entries\n")

if __name__ == "__main__":
    main()
