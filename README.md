# ID Culture Reference Site

A personal study reference for Industrial Design History. A searchable index of 228 designers, companies, and studios — each with their own detail page covering biography, key works, fast facts, references, gallery, and personal notes.

Built as a static site hosted on GitHub Pages. No frameworks, no build tools, no backend. Just HTML, CSS, JavaScript, and a few Python utility scripts.

**Live site:** `https://YOURUSERNAME.github.io/id-culture/`

---

## Folder Structure

```
id-culture/
│
├── index.html                  ← Searchable index of all 228 entries
├── generate_page.py            ← Generates HTML detail pages from index data
├── gallery_sync.py             ← Generates/updates JSON gallery files from image folders
├── sync_index_links.py         ← Scans generated pages and updates index.html links
├── create_image_folders.py     ← Creates images/ subfolder for every entry
├── optimize_images.py          ← Resizes and compresses images before committing
├── nextcloud_gallery_sync.py   ← Syncs gallery JSONs from a Nextcloud share (optional)
│
├── designers/
│   ├── dieter-rams.html        ← Detail page
│   ├── dieter-rams.json        ← Gallery image list
│   └── ...
│
├── companies/
│   ├── braun.html
│   ├── braun.json
│   └── ...
│
└── images/
    ├── dieter-rams/            ← Image files for Dieter Rams
    │   └── sk4-phonosuper-1956.jpg
    └── ...
```

Every entry gets three things: an HTML file, a JSON file, and an images subfolder. The HTML and JSON live in `designers/` or `companies/`. The images live in `images/[slug]/`.

---

## How It All Fits Together

### The index (`index.html`)
The main page. Contains a JavaScript data array with every entry — names, dates, tags, and a `page` field that links to the detail page. Supports live search and tag filtering.

### Detail pages
Each entry has its own HTML page with:
- **Hero** — name, timeline bar, tags
- **About** — blurb
- **Key Works / Notable Products** — chips or product list
- **Gallery** — loads from the JSON file; also supports URL paste and drag-and-drop preview
- **My Notes** — saves to `localStorage` (browser only, not synced)
- **Fast Facts** — sidebar
- **References** — sidebar with books, links, films
- **Related Entries** — auto-populated from collab tags

### Gallery JSON
A simple list of image paths and captions that the detail page fetches on load:

```json
{
  "images": [
    {
      "file": "../images/dieter-rams/sk4-phonosuper-1956.jpg",
      "caption": "SK4 Phonosuper, Braun, 1956"
    }
  ]
}
```

Paths are relative from the JSON file's location. `gallery_sync.py` writes these automatically.

---

## Running Locally

The gallery uses `fetch()` to load JSON files, so you must use a local server — opening HTML files directly will cause the gallery to silently fail.

```bash
# From the site root folder
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser. Stop with `Ctrl+C`.

---

## Python Scripts

All scripts must be run from the **site root** (the folder containing `index.html`).

---

### `generate_page.py`
Generates a detail HTML page for any entry, using the data already in `index.html`.

Auto-fills: name, dates, type, tags, timeline bar, related entries, key designers grid.
You fill in afterwards: about blurb, key works, fast facts detail, references.

```bash
# Interactive — pick from a numbered list
python generate_page.py

# Generate one specific entry
python generate_page.py "Dieter Rams"

# Generate all entries
python generate_page.py --all

# Generate all, skip entries that already have a page (safe after editing)
python generate_page.py --all --skip-existing
```

⚠️ Running `--all` without `--skip-existing` will overwrite pages you've already edited.

---

### `gallery_sync.py`
Scans an `images/[slug]/` folder and writes the matching JSON file. Only adds new images — never removes or duplicates existing entries.

```bash
# Interactive — pick from a list of image folders
python gallery_sync.py

# Sync a specific entry
python gallery_sync.py dieter-rams
python gallery_sync.py braun
```

After running, open the JSON and make captions more descriptive if needed:
```json
"caption": "Sk4 Phonosuper 1956"
→
"caption": "SK4 Phonosuper, Braun, 1956 — with Hans Gugelot"
```

---

### `sync_index_links.py`
Scans all HTML files in `designers/` and `companies/`, reads entry names from their `<title>` tags, and updates `index.html` so every card is a clickable link. Run this if any cards show "Page not yet built" after generating pages.

```bash
python sync_index_links.py
```

---

### `create_image_folders.py`
Creates an empty `images/[slug]/` folder for every entry in `index.html`. Safe to re-run — only creates folders that don't already exist.

```bash
python create_image_folders.py
```

---

### `optimize_images.py`
Resizes and compresses all images in the `images/` folder in place. Caps width at 1200px and compresses JPEGs to quality 82. Run this before `gallery_sync.py` whenever you add new images.

```bash
# Optimize one entry
python optimize_images.py dieter-rams

# Optimize everything
python optimize_images.py
```

Requires Pillow:
```bash
pip install Pillow
```

You can adjust `MAX_WIDTH` and `JPEG_QUALITY` at the top of the script.

---

### `nextcloud_gallery_sync.py` (optional)
Syncs gallery JSONs from a Nextcloud public share instead of local image folders. Only useful if hosting images on Nextcloud. Edit the three config values at the top of the script before running.

```bash
pip install requests
python nextcloud_gallery_sync.py
```

Note: Nextcloud serves files as downloads rather than inline images, which causes issues with `<img>` tags. Committing images directly to the repo (see below) is simpler and more reliable.

---

## Adding Images to an Entry

```bash
# 1. Drop image files into the right folder
#    images/dieter-rams/braun-phase-1-1971.jpg

# 2. Optimize — resizes to 1200px wide and compresses in place
python optimize_images.py dieter-rams

# 3. Sync to JSON
python gallery_sync.py dieter-rams

# 4. Edit captions in the JSON if needed

# 5. Commit and push
git add .
git commit -m "add Dieter Rams images"
git push
```

Then hard refresh the live site (**Ctrl+Shift+R**) to bypass browser cache.

To optimize every folder at once:
```bash
python optimize_images.py
```

### Image naming
Keep filenames **lowercase and hyphenated**: `braun-phase-1-1971.jpg` not `Braun Phase 1 1971.jpg`. GitHub Pages runs on Linux which is case-sensitive — mismatched case works locally but breaks on the live site.

### Image size
`optimize_images.py` handles resizing automatically — it caps images at 1200px wide and compresses JPEGs to quality 82. You can adjust both values at the top of the script. This keeps the repo well under GitHub's 1GB soft limit even with many images per entry.

---

## Adding a New Entry

```bash
# 1. Add the entry to the data array in index.html
#    (name, type, dates, tags — follow existing format)

# 2. Generate the detail page
python generate_page.py "Entry Name"

# 3. Update index links
python sync_index_links.py

# 4. Fill in the HTML — about blurb, key works, fast facts, references

# 5. Create the image folder
mkdir images/entry-slug

# 6. Add images, run gallery sync
python gallery_sync.py entry-slug

# 7. Commit and push
git add .
git commit -m "Add Entry Name page"
git push
```

---

## Naming Conventions

Entry names are converted to lowercase hyphenated slugs:

| Entry name | Slug |
|---|---|
| Dieter Rams | `dieter-rams` |
| Charles and Ray Eames | `charles-and-ray-eames` |
| Tiffany & Co. | `tiffany-co` |
| Wiener Werkstätte | `wiener-werkstatte` |
| HfG Ulm | `hochschule-fur-gestaltung-ulm-hfg-ulm` |

The slug is used for the HTML file, JSON file, and images subfolder — all three must match exactly.

---

## Deploying to GitHub Pages

### First time setup (already done)
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create id-culture --public --push --source=.
gh api repos/YOURUSERNAME/id-culture/pages --method POST --field source[branch]=main --field source[path]=/
```

### Every subsequent update
```bash
git add .
git commit -m "describe what changed"
git push
```

The live site updates within 30–60 seconds of each push. Always **Ctrl+Shift+R** after checking the live site to make sure you're not seeing a cached version.

**Live URL:** `https://YOURUSERNAME.github.io/id-culture/`

---

## Gallery Modes

| Mode | How | Persists after refresh? |
|---|---|---|
| **Permanent** | Add file to `images/` + run `gallery_sync.py` + push | Yes |
| **URL preview** | Paste a URL into the input box on the detail page | No |
| **Drag-and-drop preview** | Drop an image onto the drop zone | No |

Use URL paste and drag-and-drop to check how an image looks before committing it to the repo.

---

## Notes

Notes typed into the **My Notes** textarea on any detail page save to your browser's `localStorage`. This means:

- They persist across refreshes and browser restarts on the same device
- They are **not** synced across devices — notes on your laptop won't appear on your phone
- They are not stored in the repo

To back up notes or access them on another device, copy the text out of the textarea and save it elsewhere.

---

## Tag Reference

Tags use a `kind:value` format in `index.html`:

| Prefix | Purpose | Example |
|---|---|---|
| `era:` | Historical period / movement | `era:Bauhaus` |
| `style:` | Design style or school | `style:Streamlining` |
| `type:` | Type of work | `type:Furniture` |
| `collab:` | Associated company or studio | `collab:Braun` |

These drive the filter buttons on the index, the tag chips on each card, and the Related Entries cross-referencing on detail pages.


missing designers:
olof backstrom and fiskamin
vignelli
colombini