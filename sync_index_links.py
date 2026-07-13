#!/usr/bin/env python3
"""
sync_index_links.py
───────────────────
Scans the designers/ and companies/ folders for generated HTML files,
matches them against entries in index.html, and adds the correct
page: "..." field to every matching entry so the cards become clickable.

Run this once after generate_page.py --all, or any time pages are added.

Usage:
    python3 sync_index_links.py
"""

import os
import re
import sys

INDEX_FILE    = "index.html"
DESIGNERS_DIR = "designers"
COMPANIES_DIR = "companies"

# Files managed manually — skip them so we don't overwrite existing page fields
SKIP_FILES = {"dieter-rams.html", "braun.html"}


def find_all_pages() -> dict:
    """
    Walk designers/ and companies/ and return a dict of:
        { "designers/william-morris.html": "designers", ... }
    """
    pages = {}
    for folder in (DESIGNERS_DIR, COMPANIES_DIR):
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            if fname.endswith(".html") and fname not in SKIP_FILES:
                path = os.path.join(folder, fname).replace("\\", "/")
                pages[path] = folder
    return pages


def extract_name_from_html(path: str):
    """
    Read the <title> tag from a generated page to get the entry name.
    Generated pages all have: <title>Name — ID History</title>
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"<title>(.+?)\s*\u2014\s*ID History</title>", content)
        if m:
            return m.group(1).strip()
        # Fallback: em-dash as literal characters
        m = re.search(r"<title>(.+?)\s*—\s*ID History</title>", content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def update_index(name: str, page_path: str, source: str):
    """
    Find the JS object with this name in the data array and insert/replace
    the page field. index.html uses unquoted JS keys: { name: "...", ... }
    Returns (new_source, changed).
    """
    name_escaped = re.escape(name)

    # Match the object on a single line (all entries are one-liners)
    pattern = re.compile(
        r'(\{[^\n{}]*?name\s*:\s*"' + name_escaped + r'"[^\n{}]*?\})'
    )

    match = pattern.search(source)
    if not match:
        return source, False

    obj_text = match.group(1)

    # Already has the correct page field — skip
    if f'page: "{page_path}"' in obj_text:
        return source, False

    # Remove any existing page field
    obj_cleaned = re.sub(r',\s*page\s*:\s*"[^"]*"', "", obj_text)
    obj_cleaned = re.sub(r'page\s*:\s*"[^"]*"\s*,\s*', "", obj_cleaned)

    # Insert page field right after the name value
    obj_updated = re.sub(
        r'(name\s*:\s*"' + name_escaped + r'")',
        r'\1, page: "' + page_path + r'"',
        obj_cleaned,
        count=1
    )

    new_source = source[:match.start()] + obj_updated + source[match.end():]
    return new_source, True


def main():
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Sync Index Links")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if not os.path.exists(INDEX_FILE):
        print(f"  ✗ {INDEX_FILE} not found. Run from your site root.\n")
        sys.exit(1)

    pages = find_all_pages()
    if not pages:
        print("  No generated pages found in designers/ or companies/.\n")
        print("  Run generate_page.py first.\n")
        sys.exit(0)

    print(f"  Found {len(pages)} HTML page(s) to process...\n")

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        source = f.read()

    updated   = 0
    skipped   = 0
    not_found = []

    for page_path, folder in sorted(pages.items()):
        name = extract_name_from_html(page_path)
        if not name:
            print(f"  ✗ could not read name from {page_path}")
            not_found.append(page_path)
            continue

        source, changed = update_index(name, page_path, source)
        if changed:
            print(f"  ✓  {name}")
            print(f"       → {page_path}")
            updated += 1
        else:
            skipped += 1

    if updated > 0:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(source)
        print(f"\n  ✓ index.html updated — {updated} link(s) added")
    else:
        print(f"\n  index.html already up to date — nothing to change")

    if skipped:
        print(f"  {skipped} page(s) already had correct links (skipped)")

    if not_found:
        print(f"\n  Could not match {len(not_found)} page(s):")
        for p in not_found:
            print(f"    - {p}")
        print("  Check that the <title> tag follows: <title>Name — ID History</title>")

    print()


if __name__ == "__main__":
    main()
