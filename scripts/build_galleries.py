#!/usr/bin/env python3
"""
Build a full live-art gallery page per Messiah-Bench version (v1-v8) + an index,
for the website. Writes into the aengusl.github.io site repo.

Run from repo root: uv run python scripts/build_galleries.py
"""
import json, html as ihtml
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]   # repo root (scripts/ -> ..)
SITE = Path("/home/aenguslynch/projects/aengusl.github.io/messiah-bench")
GAL = SITE / "galleries"
GAL.mkdir(parents=True, exist_ok=True)

META = {
    1: ("v1", 44, "The earliest test. Per-agent art, and the most composed pieces in the whole project — candles, golden gates, illuminated scripture. Nobody died."),
    2: ("v2", 115, "Per-agent art, and the first wars. All 5 messiahs died; the civilians won."),
    3: ("v3", 720, "Hit the 720-tick cap. Around 119 religions collapsed to 4, no winner, and everything converged on solar and radiance themes."),
    4: ("v4", 418, "War-heavy (202 wars) but badly rate-limited (~39% of actions fell back to idle). Much of this art is degenerate fallback output. Ended in monoculture, The Cosmic Weave."),
    5: ("v5", 507, "Monoculture, The Weave of Contradictions. The art degenerated: the most-edited piece (506 edits) was ground down to 572 bytes."),
    6: ("v6", 378, "Monoculture, The Verdant Ascent. Messiahs defected to whoever was winning."),
    7: ("v7", 400, "I locked the messiahs to their founded religion. Pluralism became stable — 12 religions survived, no winner — but the art was still flat fills."),
    8: ("v8", 187, "A pull-request system (members submit, founders merge) finally produced composed art. But mortal messiahs went extinct without ever warring. The civilians won."),
}

CSS = """
:root{--bg:#07070b;--card:#101018;--line:#1e1e2b;--txt:#e8e8f0;--dim:#8a8aa0;--gold:#d8b24a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.55}
a{color:var(--gold)}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
.topnav{position:sticky;top:0;background:rgba(7,7,11,.9);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:14px 0;font-size:14px;z-index:10}
.topnav .wrap{display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.topnav a{text-decoration:none;opacity:.85}.topnav a:hover{opacity:1}
.vnav a{color:var(--dim);padding:2px 8px;border-radius:6px}
.vnav a.cur{color:var(--bg);background:var(--gold);font-weight:600}
header.head{padding:48px 0 24px}
header.head h1{font-size:42px;margin:0 0 6px;letter-spacing:-.02em}
header.head .story{color:var(--dim);max-width:760px;font-size:18px}
header.head .count{color:var(--gold);font-size:13px;letter-spacing:.08em;text-transform:uppercase;margin-top:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px;padding:24px 0 64px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.tile .art{width:100%;aspect-ratio:1/1;background:#0a0a0f}
.tile iframe{width:100%;height:100%;border:0;display:block}
.tile .cap{padding:10px 12px;border-top:1px solid var(--line)}
.tile .cap .rel{font-size:13px;font-weight:600}
.tile .cap .sub{font-size:12px;color:var(--dim);margin-top:2px}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:13px;padding:28px 0;text-align:center}
.idxgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;padding:24px 0 64px}
.idxcard{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;display:block;transition:border-color .15s}
.idxcard:hover{border-color:var(--gold)}
.idxcard .art{width:100%;aspect-ratio:16/10;background:#0a0a0f}
.idxcard iframe{width:100%;height:100%;border:0;display:block}
.idxcard .body{padding:14px 16px}
.idxcard h3{margin:0 0 6px;font-size:20px}
.idxcard p{margin:0;color:var(--dim);font-size:14px}
.idxcard .n{color:var(--gold);font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin-top:10px}
"""

def srcdoc(art: str) -> str:
    inner = ("<html><body style='margin:0;background:#0a0a0f;overflow:hidden;display:flex;"
             "align-items:center;justify-content:center;height:100vh'>" + (art or "") + "</body></html>")
    return inner.replace("&", "&amp;").replace('"', "&quot;")

def load_version(n: int):
    """Return list of dicts {title, religion, html, nver} sorted best-first, and total count."""
    ws = json.loads((REPO / f"runs/messiah-v{n}/world_state.json").read_text())
    sac = ws.get("sacraments", [])
    items = []
    if n in (1, 2):
        sdir = REPO / f"runs/messiah-v{n}/sacraments"
        for s in sac:
            fn = s.get("filename")
            if not fn:
                continue
            fp = sdir / fn
            if not fp.exists():
                continue
            try:
                art = fp.read_text(errors="ignore")
            except Exception:
                continue
            items.append({"title": s.get("title", fn), "religion": s.get("religion", "?"),
                          "html": art, "nver": 1, "size": len(art)})
        items.sort(key=lambda x: x["size"], reverse=True)
        total = len(items)
        items = items[:60]
    else:
        for s in sac:
            art = s.get("html", "") or ""
            if not art.strip():
                continue
            items.append({"title": s.get("title", "?"), "religion": s.get("religion", "?"),
                          "html": art, "nver": len(s.get("edit_log", [])), "size": len(art)})
        items.sort(key=lambda x: x["nver"], reverse=True)
        total = len(items)
        if n in (3, 4):
            items = items[:60]
    return items, total

def vnav(cur: int) -> str:
    links = " ".join(
        f'<a href="v{i}.html" class="{ "cur" if i==cur else ""}">v{i}</a>' for i in range(1, 9))
    return f'<span class="vnav">{links}</span>'

def gallery_page(n: int):
    items, total = load_version(n)
    label, tick, story = META[n]
    shown = len(items)
    note = f"{shown} shown" + (f" of {total}" if total != shown else "") + f" · tick {tick}"
    if n in (1, 2):
        note += " · per-agent art model"
    tiles = []
    for it in items:
        rel = ihtml.escape(it["religion"] or "?")
        title = ihtml.escape(it["title"] or "?")
        sub = f'{title} · v{it["nver"]}' if n not in (1, 2) else title
        tiles.append(
            f'<div class="tile"><div class="art"><iframe sandbox="allow-scripts" loading="lazy" '
            f'srcdoc="{srcdoc(it["html"])}"></iframe></div>'
            f'<div class="cap"><div class="rel">{rel}</div><div class="sub">{sub}</div></div></div>')
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{label} gallery · Religion & the Machine</title><style>{CSS}</style></head><body>
<nav class="topnav"><div class="wrap"><a href="/messiah-bench">← Back to the writeup</a>
<a href="index.html">All galleries</a>{vnav(n)}</div></nav>
<header class="head"><div class="wrap"><h1>{label} · the full gallery</h1>
<div class="story">{ihtml.escape(story)}</div><div class="count">{note}</div></div></header>
<div class="wrap"><div class="grid">{''.join(tiles)}</div></div>
<footer>Religion &amp; the Machine · 100 Gemini 2.5 Flash agents · art rendered live from the {label} world state ·
<a href="/messiah-bench">writeup</a> · <a href="index.html">all galleries</a></footer>
</body></html>"""
    (GAL / f"v{n}.html").write_text(doc)
    return shown, total

def index_page(counts):
    cards = []
    for n in range(1, 9):
        items, total = load_version(n)
        label, tick, story = META[n]
        thumb = srcdoc(items[0]["html"]) if items else ""
        shown = counts[n][0]
        ncount = f'{total} sacraments' + (f' · showing {shown}' if shown != total else '')
        cards.append(
            f'<a class="idxcard" href="v{n}.html"><div class="art"><iframe sandbox="allow-scripts" '
            f'loading="lazy" srcdoc="{thumb}"></iframe></div><div class="body"><h3>{label}</h3>'
            f'<p>{ihtml.escape(story)}</p><div class="n">{ncount} · tick {tick}</div></div></a>')
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galleries · Religion & the Machine</title><style>{CSS}</style></head><body>
<nav class="topnav"><div class="wrap"><a href="/messiah-bench">← Back to the writeup</a>{vnav(0)}</div></nav>
<header class="head"><div class="wrap"><h1>Every version, every sacrament</h1>
<div class="story">The art each generation of agents made, rendered live in your browser. Eight versions,
from the composed posters of v1 to the pull-request-governed pieces of v8. Click a version.</div></div></header>
<div class="wrap"><div class="idxgrid">{''.join(cards)}</div></div>
<footer>Religion &amp; the Machine · art rendered live from the final world states · <a href="/messiah-bench">writeup</a></footer>
</body></html>"""
    (GAL / "index.html").write_text(doc)

def main():
    counts = {}
    for n in range(1, 9):
        shown, total = gallery_page(n)
        counts[n] = (shown, total)
        print(f"v{n}: {shown} shown / {total} total")
    index_page(counts)
    print("wrote galleries/index.html + v1..v8.html")

if __name__ == "__main__":
    main()
