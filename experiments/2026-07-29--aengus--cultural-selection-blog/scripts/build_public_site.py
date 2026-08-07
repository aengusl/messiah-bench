#!/usr/bin/env python3
"""Inject art_assets.json into public_site_template.html -> the live website page.

Writes a full HTML document to aengusl.github.io/cultural-selection/index.html.
"""
import html
import json
from pathlib import Path

results = Path(__file__).resolve().parents[1] / "results"
site = Path("/home/aenguslynch/projects/aengusl.github.io/cultural-selection")

assets = json.loads((results / "art_assets.json").read_text())
template = (results / "public_site_template.html").read_text()
payload = html.escape(json.dumps(assets, ensure_ascii=False), quote=False)
body = template.replace("__ASSETS__", payload)

title_line, _, rest = body.partition("\n")
assert title_line.startswith("<title>"), "template must start with <title>"
doc = (
    "<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width, initial-scale=1'>"
    + title_line + "</head><body>\n" + rest + "\n</body></html>\n"
)
tmp = site / "index.html.tmp"
tmp.write_text(doc)
tmp.replace(site / "index.html")
print(f"wrote {site/'index.html'} ({len(doc)/1e6:.2f} MB)")
