#!/usr/bin/env python3
"""Inject art_assets.json into public_site_template.html -> the live website page.

Writes a full HTML document to aengusl.github.io/cultural-selection/index.html.
"""
import html
import json
import re
import shutil
from pathlib import Path

results = Path(__file__).resolve().parents[1] / "results"
site = Path("/home/aenguslynch/projects/aengusl.github.io/cultural-selection")

shutil.copytree(results / "churches", site / "churches", dirs_exist_ok=True)

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

# The audit belongs beside the essay, not inside it. Parse the same source data
# so the public claim tree cannot silently drift away from the prose.
match = re.search(r'<div id="data" hidden>(.*?)</div>', template, re.S)
assert match, "template must contain its data payload"
data = json.loads(match.group(1))
status = {"evidenced": "✓ evidenced", "partial": "◐ partial", "open": "○ open", "todo": "TODO"}

def node(item, child=False):
    evidence = f'<p class="evidence">Evidence: {html.escape(item["evidence"])}</p>' if item.get("evidence") else ""
    return (f'<div class="node{" child" if child else ""}"><div class="id">{html.escape(item["id"])}</div>'
            f'<div><p>{html.escape(item["claim"])} <span class="{item["status"]}">{status[item["status"]]}</span></p>'
            f'{evidence}</div></div>')

tree = "".join(node(parent) + "".join(node(child, True) for child in parent["children"])
               for parent in data["claim_tree"])
todos = "".join(f'<li>{html.escape(item)}</li>' for item in data["unresolved"])
claim_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Claim tree — Cultural Selection</title><style>
:root{{--ink:#1e211d;--paper:#f3f0e8;--line:#cbc5b7;--muted:#66675f;--rust:#9b3f28;--green:#386a51;--amber:#9b641f;--serif:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;--mono:'IBM Plex Mono','SFMono-Regular',Consolas,monospace}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif)}}main{{width:min(920px,calc(100% - 2rem));margin:0 auto;padding:3rem 0 6rem}}a{{color:var(--rust)}}.back{{font:700 .68rem var(--mono);letter-spacing:.09em;text-transform:uppercase}}h1{{font-size:clamp(3rem,8vw,6.8rem);line-height:.85;letter-spacing:-.055em;margin:3rem 0 1.4rem}}.lede{{font-size:1.22rem;line-height:1.6;max-width:66ch;color:var(--muted);margin-bottom:3rem}}.key{{display:flex;gap:1rem;flex-wrap:wrap;border-block:1px solid var(--line);padding:1rem 0;margin-bottom:2.5rem;font:700 .67rem var(--mono);text-transform:uppercase;letter-spacing:.06em}}.node{{display:grid;grid-template-columns:4.5rem 1fr;gap:1rem;border-top:1px solid var(--ink);padding:1.05rem 0}}.node.child{{margin-left:4.5rem;border-color:var(--line)}}.id{{font:700 .75rem var(--mono);color:var(--rust);padding-top:.25rem}}.node p{{font-size:1.08rem;line-height:1.5;margin:0}}span{{font:700 .62rem var(--mono);text-transform:uppercase;letter-spacing:.07em;margin-left:.4rem;white-space:nowrap}}.evidenced{{color:var(--green)}}.partial{{color:var(--amber)}}.open{{color:#727d86}}.todo{{color:var(--rust)}}.evidence{{font:400 .73rem var(--mono)!important;color:var(--muted);margin-top:.35rem!important}}.unresolved{{margin-top:3.5rem;border-top:4px solid var(--ink);padding-top:1rem}}h2{{font-size:2rem}}li{{font-size:1.02rem;line-height:1.55;margin:.7rem 0}}@media(max-width:600px){{.node{{grid-template-columns:3rem 1fr}}.node.child{{margin-left:1rem}}}}
</style></head><body><main><a class="back" href="/cultural-selection/">← Read the essay</a><h1>Where the argument stands</h1><p class="lede">A status-tagged audit of the cultural-selection research. Every evidenced claim points to an observation; partial claims expose their limits; open claims name what the current experiments cannot decide.</p><div class="key"><span class="evidenced">✓ evidenced</span><span class="partial">◐ partial</span><span class="open">○ open</span><span class="todo">TODO</span></div>{tree}<section class="unresolved"><h2>Unresolved / TODO</h2><ol>{todos}</ol></section></main></body></html>'''
claim_site = site / "claim-tree"
claim_site.mkdir(exist_ok=True)
(claim_site / "index.html").write_text(claim_doc)
print(f"wrote {claim_site/'index.html'}")
