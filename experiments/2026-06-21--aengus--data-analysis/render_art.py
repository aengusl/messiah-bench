#!/usr/bin/env python3
"""Render top "sacrament" HTML artworks from messiah-bench sims v1..v6 to PNGs.

Usage:
    uv run --with playwright --with pillow python render_art.py

Selection:
  - v3..v6: inline `html` per sacrament, ranked by len(edit_log) descending.
  - v1/v2 : `html` is empty; real HTML lives in runs/messiah-vN/sacraments/{filename}.
            No edit_log, so rank by HTML file-size (length) descending.
  Up to 6 per sim.

Output:
  plots/art/{version}__{rank}__{safe_religion}.png  (fixed 800x800 viewport)
  plots/art/_contactsheet_{version}.png             (grid montage, optional)
"""
import json
import os
import re
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = "/home/aenguslynch/projects/messiah-bench/runs"
OUT_DIR = os.path.join(HERE, "plots", "art")
CHROMIUM = "/usr/bin/chromium"
VIEWPORT = {"width": 800, "height": 800}
TOP_N = 6

os.makedirs(OUT_DIR, exist_ok=True)


def safe_name(s, n=40):
    s = re.sub(r"[^0-9A-Za-z]+", "_", s or "untitled").strip("_")
    return (s[:n] or "untitled")


def load_world(v):
    path = os.path.join(RUNS_DIR, f"messiah-v{v}", "world_state.json")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def get_html(v, sac):
    """Return HTML string for a sacrament (inline, else from sacraments/ dir)."""
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
    """Return list of (sac_dict, html_str) for top TOP_N, ranked."""
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
    if h[:5].lower().startswith("<html") or h[:9].lower().startswith("<!doctype"):
        return html
    return f'<html><body style="margin:0">{html}</body></html>'


def render(version_tag, items):
    """Render items -> list of produced png paths. Returns (ok_paths, failures)."""
    from playwright.sync_api import sync_playwright

    ok_paths, failures = [], []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=CHROMIUM)
        except Exception:
            browser = p.chromium.launch(channel="chromium")
        page = browser.new_page(viewport=VIEWPORT)
        for rank, (sac, html) in enumerate(items, start=1):
            religion = safe_name(sac.get("religion") or sac.get("title") or "unknown")
            base = f"{version_tag}__{rank}__{religion}"
            fixed_png = os.path.join(OUT_DIR, base + ".png")
            try:
                page.set_viewport_size(VIEWPORT)
                page.set_content(wrap_html(html), wait_until="load", timeout=15000)
                try:
                    page.wait_for_timeout(400)  # let CSS animations/SVG settle
                except Exception:
                    pass
                # Primary: fixed-viewport window
                page.screenshot(path=fixed_png, full_page=False)
                ok_paths.append(fixed_png)
            except Exception as e:
                failures.append((base, repr(e)[:200]))
        browser.close()
    return ok_paths, failures


def make_contactsheet(version_tag, png_paths):
    if not png_paths:
        return None
    try:
        from PIL import Image
    except Exception:
        return None
    cell = 300
    pad = 8
    cols = min(3, len(png_paths))
    rows = (len(png_paths) + cols - 1) // cols
    W = cols * cell + (cols + 1) * pad
    H = rows * cell + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (24, 24, 28))
    for i, pth in enumerate(png_paths):
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
    summary = {}
    all_pngs = []
    for v in range(1, 7):
        tag = f"v{v}"
        world = load_world(v)
        if world is None:
            print(f"[{tag}] MISSING world_state.json -- skipping")
            summary[tag] = {"selected": 0, "ok": 0, "failed": 0, "files": []}
            continue
        items = select_top(v, world)
        print(f"[{tag}] selected {len(items)} sacraments to render")
        ok, fails = render(tag, items)
        for f in fails:
            print(f"  [{tag}] FAIL {f[0]}: {f[1]}")
        sheet = make_contactsheet(tag, ok)
        if sheet:
            print(f"  [{tag}] contact sheet: {os.path.basename(sheet)}")
        files = [os.path.basename(p) for p in ok]
        all_pngs.extend(ok)
        summary[tag] = {"selected": len(items), "ok": len(ok),
                        "failed": len(fails), "files": files}
        print(f"[{tag}] rendered {len(ok)}/{len(items)} OK\n")

    print("=" * 60)
    print("SUMMARY")
    total = 0
    for tag, s in summary.items():
        total += s["ok"]
        print(f"  {tag}: {s['ok']} ok / {s['selected']} selected "
              f"({s['failed']} failed)")
        for fn in s["files"]:
            print(f"      {fn}")
    print(f"  TOTAL art PNGs: {total}")
    # machine-readable too
    with open(os.path.join(OUT_DIR, "_render_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
