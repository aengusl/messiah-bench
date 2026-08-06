#!/usr/bin/env python3
"""Inject results/art_assets.json into evidence_template.html -> results/progress.html.

progress.html is the published artifact (stable URL); the template is the source.
"""
import html
import json
from pathlib import Path

results = Path(__file__).resolve().parents[1] / "results"
assets = json.loads((results / "art_assets.json").read_text())
template = (results / "evidence_template.html").read_text()

payload = html.escape(json.dumps(assets, ensure_ascii=False), quote=False)
out = template.replace("__ASSETS__", payload)
tmp = results / "progress.html.tmp"
tmp.write_text(out)
tmp.replace(results / "progress.html")
print(f"wrote results/progress.html ({len(out)/1e6:.2f} MB)")
