# ID History Reference Site

A personal study reference for Industrial Design History. A searchable index of designers, companies, and studios — each with their own detail page for notes, images, references, and key works.

Built as a static site that runs entirely in the browser. No frameworks, no build tools, no backend. Just HTML, CSS, JavaScript, and two Python utility scripts.

---

## Folder Structure

```
id-history/
│
├── index.html                  ← The main searchable index of all entries
├── detail.html                 ← Legacy Wikipedia page (can be ignored)
│
├── generate_page.py            ← Generates HTML detail pages from index data
├── gallery_sync.py             ← Generates/updates JSON gallery files from image folders
├── sync_index_links.py         ← Scans generated pages and updates index.html links
│
├── designers/
│   ├── dieter-rams.html        ← Detail page for Dieter Rams
│   ├── dieter-rams.json        ← Gallery image list for Dieter Rams
│   └── ...
│
├── companies/
│   ├── braun.html              ← Detail page for Braun
│   ├── braun.json              ← Gallery image list for Braun
│   └── ...
│
└── images/
    ├── dieter-rams/            ← Image files for Dieter Rams
    │   ├── t3-radio-1958.jpg
    │   └── 606-shelving-1960.jpg
    ├── braun/
    └── ...
```

**Rule of thumb:** every entry gets three things — an HTML file, a JSON file, and an images subfolder. The HTML and JSON live in `designers/` or `companies/`. The images live in `images/[slug]/`.

---

## How It All Fits Together

### The index (`index.html`)
The main page. Contains a JavaScript data array with every designer, company, and studio — their names, dates, tags, and a `page` field that links to their detail page once one has been generated. Supports live search and filtering by type and era.

When you generate a detail page with `generate_page.py`, the script attempts to add the `page` field automatically. However if any links didn't get written correctly, run `sync_index_links.py` — it scans every HTML file in `designers/` and `companies/`, reads the name from the `<title>` tag, and updates `index.html` in one reliable pass. This is the recommended way to fix links after a bulk `--all` generation.

Cards without a `page` field show a subtle "Page not yet built" note and are not clickable.

### Detail pages (`designers/*.html`, `companies/*.html`)
Each entry gets its own HTML file with:
- **Hero** — name, eyebrow, timeline bar, tags
- **About** — a short blurb you write yourself
- **Key Works** (designers) or **Notable Products** (companies) — you fill in
- **Key Designers** (companies only) — auto-populated from collab tags
- **Gallery** — loads from the JSON file; also supports URL paste and drag-and-drop preview
- **My Notes** — a textarea that saves to `localStorage` (persists in your browser)
- **Fast Facts** — sidebar with dates, nationality, collaborators
- **References** — sidebar for books, films, links (you add these)
- **Related Entries** — auto-populated by cross-referencing collab tags

### Gallery JSON (`designers/*.json`, `companies/*.json`)
A simple list of image file paths and captions. The detail page reads this on load and populates the gallery. Example:

```json
{
  "images": [
    {
      "file": "../images/dieter-rams/t3-radio-1958.jpg",
      "caption": "T3 Pocket Radio, Braun, 1958"
    },
    {
      "file": "../images/dieter-rams/606-shelving-1960.jpg",
      "caption": "606 Universal Shelving System, Vitsœ, 1960"
    }
  ]
}
```

Paths are relative from the JSON file's location to the image. The `gallery_sync.py` script writes these paths automatically — you don't need to calculate them by hand.

---

## Running Locally

Because the gallery uses `fetch()` to load JSON files, you **must** use a local server when working on the site. Opening HTML files by double-clicking them will cause the gallery to silently fail.

```bash
# From your site root folder
python3 -m http.server 8000
```

Then open your browser to:

```
http://localhost:8000
```

Keep this running in a terminal tab while you work. Stop it with `Ctrl + C`.

---

## Python Scripts

Both scripts must be run from the **site root folder** (the folder containing `index.html`).

---

### `generate_page.py`

Reads the data array from `index.html` and generates a ready-to-edit HTML detail page for any entry. Also automatically updates `index.html` to add the `page` link so the card becomes clickable.

**What it fills in automatically:**
- Name, dates, type label, eyebrow text
- All tags (era, style, type, collab)
- Timeline bar (calculated from dates)
- Related Entries sidebar (cross-referenced from collab tags)
- Key Designers grid on company pages (from collab tags)
- Gallery, notes, and drag-and-drop — all wired up
- Fast Facts with known fields pre-filled

**What you fill in afterwards:**
- About / blurb text
- Key Works (designers) or Notable Products (companies)
- Fast Facts details (birthplace, training, specific roles)
- References (books, films, links)
- Gallery images (via JSON)

Placeholders are marked with `═══` comment blocks inside the HTML so they're easy to find.

#### Commands

```bash
# Guided mode — shows a numbered list of all entries, pick one
python3 generate_page.py

# Generate one specific entry by name
python3 generate_page.py "Dieter Rams"
python3 generate_page.py "Charles and Ray Eames"
python3 generate_page.py "Tiffany & Co."

# Generate all entries at once
python3 generate_page.py --all

# Generate all entries, but skip any that already have a page
# (safe to run after you've already filled in some pages)
python3 generate_page.py --all --skip-existing
```

**Important:** if you've already filled in a page and run `--all` without `--skip-existing`, it will overwrite your work. Always use `--skip-existing` after you've started editing pages.

---

### `gallery_sync.py`

Scans an image folder and generates or updates the matching JSON file. Only adds new images — never removes or overwrites entries you've already edited.

#### Workflow

1. Add image files to `images/[entry-name]/` — e.g. `images/dieter-rams/t3-radio-1958.jpg`
2. Run `gallery_sync.py`
3. Pick the folder from the list (or pass it as an argument)
4. The script writes the new entries to the JSON, skipping any already listed
5. Open the JSON and edit the captions to be more descriptive if needed

#### Commands

```bash
# Guided mode — shows a list of image folders, pick one
python3 gallery_sync.py

# Pass the folder name directly (faster)
python3 gallery_sync.py dieter-rams
python3 gallery_sync.py braun
python3 gallery_sync.py charles-and-ray-eames
```

The script always confirms before writing. Press `Y` (or just Enter) to confirm, `n` to cancel.

#### Caption editing

The script auto-generates captions from filenames:
`t3-pocket-radio-1958.jpg` → `"T3 Pocket Radio 1958"`

After running the script, open the JSON and make captions more descriptive:
```json
"caption": "T3 Pocket Radio 1958"
→
"caption": "T3 Pocket Radio, Braun, 1958 — Dieter Rams"
```

---

### `sync_index_links.py`

Scans `designers/` and `companies/` for all generated HTML files, reads the entry name from each file's `<title>` tag, and updates `index.html` with the correct `page` field so every card becomes a clickable link.

Run this after `generate_page.py --all` if cards aren't clickable, or any time you add new pages and want to make sure the index is up to date.

#### Commands

```bash
# Scan all generated pages and update index.html
python3 sync_index_links.py
```

The script is safe to run multiple times — it skips any entry that already has the correct link and only writes to `index.html` if something actually changed.

---

### Recommended workflow after `generate_page.py --all`

```bash
# Step 1 — generate all pages
python3 generate_page.py --all --skip-existing

# Step 2 — make sure all cards are linked (fixes any that generate_page missed)
python3 sync_index_links.py
```

Here's the full workflow for adding a new designer or company:

```
1. Add the entry to the data array in index.html
   (name, type, dates, tags — follow the existing format)

2. Run the generator:
   python3 generate_page.py "Entry Name"

3. Run sync to make the card clickable:
   python3 sync_index_links.py

4. Open the generated HTML file and fill in:
   - About blurb
   - Key Works or Notable Products
   - Fast Facts details
   - References

5. Create an images folder:
   images/entry-name/

6. Add image files to that folder

7. Run gallery sync:
   python3 gallery_sync.py entry-name

8. Edit captions in the JSON to be descriptive

9. Preview in your browser at http://localhost:8000

10. Commit and push to GitHub
```

---

## Adding Images to an Existing Page

```
1. Drop image files into images/[entry-name]/

2. Run:
   python3 gallery_sync.py entry-name

3. Edit captions in the JSON if needed

4. Refresh the page in your browser
```

---

## Naming Conventions

File and folder names use **lowercase hyphenated slugs** derived from the entry name:

| Entry name | Slug | Files |
|---|---|---|
| Dieter Rams | `dieter-rams` | `designers/dieter-rams.html`, `designers/dieter-rams.json`, `images/dieter-rams/` |
| Charles and Ray Eames | `charles-and-ray-eames` | `designers/charles-and-ray-eames.html` etc. |
| Tiffany & Co. | `tiffany-co` | `companies/tiffany-co.html` etc. |
| Wiener Werkstätte | `wiener-werkstatte` | `designers/wiener-werkstatte.html` etc. |

**Keep image filenames lowercase and hyphenated too.** GitHub Pages runs on Linux, which is case-sensitive. A file named `T3-Radio.jpg` will work locally on Mac or Windows but break on the live site if the JSON references `t3-radio.jpg`.

---

## Deploying to GitHub Pages

```bash
# First time setup (do this once)
git init
git remote add origin https://github.com/yourusername/id-history.git

# Every time you want to publish changes
git add .
git commit -m "Add Eames page and gallery images"
git push origin main
```

Then in your GitHub repo:
- Go to **Settings → Pages**
- Set source to **Deploy from a branch**
- Set branch to **main**, folder to **/ (root)**
- Save

Your site will be live at `https://yourusername.github.io/id-history/` within about 30 seconds of each push. The gallery and JSON loading work automatically on GitHub Pages since it serves files over HTTP — no local server needed.

---

## Gallery: Local Preview vs Permanent

The gallery has two modes:

| Mode | How | Persists? |
|---|---|---|
| **Permanent** | Add file to `images/` folder + run `gallery_sync.py` | Yes — survives page refresh |
| **URL preview** | Paste a URL into the input box on the detail page | Session only — gone on refresh |
| **Drag-and-drop preview** | Drop an image file onto the drop zone | Session only — gone on refresh |

Use URL paste and drag-and-drop to quickly check how an image looks before committing to downloading and organising it properly.

---

## Notes

Notes typed into the **My Notes** textarea on any detail page are saved to your browser's `localStorage`. This means:

- They persist across page refreshes and browser restarts
- They are saved **per browser** — notes on your laptop won't appear on your phone
- They are not stored in any file in the repo — they live only in the browser
- To back them up, copy the text out and save it somewhere

If you want notes to be part of the repo and visible on any device, copy them into the HTML file itself as a comment or as actual content in the about section.

---

## Tag Reference

Tags in `index.html` use a `kind:value` format:

| Prefix | Purpose | Example |
|---|---|---|
| `era:` | Art movement / historical period | `era:Bauhaus` |
| `style:` | Design style or school | `style:Streamlining` |
| `type:` | Type of work | `type:Furniture` |
| `collab:` | Associated company or studio | `collab:Braun` |

These drive the filter buttons on the index, the tag chips on each card, and the Related Entries cross-referencing on detail pages.
