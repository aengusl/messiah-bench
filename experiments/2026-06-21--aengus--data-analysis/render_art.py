#!/usr/bin/env python3
"""Render top "sacrament" HTML artworks from messiah-bench sims v1..v6 to PNGs.

Usage:
    uv run --with playwright --with pillow python render_art.py            # all sims
    uv run --with playwright --with pillow python render_art.py 3 4 5 6    # subset

Selection:
  - v3..v6: inline `html` per sacrament, ranked by len(edit_log) descending.
  - v1/v2 : `html` is empty; real HTML lives in runs/messiah-vN/sacraments/{filename}.
            No edit_log, so rank by HTML file-size (length) descending.
  Up to 6 per sim.

Adaptive sizing (v3+ artworks often declare an explicit root canvas size):
  - Parse the FIRST declared width:Npx / height:Npx in the html head.
  - Use those as the viewport, CAPPED to [200, 4000] per axis
    (15700 -> 4000 so giant canvases aren't cropped to a corner;
     100  -> 200  so tiny canvases aren't shrunk to a speck).
  - If none found, default 1000x1000.
  - Screenshot full_page=False at that viewport, then downscale the PNG to
    max 600px on the long side (PIL LANCZOS) so files stay small/comparable.

Output:
  plots/art/{version}__{rank}__{safe_religion}.png
  plots/art/_contactsheet_{version}.png
  plots/art/_render_summary.json   (per-file note: real_art|fallback_gradient|flat_fill|blank)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = "/home/aenguslynch/projects/messiah-bench/runs"
OUT_DIR = os.path.join(HERE, "plots", "art")
CHROMIUM = "/usr/bin/chromium"
TOP_N = 6
SIZE_MIN, SIZE_MAX = 200, 4000
DEFAULT_VP = (1000, 1000)
THUMB_MAX = 600
SUMMARY_PATH = os.path.join(OUT_DIR, "_render_summary.json")

os.makedirs(OUT_DIR, exist_ok=True)


def safe_name(s, n=40):
    s = re.sub(r"[^0-9A-Za-z]+", "_", s or "untitled").strip("_")
    return s[:n] or "untitled"


def load_world(v):
    path = os.path.join(RUNS_DIR, f"messiah-v{v}", "world_state.json")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def get_html(v, sac):
    html = sac.get("html") or ""
    if html.strip():
        return html
    fn = sac.get("filename")
    if fn:
        p = os.path.join(RUNS_DIR, f"messiah-v{v}", "sacraments", fn)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                return f.read()
    return ""


def select_top(v, world):
    sac = world.get("sacraments", []) or []
    enriched = []
    for s in sac:
        html = get_html(v, s)
        if not html.strip():
            continue
        el = s.get("edit_log")
        rank_key = len(el) if isinstance(el, list) else len(html)
        enriched.append((rank_key, html, s))
    enriched.sort(key=lambda x: x[0], reverse=True)
    return [(s, html) for (_, html, s) in enriched[:TOP_N]]


def wrap_html(html):
    h = html.lstrip()
    low = h[:9].lower()
    if low.startswith("<html") or low.startswith("<!doctype"):
        return html
    return f'<html><body style="margin:0">{html}</body></html>'


def declared_viewport(html):
    """Parse first declared width:Npx & height:Npx; cap to [200,4000].
    Returns (w, h, raw_w, raw_h) where raw_* are the unclamped declared ints
    (None if not found)."""
    head = html[:4000]
    wm = re.search(r"width\s*:\s*([0-9]+(?:\.[0-9]+)?)px", head)
    hm = re.search(r"height\s*:\s*([0-9]+(?:\.[0-9]+)?)px", head)
    raw_w = int(float(wm.group(1))) if wm else None
    raw_h = int(float(hm.group(1))) if hm else None

    def clamp(x, default):
        if x is None:
            return default
        return max(SIZE_MIN, min(SIZE_MAX, x))

    if raw_w is None and raw_h is None:
        w, h = DEFAULT_VP
    else:
        w = clamp(raw_w, DEFAULT_VP[0])
        h = clamp(raw_h, DEFAULT_VP[1])
    return w, h, raw_w, raw_h


def classify(png_path):
    """Heuristic: real_art | fallback_gradient | flat_fill | blank.
    Uses color variety + brightness. Returns a short note string."""
    try:
        from PIL import Image
        im = Image.open(png_path).convert("RGB")
    except Exception:
        return "blank"
    small = im.resize((64, 64))
    px = list(small.getdata())
    n = len(px)
    # unique-ish colors (quantize to 5-bit/channel)
    q = set(((r >> 3, g >> 3, b >> 3) for (r, g, b) in px))
    ncolors = len(q)
    # std of luminance
    lum = [0.299 * r + 0.587 * g + 0.114 * b for (r, g, b) in px]
    mean = sum(lum) / n
    var = sum((x - mean) ** 2 for x in lum) / n
    std = var ** 0.5

    if ncolors <= 3 and std < 6:
        # essentially one flat color (white/black/dark fill)
        return "blank" if mean > 245 or mean < 8 else "flat_fill"
    if ncolors <= 40 and std < 60:
        # smooth low-color spread -> gradient-ish
        return "fallback_gradient"
    return "real_art"


def render(version_tag, items):
    """Render -> (results, failures). results: list of dicts per file."""
    from playwright.sync_api import sync_playwright

    results, failures = [], []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=CHROMIUM)
        except Exception:
            browser = p.chromium.launch(channel="chromium")
        page = browser.new_page()
        for rank, (sac, html) in enumerate(items, start=1):
            religion = safe_name(sac.get("religion") or sac.get("title") or "unknown")
            base = f"{version_tag}__{rank}__{religion}"
            png = os.path.join(OUT_DIR, base + ".png")
            try:
                w, h, raw_w, raw_h = declared_viewport(html)
                page.set_viewport_size({"width": w, "height": h})
                page.set_content(wrap_html(html), wait_until="load", timeout=20000)
                try:
                    page.wait_for_timeout(450)
                except Exception:
                    pass
                page.screenshot(path=png, full_page=False)
                downscale(png)
                note = classify(png)
                results.append({
                    "file": base + ".png", "rank": rank,
                    "religion": sac.get("religion"),
                    "edit_log_len": len(sac.get("edit_log", []) or []),
                    "declared": [raw_w, raw_h], "viewport": [w, h],
                    "note": note,
                })
            except Exception as e:
                failures.append((base, repr(e)[:200]))
                results.append({
                    "file": base + ".png", "rank": rank,
                    "religion": sac.get("religion"), "note": "blank",
                    "error": repr(e)[:200],
                })
        browser.close()
    return results, failures


def downscale(png_path, max_side=THUMB_MAX):
    try:
        from PIL import Image
        im = Image.open(png_path).convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
            im.save(png_path)
    except Exception:
        pass


def make_contactsheet(version_tag, png_files):
    files = [os.path.join(OUT_DIR, f) for f in png_files
             if os.path.isfile(os.path.join(OUT_DIR, f))]
    if not files:
        return None
    try:
        from PIL import Image
    except Exception:
        return None
    cell, pad = 300, 8
    cols = min(3, len(files))
    rows = (len(files) + cols - 1) // cols
    W = cols * cell + (cols + 1) * pad
    H = rows * cell + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (24, 24, 28))
    for i, pth in enumerate(files):
        try:
            im = Image.open(pth).convert("RGB")
            im.thumbnail((cell, cell))
            r, c = divmod(i, cols)
            x = pad + c * (cell + pad) + (cell - im.width) // 2
            y = pad + r * (cell + pad) + (cell - im.height) // 2
            sheet.paste(im, (x, y))
        except Exception:
            continue
    out = os.path.join(OUT_DIR, f"_contactsheet_{version_tag}.png")
    sheet.save(out)
    return out


def main():
    args = [a for a in sys.argv[1:] if a.isdigit()]
    versions = [int(a) for a in args] if args else list(range(1, 7))

    # preserve prior summary for versions we are not re-rendering
    summary = {}
    if os.path.isfile(SUMMARY_PATH):
        try:
            summary = json.load(open(SUMMARY_PATH))
        except Exception:
            summary = {}

    for v in versions:
        tag = f"v{v}"
        world = load_world(v)
        if world is None:
            print(f"[{tag}] MISSING world_state.json -- skipping")
            summary[tag] = {"selected": 0, "ok": 0, "failed": 0, "items": []}
            continue
        items = select_top(v, world)
        print(f"[{tag}] selected {len(items)} sacraments")
        results, fails = render(tag, items)
        for f in fails:
            print(f"  [{tag}] FAIL {f[0]}: {f[1]}")
        sheet = make_contactsheet(tag, [r["file"] for r in results])
        if sheet:
            print(f"  [{tag}] contact sheet: {os.path.basename(sheet)}")
        ok = len(results) - len(fails)
        summary[tag] = {"selected": len(items), "ok": ok,
                        "failed": len(fails), "items": results}
        for r in results:
            print(f"      {r['file']:50} declared={r.get('declared')} "
                  f"vp={r.get('viewport')} -> {r['note']}")
        print(f"[{tag}] rendered {ok}/{len(items)} OK\n")

    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print("SUMMARY  (note counts per sim)")
    for tag in sorted(summary, key=lambda t: int(t[1:])):
        s = summary[tag]
        notes = {}
        for r in s.get("items", []):
            notes[r["note"]] = notes.get(r["note"], 0) + 1
        print(f"  {tag}: {s.get('ok',0)}/{s.get('selected',0)} ok  notes={notes}")


if __name__ == "__main__":
    main()
