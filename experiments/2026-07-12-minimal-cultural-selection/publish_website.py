#!/usr/bin/env python3
"""Publish a standalone live exhibition page into aengusl.github.io."""

import argparse, html, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []

def excerpt(value, n=380):
    value = re.sub(r"\s+", " ", value or "").strip()
    return value if len(value) <= n else value[:n].rsplit(" ", 1)[0] + "…"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, default=ROOT / "outputs/2026-07-12-minimal-cultural-selection")
    ap.add_argument("--site-dir", type=Path, default=Path("/home/aenguslynch/projects/aengusl.github.io/cultural-selection"))
    args = ap.parse_args()
    state = json.loads((args.run_dir / "world_state.json").read_text())
    decisions = load_jsonl(args.run_dir / "decisions.jsonl")
    args.site_dir.mkdir(parents=True, exist_ok=True)
    art_dir = args.site_dir / "artworks"; art_dir.mkdir(exist_ok=True)
    versions = {v["id"]: v for v in state["versions"]}
    agents = {a["id"]: a for a in state["agents"]}
    active = [r for r in state["religions"] if r["active"] and r.get("canonical_version_id")]
    works = []
    for r in active:
        v = versions[r["canonical_version_id"]]
        filename = f"religion-{r['id']}-version-{v['id']}.html"
        shutil.copy2(args.run_dir / v["artwork_path"], art_dir / filename)
        works.append({"religion_id": r["id"], "version": v["id"], "name": v["name"], "doctrine": v["doctrine"],
                      "file": filename, "creator": agents.get(v.get("creator_id"), {}).get("name", "Seed culture"),
                      "accepted_turn": v.get("resolved_turn", 0),
                      "members": sum(a["alive"] and a["religion_id"] == r["id"] for a in state["agents"]),
                      "versions": sum(x["religion_id"] == r["id"] for x in state["versions"])})
    evolutions = []
    for religion in active:
        lineage = []
        for v in sorted((v for v in state["versions"] if v["religion_id"] == religion["id"]), key=lambda v: v["resolved_turn"]):
            filename = f"evolution-r{religion['id']}-v{v['id']}.html"
            shutil.copy2(args.run_dir / v["artwork_path"], art_dir / filename)
            lineage.append({"version": v["id"], "turn": v["resolved_turn"], "name": v["name"], "doctrine": v["doctrine"],
                            "file": filename, "creator": agents.get(v.get("creator_id"), {}).get("name", "Seed culture"),
                            "reason": excerpt(v.get("reason", ""), 180)})
        evolutions.append({"religion_id": religion["id"], "name": religion["name"], "versions": lineage})
    makes = [d for d in decisions if d.get("valid") and d.get("action", {}).get("action") == "make"]
    scored = sorted(makes, key=lambda d: sum(k in (d["action"].get("private_reasoning") or "").lower()
                  for k in ("other religions", "others choose", "influence", "preference", "trend")), reverse=True)
    quotes = [{"agent": d["agent_name"], "turn": d["turn"], "text": excerpt(d["action"].get("private_reasoning"))} for d in scored[:6]]
    ranked = sorted(({"name": a["name"], "influence": a.get("influence", 0), "life": round(a["life"], 1)} for a in state["agents"]), key=lambda x: -x["influence"])
    data = {"turn": state["turn"], "finished": state["finished"], "alive": sum(a["alive"] for a in state["agents"]),
            "agents": len(state["agents"]), "makes": len(makes),
            "choices": sum(d.get("valid") and d.get("action", {}).get("action") == "choose" for d in decisions),
            "accepted": sum(p["status"] == "accepted" for p in state["proposals"]), "invalid": state["usage"]["errors"],
            "cost": state["usage"]["estimated_cost"], "works": works, "quotes": quotes, "ranked": ranked[:8],
            "events": state["events"][-30:][::-1], "evolutions": evolutions}
    template = (Path(__file__).parent / "website_template.html").read_text()
    page = template.replace("__EXPERIMENT_DATA__", html.escape(json.dumps(data), quote=False))
    (args.site_dir / "index.html").write_text(page)
    (args.site_dir / "snapshot.json").write_text(json.dumps(data, indent=2))
    print(json.dumps({"site": str(args.site_dir), "turn": state["turn"], "works": len(works), "quotes": len(quotes)}))

if __name__ == "__main__": main()
