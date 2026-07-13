#!/usr/bin/env python3
"""
generate_page.py
────────────────
Reads the data array from index.html and generates a detail HTML page
for any designer, company, or studio entry.

Usage:
    python3 generate_page.py                  # guided mode — pick from a list
    python3 generate_page.py "Dieter Rams"    # generate one entry by name
    python3 generate_page.py --all            # generate all entries at once
    python3 generate_page.py --all --skip-existing  # skip already-built pages

Place this script in the root of your id-history site folder.
"""

import os
import re
import sys
import json


# ── Config ────────────────────────────────────────────────────────────────────

INDEX_FILE     = "index.html"
DESIGNERS_DIR  = "designers"
COMPANIES_DIR  = "companies"
IMAGES_ROOT    = "images"

# Timeline bar spans this year range
TL_START = 1600
TL_END   = 2030
TL_SPAN  = TL_END - TL_START


# ── Parse index.html data array ───────────────────────────────────────────────

def parse_index_data(path: str) -> list[dict]:
    """
    Extract the JS data array from index.html by reading between
    'const data = [' and the closing '];' that follows it.
    Then parse each object with a regex rather than running JS.
    """
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    # Grab everything between `const data = [` and the matching `];`
    m = re.search(r"const data\s*=\s*\[(.+?)\];\s*\n", source, re.DOTALL)
    if not m:
        print("✗ Could not find 'const data = [...]' in index.html")
        sys.exit(1)

    block = m.group(1)

    entries = []
    # Each entry is a { ... } object — split on object boundaries
    for obj_match in re.finditer(r"\{([^{}]+)\}", block, re.DOTALL):
        obj_text = obj_match.group(1)

        def field(key):
            fm = re.search(rf'{key}\s*:\s*"([^"]*)"', obj_text)
            return fm.group(1) if fm else ""

        def field_list(key):
            fm = re.search(rf'{key}\s*:\s*\[([^\]]*)\]', obj_text)
            if not fm:
                return []
            items = re.findall(r'"([^"]*)"', fm.group(1))
            return items

        name  = field("name")
        etype = field("type")
        dates = field("dates")
        page  = field("page")
        tags  = field_list("tags")

        if name and etype:
            entries.append({
                "name":  name,
                "type":  etype,
                "dates": dates,
                "page":  page,
                "tags":  tags,
            })

    return entries


# ── Data helpers ──────────────────────────────────────────────────────────────

def tags_of_kind(tags: list, kind: str) -> list[str]:
    prefix = kind + ":"
    return [t[len(prefix):] for t in tags if t.startswith(prefix)]


def name_to_slug(name: str) -> str:
    """'Charles and Ray Eames' → 'charles-and-ray-eames'"""
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug


def output_path(entry: dict) -> str:
    slug = name_to_slug(entry["name"])
    folder = DESIGNERS_DIR if entry["type"] in ("designer", "studio") else COMPANIES_DIR
    return os.path.join(folder, f"{slug}.html")


def relative_prefix(entry: dict) -> str:
    """Path prefix from the output file back to site root."""
    return "../"


# ── Timeline bar calculation ──────────────────────────────────────────────────

def timeline_bar(dates: str) -> tuple[float, float, str]:
    """
    Returns (left_pct, width_pct, label) for the career/lifespan bar.
    Tries to extract two years from the dates string.
    Falls back to a single year if only one found.
    """
    years = [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", dates)]
    if len(years) >= 2:
        start, end = years[0], years[-1]
    elif len(years) == 1:
        start = years[0]
        end   = min(start + 40, TL_END - 5)  # assume ~40yr career if only one date
    else:
        return 20.0, 40.0, dates  # fallback

    start = max(start, TL_START)
    end   = min(end,   TL_END)
    left  = round((start - TL_START) / TL_SPAN * 100, 1)
    width = round((end - start)      / TL_SPAN * 100, 1)
    width = max(width, 2.0)  # always visible

    return left, width, dates


# ── Related entries ───────────────────────────────────────────────────────────

def find_related(entry: dict, all_entries: list[dict]) -> list[dict]:
    """
    Find other entries that are either:
    - Named in this entry's collab tags, OR
    - Have this entry's name in their collab tags
    """
    my_collabs = set(tags_of_kind(entry["tags"], "collab"))
    my_name    = entry["name"]
    related    = []
    seen       = set()

    for other in all_entries:
        if other["name"] == my_name:
            continue
        other_collabs = set(tags_of_kind(other["tags"], "collab"))
        if other["name"] in my_collabs or my_name in other_collabs:
            if other["name"] not in seen:
                related.append(other)
                seen.add(other["name"])

    return related[:10]  # cap at 10


# ── HTML shared CSS ───────────────────────────────────────────────────────────

SHARED_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:        #121212;
    --surface:   #1e1e1e;
    --border:    #2a2a2a;
    --text:      #f5f2ee;
    --muted:     #888;
    --faint:     #444;
    --gold:      #c8a96e;
    --gold-dim:  rgba(200,169,110,0.15);
    --tag-era:   rgba(74,95,168,0.25);
    --tag-style: rgba(138,64,32,0.25);
    --tag-type:  rgba(42,106,42,0.25);
    --tag-collab:rgba(106,32,128,0.25);
  }
  html { scroll-behavior: smooth; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; font-size: 15px; line-height: 1.6; min-height: 100vh; }
  a { color: var(--gold); text-decoration: none; }
  a:hover { text-decoration: underline; }

  nav { background: #000; padding: 0.85rem 2.5rem; display: flex; align-items: center; gap: 1.5rem; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
  .nav-back { font-size: 0.8rem; color: var(--muted); letter-spacing: 0.04em; transition: color 0.15s; }
  .nav-back:hover { color: var(--text); text-decoration: none; }
  .nav-back::before { content: "← "; }
  .nav-title { font-size: 0.75rem; color: var(--faint); letter-spacing: 0.08em; text-transform: uppercase; }
  .nav-type-pill { margin-left: auto; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.2rem 0.65rem; border-radius: 20px; border: 1px solid; }
  .nav-type-pill.designer { color: var(--gold); border-color: var(--gold-dim); background: var(--gold-dim); }
  .nav-type-pill.company  { color: #c080e0; border-color: rgba(106,32,128,0.4); background: rgba(106,32,128,0.15); }
  .nav-type-pill.studio   { color: #72b872; border-color: rgba(42,106,42,0.4);  background: rgba(42,106,42,0.15); }

  .hero { padding: 4rem 2.5rem 2.5rem; border-bottom: 1px solid var(--border); }
  .hero-eyebrow { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--gold); margin-bottom: 0.75rem; }
  .hero-name { font-size: clamp(2.8rem, 7vw, 5.5rem); font-weight: 700; line-height: 0.95; letter-spacing: -0.03em; color: var(--text); margin-bottom: 1.5rem; }

  .timeline-bar { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
  .tl-label { font-size: 0.7rem; color: var(--muted); white-space: nowrap; }
  .tl-track { flex: 1; height: 3px; background: var(--border); border-radius: 2px; position: relative; max-width: 480px; }
  .tl-active { position: absolute; top: 0; height: 100%; background: var(--gold); border-radius: 2px; }
  .tl-dates { font-size: 0.72rem; color: var(--muted); font-style: italic; white-space: nowrap; }

  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .tag { font-size: 0.68rem; padding: 0.2rem 0.55rem; border-radius: 12px; border: 1px solid; white-space: nowrap; letter-spacing: 0.02em; }
  .tag.era    { background: var(--tag-era);   border-color: rgba(74,95,168,0.4);  color: #8a9fd8; }
  .tag.style  { background: var(--tag-style); border-color: rgba(138,64,32,0.4);  color: #d4895a; }
  .tag.type   { background: var(--tag-type);  border-color: rgba(42,106,42,0.4);  color: #72b872; }
  .tag.collab { background: var(--tag-collab);border-color: rgba(106,32,128,0.4); color: #c080e0; }

  .content { display: grid; grid-template-columns: 1fr 300px; gap: 0; max-width: 1200px; }
  .main-col { padding: 2.5rem; border-right: 1px solid var(--border); }
  .side-col { padding: 2rem 1.75rem; }

  .section { margin-bottom: 3rem; }
  .section-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--gold); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }
  .section-label::after { content: ""; flex: 1; height: 1px; background: var(--border); }

  .blurb { font-size: 0.95rem; color: #ccc; line-height: 1.75; max-width: 65ch; }
  .blurb p + p { margin-top: 0.85rem; }
  .blurb ul { padding-left: 1.25rem; margin-top: 0.5rem; }
  .blurb ul li { margin-bottom: 0.35rem; color: #bbb; }
  .placeholder { color: var(--faint); font-size: 0.85rem; font-style: italic; border: 1.5px dashed var(--border); border-radius: 8px; padding: 1.25rem; }

  .key-works { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .work-chip { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 0.4rem 0.75rem; font-size: 0.78rem; color: var(--text); line-height: 1.3; }
  .work-chip span { display: block; font-size: 0.65rem; color: var(--muted); margin-top: 0.1rem; }

  .designers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.6rem; }
  .designer-chip { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.6rem 0.75rem; font-size: 0.78rem; color: var(--text); transition: border-color 0.15s; display: block; text-decoration: none; }
  .designer-chip:hover { border-color: var(--gold); text-decoration: none; }
  .designer-chip span { display: block; font-size: 0.65rem; color: var(--muted); margin-top: 0.15rem; }

  .product-list { list-style: none; }
  .product-list li { display: flex; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); font-size: 0.82rem; align-items: baseline; }
  .product-list li:last-child { border-bottom: none; }
  .product-year { color: var(--gold); font-size: 0.72rem; white-space: nowrap; min-width: 40px; }
  .product-name { color: var(--text); }
  .product-designer { color: var(--muted); font-size: 0.72rem; margin-left: auto; white-space: nowrap; }

  .gallery-controls { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
  .url-input-row { display: flex; gap: 0.5rem; flex: 1; min-width: 260px; }
  .url-input-row input { flex: 1; background: var(--surface); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.82rem; padding: 0.45rem 0.75rem; outline: none; transition: border-color 0.15s; }
  .url-input-row input:focus { border-color: var(--gold); }
  .url-input-row input::placeholder { color: var(--faint); }
  .btn { background: var(--gold-dim); border: 1px solid var(--gold); color: var(--gold); border-radius: 6px; padding: 0.45rem 0.9rem; font-size: 0.78rem; cursor: pointer; white-space: nowrap; transition: background 0.15s; }
  .btn:hover { background: rgba(200,169,110,0.25); }

  .drop-zone { border: 1.5px dashed var(--faint); border-radius: 8px; padding: 1.25rem; text-align: center; font-size: 0.78rem; color: var(--muted); cursor: pointer; transition: border-color 0.15s, background 0.15s; margin-bottom: 1.25rem; }
  .drop-zone.drag-over { border-color: var(--gold); background: var(--gold-dim); color: var(--gold); }
  .drop-zone input[type="file"] { display: none; }

  .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; }
  .gallery-item { position: relative; border-radius: 8px; overflow: hidden; background: var(--surface); border: 1px solid var(--border); }
  .gallery-item img { width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; transition: opacity 0.2s; }
  .gallery-item:hover img { opacity: 0.85; }
  .gallery-item-caption { padding: 0.45rem 0.6rem; font-size: 0.68rem; color: var(--muted); line-height: 1.4; }
  .gallery-item-remove { position: absolute; top: 0.4rem; right: 0.4rem; background: rgba(0,0,0,0.6); color: #fff; border: none; border-radius: 50%; width: 22px; height: 22px; font-size: 0.7rem; cursor: pointer; display: none; align-items: center; justify-content: center; }
  .gallery-item:hover .gallery-item-remove { display: flex; }
  .gallery-empty { grid-column: 1/-1; text-align: center; padding: 2.5rem; color: var(--faint); font-size: 0.82rem; border: 1.5px dashed var(--border); border-radius: 8px; }

  .notes-area { width: 100%; min-height: 180px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 0.88rem; font-family: inherit; line-height: 1.7; padding: 1rem 1.1rem; resize: vertical; outline: none; transition: border-color 0.15s; }
  .notes-area:focus { border-color: var(--gold); }
  .notes-area::placeholder { color: var(--faint); }
  .notes-save-row { display: flex; align-items: center; gap: 0.75rem; margin-top: 0.6rem; }
  .notes-saved { font-size: 0.72rem; color: var(--muted); opacity: 0; transition: opacity 0.3s; }
  .notes-saved.show { opacity: 1; }

  .side-section { margin-bottom: 2rem; }
  .side-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }

  .fact-list { list-style: none; }
  .fact-list li { display: flex; justify-content: space-between; align-items: baseline; gap: 0.75rem; padding: 0.45rem 0; border-bottom: 1px solid var(--border); font-size: 0.8rem; }
  .fact-list li:last-child { border-bottom: none; }
  .fact-key { color: var(--muted); flex-shrink: 0; }
  .fact-val { color: var(--text); text-align: right; }

  .ref-list { list-style: none; }
  .ref-list li { padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.78rem; line-height: 1.4; }
  .ref-list li:last-child { border-bottom: none; }
  .ref-list a { color: var(--gold); }
  .ref-type { display: inline-block; font-size: 0.6rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); background: var(--border); padding: 0.1rem 0.4rem; border-radius: 3px; margin-right: 0.3rem; vertical-align: middle; }

  .related-list { list-style: none; }
  .related-list li { padding: 0.3rem 0; }
  .related-list a { font-size: 0.8rem; color: var(--muted); display: flex; align-items: center; gap: 0.4rem; transition: color 0.15s; }
  .related-list a:hover { color: var(--gold); text-decoration: none; }
  .related-list a::before { content: "→"; font-size: 0.7rem; }

  footer { border-top: 1px solid var(--border); padding: 1.5rem 2.5rem; font-size: 0.72rem; color: var(--faint); display: flex; gap: 1rem; justify-content: space-between; }

  @media (max-width: 768px) {
    .content { grid-template-columns: 1fr; }
    .main-col { border-right: none; border-bottom: 1px solid var(--border); padding: 1.5rem 1rem; }
    .side-col { padding: 1.5rem 1rem; }
    .hero { padding: 2.5rem 1rem 1.75rem; }
    nav { padding: 0.85rem 1rem; }
    footer { padding: 1rem; flex-direction: column; }
  }
"""

SHARED_JS = """
async function loadGallery(pageKey, folder) {
  try {
    const res = await fetch(`../${folder}/${pageKey}.json`);
    if (!res.ok) return;
    const json = await res.json();
    if (json.images && json.images.length > 0) {
      json.images.forEach(img => addImageToGrid(img.file, img.caption || ""));
    }
  } catch(e) {}
}

function addImageToGrid(src, caption) {
  const empty = document.getElementById("gallery-empty");
  if (empty) empty.remove();
  const grid = document.getElementById("gallery-grid");
  const item = document.createElement("div");
  item.className = "gallery-item";
  item.innerHTML = `
    <a href="${src}" target="_blank" rel="noopener">
      <img src="${src}" alt="${caption}" loading="lazy" onerror="this.closest('.gallery-item').style.display='none'">
    </a>
    <div class="gallery-item-caption">${caption}</div>
    <button class="gallery-item-remove" onclick="this.closest('.gallery-item').remove()" title="Remove (preview only)">✕</button>
  `;
  grid.appendChild(item);
}

function addFromUrl() {
  const input = document.getElementById("url-input");
  const url = input.value.trim();
  if (!url) return;
  const caption = url.split("/").pop().replace(/\\.[^.]+$/, "").replace(/[-_]/g, " ");
  addImageToGrid(url, caption + " (URL preview)");
  input.value = "";
}
document.getElementById("url-input").addEventListener("keydown", e => { if (e.key === "Enter") addFromUrl(); });

const dropZone = document.getElementById("drop-zone");
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  handleFiles(e.dataTransfer.files);
});
function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = e => addImageToGrid(e.target.result, file.name.replace(/\\.[^.]+$/, "") + " (local preview)");
    reader.readAsDataURL(file);
  });
}
document.getElementById("file-input").addEventListener("change", function() { handleFiles(this.files); });

function saveNotes(key) {
  localStorage.setItem(`notes::${key}`, document.getElementById("notes-area").value);
  const indicator = document.getElementById("notes-saved");
  indicator.classList.add("show");
  setTimeout(() => indicator.classList.remove("show"), 2000);
}
function loadNotes(key) {
  const saved = localStorage.getItem(`notes::${key}`);
  if (saved) document.getElementById("notes-area").value = saved;
}
"""


# ── HTML builders ─────────────────────────────────────────────────────────────

def build_tags_html(tags: list[str]) -> str:
    parts = []
    for kind, css_class in [("era","era"),("style","style"),("type","type"),("collab","collab")]:
        for val in tags_of_kind(tags, kind):
            prefix = "↔ " if kind == "collab" else ""
            parts.append(f'<span class="tag {css_class}">{prefix}{val}</span>')
    return "\n        ".join(parts)


def build_related_html(related: list[dict], entry: dict) -> str:
    if not related:
        return "<li><span style='color:var(--faint);font-size:0.8rem'>None identified yet</span></li>"
    lines = []
    for r in related:
        slug = name_to_slug(r["name"])
        folder = DESIGNERS_DIR if r["type"] in ("designer","studio") else COMPANIES_DIR
        # Relative path from current file's folder back to sibling folder
        current_folder = DESIGNERS_DIR if entry["type"] in ("designer","studio") else COMPANIES_DIR
        if folder == current_folder:
            href = f"{slug}.html"
        else:
            href = f"../{folder}/{slug}.html"
        lines.append(f'<li><a href="{href}">{r["name"]}</a></li>')
    return "\n        ".join(lines)


def build_collab_chips_html(entry: dict, all_entries: list[dict]) -> str:
    """For company pages: build the Key Designers grid from collab tags."""
    collab_names = tags_of_kind(entry["tags"], "collab")
    name_to_entry = {e["name"]: e for e in all_entries}
    chips = []
    for cname in collab_names:
        matched = name_to_entry.get(cname)
        if matched and matched["type"] in ("designer", "studio"):
            slug = name_to_slug(matched["name"])
            current_folder = COMPANIES_DIR
            href = f"../{DESIGNERS_DIR}/{slug}.html"
            chips.append(f'''        <a class="designer-chip" href="{href}">
          {matched["name"]}
          <span><!-- role/contribution --></span>
        </a>''')
    if not chips:
        return '        <p class="placeholder">Add key designers manually.</p>'
    return "\n".join(chips)


def build_fact_list(entry: dict) -> str:
    """Build auto-populated fast facts rows."""
    eras   = tags_of_kind(entry["tags"], "era")
    collabs = tags_of_kind(entry["tags"], "collab")
    rows = []

    if entry["dates"]:
        rows.append(("Dates", entry["dates"]))

    if entry["type"] == "designer":
        rows.append(("Nationality", "<!-- e.g. German -->"))
        rows.append(("Training",    "<!-- e.g. Wiesbaden School of Art -->"))
    elif entry["type"] in ("company", "studio"):
        rows.append(("Founded",  entry["dates"] or "<!-- year -->"))
        rows.append(("Founder",  "<!-- name -->"))
        rows.append(("HQ",       "<!-- city, country -->"))

    if eras:
        rows.append(("Era", eras[0]))
    if collabs:
        rows.append(("Key collaborators", ", ".join(collabs[:3])))

    rows.append(("Week covered", "<!-- Week N — Topic -->"))

    return "\n        ".join(
        f'<li><span class="fact-key">{k}</span><span class="fact-val">{v}</span></li>'
        for k, v in rows
    )


def build_eyebrow(entry: dict) -> str:
    parts = []
    types  = tags_of_kind(entry["tags"], "type")
    styles = tags_of_kind(entry["tags"], "style")
    if types:
        parts.append(types[0])
    if styles:
        parts.append(styles[0])
    if entry["dates"]:
        parts.append(entry["dates"])
    return " · ".join(parts)


# ── Page builders ─────────────────────────────────────────────────────────────

def build_designer_page(entry: dict, all_entries: list[dict]) -> str:
    slug       = name_to_slug(entry["name"])
    prefix     = relative_prefix(entry)
    left, width, tl_label = timeline_bar(entry["dates"])
    folder     = DESIGNERS_DIR if entry["type"] in ("designer","studio") else COMPANIES_DIR
    type_label = "Designer" if entry["type"] == "designer" else "Studio / Organization"
    type_class = entry["type"] if entry["type"] in ("designer","company","studio") else "designer"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{entry["name"]} — ID History</title>
<style>{SHARED_CSS}
</style>
</head>
<body>

<nav>
  <a class="nav-back" href="{prefix}index.html">Index</a>
  <span class="nav-title">ID History Reference</span>
  <span class="nav-type-pill {type_class}">{type_label}</span>
</nav>

<div class="hero">
  <div class="hero-eyebrow">{build_eyebrow(entry)}</div>
  <h1 class="hero-name">{entry["name"]}</h1>

  <div class="timeline-bar">
    <span class="tl-label">{TL_START}</span>
    <div class="tl-track">
      <div class="tl-active" style="left:{left}%;width:{width}%;"></div>
    </div>
    <span class="tl-label">{TL_END}</span>
    <span class="tl-dates">{tl_label}</span>
  </div>

  <div class="tags">
    {build_tags_html(entry["tags"])}
  </div>
</div>

<div class="content">
  <div class="main-col">

    <div class="section">
      <div class="section-label">About</div>
      <div class="blurb">
        <!-- ═══════════════════════════════════════════════
             ADD ABOUT TEXT HERE
             Use <p> tags for paragraphs, <ul>/<li> for lists
             ═══════════════════════════════════════════════ -->
        <p class="placeholder">About text not yet added. Write a short blurb about {entry["name"]} here.</p>
      </div>
    </div>

    <div class="section">
      <div class="section-label">Key Works</div>
      <div class="key-works">
        <!-- ═══════════════════════════════════════════════
             ADD KEY WORKS HERE — copy and repeat the chip below
             <div class="work-chip">Work Title<span>Company · Year</span></div>
             ═══════════════════════════════════════════════ -->
        <div class="work-chip placeholder">Key works not yet added<span>Add work-chip divs here</span></div>
      </div>
    </div>

    <div class="section">
      <div class="section-label">Gallery</div>
      <div class="gallery-controls">
        <div class="url-input-row">
          <input type="text" id="url-input" placeholder="Paste an image URL and press Add…">
          <button class="btn" onclick="addFromUrl()">Add</button>
        </div>
      </div>
      <div class="drop-zone" id="drop-zone">
        <input type="file" id="file-input" accept="image/*" multiple>
        ↓ Drop images here or click to browse — preview only (add to <code>images/{slug}/</code> + JSON to save)
      </div>
      <div class="gallery-grid" id="gallery-grid">
        <div class="gallery-empty" id="gallery-empty">
          No images yet. Add files to <code>images/{slug}/</code> and list them in <code>{slug}.json</code>, or paste a URL above.
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-label">My Notes</div>
      <textarea class="notes-area" id="notes-area" placeholder="Write your own study notes, observations, or lecture notes here…"></textarea>
      <div class="notes-save-row">
        <button class="btn" onclick="saveNotes('{slug}')">Save notes</button>
        <span class="notes-saved" id="notes-saved">Saved ✓</span>
        <span style="font-size:0.7rem;color:var(--faint);margin-left:auto">Saved to browser localStorage</span>
      </div>
    </div>

  </div>

  <div class="side-col">

    <div class="side-section">
      <div class="side-label">Fast Facts</div>
      <ul class="fact-list">
        {build_fact_list(entry)}
      </ul>
    </div>

    <div class="side-section">
      <div class="side-label">References</div>
      <ul class="ref-list">
        <!-- ═══════════════════════════════════════════════
             ADD REFERENCES HERE — copy and repeat the li below
             <li><span class="ref-type">Book</span><a href="URL">Title — Author</a></li>
             ref-type options: Book · Film · Web · Article · Exhibition
             ═══════════════════════════════════════════════ -->
        <li><span style="color:var(--faint);font-size:0.78rem">No references added yet.</span></li>
      </ul>
    </div>

    <div class="side-section">
      <div class="side-label">Related Entries</div>
      <ul class="related-list">
        {build_related_html(find_related(entry, all_entries), entry)}
      </ul>
    </div>

  </div>
</div>

<footer>
  <span>ID History Reference · Matthew Bird</span>
  <a href="{prefix}index.html">← Back to index</a>
</footer>

<script>
{SHARED_JS}
loadGallery("{slug}", "{folder}");
loadNotes("{slug}");
</script>
</body>
</html>"""


def build_company_page(entry: dict, all_entries: list[dict]) -> str:
    slug       = name_to_slug(entry["name"])
    prefix     = relative_prefix(entry)
    left, width, tl_label = timeline_bar(entry["dates"])
    folder     = COMPANIES_DIR
    type_label = "Company" if entry["type"] == "company" else "Studio / Organization"
    type_class = "company"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{entry["name"]} — ID History</title>
<style>{SHARED_CSS}
</style>
</head>
<body>

<nav>
  <a class="nav-back" href="{prefix}index.html">Index</a>
  <span class="nav-title">ID History Reference</span>
  <span class="nav-type-pill {type_class}">{type_label}</span>
</nav>

<div class="hero">
  <div class="hero-eyebrow">{build_eyebrow(entry)}</div>
  <h1 class="hero-name">{entry["name"]}</h1>

  <div class="timeline-bar">
    <span class="tl-label">{TL_START}</span>
    <div class="tl-track">
      <div class="tl-active" style="left:{left}%;width:{width}%;"></div>
    </div>
    <span class="tl-label">{TL_END}</span>
    <span class="tl-dates">{tl_label}</span>
  </div>

  <div class="tags">
    {build_tags_html(entry["tags"])}
  </div>
</div>

<div class="content">
  <div class="main-col">

    <div class="section">
      <div class="section-label">About</div>
      <div class="blurb">
        <!-- ═══════════════════════════════════════════════
             ADD ABOUT TEXT HERE
             Use <p> tags for paragraphs, <ul>/<li> for lists
             ═══════════════════════════════════════════════ -->
        <p class="placeholder">About text not yet added. Write a short blurb about {entry["name"]} here.</p>
      </div>
    </div>

    <div class="section">
      <div class="section-label">Key Designers</div>
      <div class="designers-grid">
        {build_collab_chips_html(entry, all_entries)}
      </div>
    </div>

    <div class="section">
      <div class="section-label">Notable Products</div>
      <ul class="product-list">
        <!-- ═══════════════════════════════════════════════
             ADD NOTABLE PRODUCTS HERE — copy and repeat the li below
             <li>
               <span class="product-year">1958</span>
               <span class="product-name">Product Name</span>
               <span class="product-designer">Designer Name</span>
             </li>
             ═══════════════════════════════════════════════ -->
        <li>
          <span class="product-year">—</span>
          <span class="product-name" style="color:var(--faint)">Notable products not yet added</span>
        </li>
      </ul>
    </div>

    <div class="section">
      <div class="section-label">Gallery</div>
      <div class="gallery-controls">
        <div class="url-input-row">
          <input type="text" id="url-input" placeholder="Paste an image URL and press Add…">
          <button class="btn" onclick="addFromUrl()">Add</button>
        </div>
      </div>
      <div class="drop-zone" id="drop-zone">
        <input type="file" id="file-input" accept="image/*" multiple>
        ↓ Drop images here or click to browse — preview only (add to <code>images/{slug}/</code> + JSON to save)
      </div>
      <div class="gallery-grid" id="gallery-grid">
        <div class="gallery-empty" id="gallery-empty">
          No images yet. Add files to <code>images/{slug}/</code> and list them in <code>{slug}.json</code>, or paste a URL above.
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-label">My Notes</div>
      <textarea class="notes-area" id="notes-area" placeholder="Write your own study notes, observations, or lecture notes here…"></textarea>
      <div class="notes-save-row">
        <button class="btn" onclick="saveNotes('{slug}')">Save notes</button>
        <span class="notes-saved" id="notes-saved">Saved ✓</span>
        <span style="font-size:0.7rem;color:var(--faint);margin-left:auto">Saved to browser localStorage</span>
      </div>
    </div>

  </div>

  <div class="side-col">

    <div class="side-section">
      <div class="side-label">Fast Facts</div>
      <ul class="fact-list">
        {build_fact_list(entry)}
      </ul>
    </div>

    <div class="side-section">
      <div class="side-label">References</div>
      <ul class="ref-list">
        <!-- ═══════════════════════════════════════════════
             ADD REFERENCES HERE — copy and repeat the li below
             <li><span class="ref-type">Book</span><a href="URL">Title — Author</a></li>
             ref-type options: Book · Film · Web · Article · Exhibition
             ═══════════════════════════════════════════════ -->
        <li><span style="color:var(--faint);font-size:0.78rem">No references added yet.</span></li>
      </ul>
    </div>

    <div class="side-section">
      <div class="side-label">Related Entries</div>
      <ul class="related-list">
        {build_related_html(find_related(entry, all_entries), entry)}
      </ul>
    </div>

  </div>
</div>

<footer>
  <span>ID History Reference · Matthew Bird</span>
  <a href="{prefix}index.html">← Back to index</a>
</footer>

<script>
{SHARED_JS}
loadGallery("{slug}", "{folder}");
loadNotes("{slug}");
</script>
</body>
</html>"""


# ── Generate one entry ────────────────────────────────────────────────────────

def generate(entry: dict, all_entries: list[dict], skip_existing: bool = False) -> str:
    path = output_path(entry)
    if skip_existing and os.path.exists(path):
        return f"  skipped  {path} (already exists)"

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if entry["type"] in ("designer", "studio"):
        html = build_designer_page(entry, all_entries)
    else:
        html = build_company_page(entry, all_entries)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return f"  written  {path}"


# ── Also update index.html to add page field ──────────────────────────────────

def update_index_page_field(entry: dict):
    """
    After generating a page, add the page: "..." field to the matching
    entry in index.html so the card becomes a live link.
    """
    path = output_path(entry)
    # Normalise to forward slashes
    page_val = path.replace("\\", "/")

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        source = f.read()

    # Find the entry by name and check if it already has a page field
    # Match the object containing this exact name
    name_escaped = re.escape(entry["name"])
    pattern = rf'(\{{[^{{}}]*?"name"\s*:\s*"{name_escaped}"[^{{}}]*?)(,?\s*"page"\s*:\s*"[^"]*")?([^{{}}]*?\}})'

    def replacer(m):
        before = m.group(1)
        rest   = m.group(3)
        # Insert page field right after name field
        name_pattern = rf'"name"\s*:\s*"{name_escaped}"'
        return re.sub(
            name_pattern,
            f'"name": "{entry["name"]}", "page": "{page_val}"',
            before
        ) + rest

    new_source = re.sub(pattern, replacer, source, count=1, flags=re.DOTALL)

    if new_source != source:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(new_source)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  ID History — Page Generator")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if not os.path.exists(INDEX_FILE):
        print(f"✗ {INDEX_FILE} not found. Run this from your site root.\n")
        sys.exit(1)

    all_entries = parse_index_data(INDEX_FILE)
    print(f"  Loaded {len(all_entries)} entries from index.html\n")

    skip_existing = "--skip-existing" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # ── Generate all ──
    if "--all" in sys.argv:
        print(f"  Generating all {len(all_entries)} pages...\n")
        for entry in all_entries:
            result = generate(entry, all_entries, skip_existing)
            print(result)
            if "written" in result:
                update_index_page_field(entry)
        print(f"\n  ✓ Done. index.html updated with page links.\n")
        return

    # ── Generate by name (passed as argument) ──
    if args:
        name = " ".join(args)
        matches = [e for e in all_entries if e["name"].lower() == name.lower()]
        if not matches:
            # fuzzy fallback
            matches = [e for e in all_entries if name.lower() in e["name"].lower()]
        if not matches:
            print(f"  ✗ No entry found matching '{name}'\n")
            sys.exit(1)
        if len(matches) > 1:
            print(f"  Multiple matches for '{name}':")
            for i, m in enumerate(matches, 1):
                print(f"    [{i}] {m['name']}")
            choice = input("\n  Enter a number: ").strip()
            entry = matches[int(choice) - 1]
        else:
            entry = matches[0]
        result = generate(entry, all_entries, skip_existing)
        print(result)
        if "written" in result:
            update_index_page_field(entry)
            print(f"  ✓ index.html updated with page link.\n")
        return

    # ── Guided mode ──
    print("  Choose an entry to generate:\n")
    for i, e in enumerate(all_entries, 1):
        built = " ✓" if os.path.exists(output_path(e)) else ""
        print(f"  [{i:>3}] {e['name']:<45} {e['type']:<10}{built}")

    print()
    raw = input("  Enter a number, a name, or 'all': ").strip()

    if raw.lower() == "all":
        for entry in all_entries:
            result = generate(entry, all_entries, skip_existing)
            print(result)
            if "written" in result:
                update_index_page_field(entry)
        print(f"\n  ✓ Done. index.html updated with page links.\n")
        return

    if raw.isdigit():
        entry = all_entries[int(raw) - 1]
    else:
        matches = [e for e in all_entries if raw.lower() in e["name"].lower()]
        if not matches:
            print(f"\n  ✗ No match for '{raw}'\n")
            sys.exit(1)
        entry = matches[0]

    result = generate(entry, all_entries, skip_existing)
    print(f"\n{result}")
    if "written" in result:
        update_index_page_field(entry)
        print(f"  ✓ index.html updated with page link.\n")


if __name__ == "__main__":
    main()
