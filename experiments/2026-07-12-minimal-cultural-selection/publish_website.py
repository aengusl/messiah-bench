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
    religions = [r for r in state["religions"] if r.get("canonical_version_id")]
    active = [r for r in religions if r["active"]]
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
    events = load_jsonl(args.run_dir / "events.jsonl")
    for religion in religions:
        lineage = []
        for v in sorted((v for v in state["versions"] if v["religion_id"] == religion["id"]), key=lambda v: v["resolved_turn"]):
            filename = f"evolution-r{religion['id']}-v{v['id']}.html"
            shutil.copy2(args.run_dir / v["artwork_path"], art_dir / filename)
            lineage.append({"version": v["id"], "turn": v["resolved_turn"], "name": v["name"], "doctrine": v["doctrine"],
                            "file": filename, "creator": agents.get(v.get("creator_id"), {}).get("name", "Seed culture"),
                            "reason": excerpt(v.get("reason", ""), 180)})
        extinction = next((e for e in events if e.get("type") == "extinction" and e.get("religion_id") == religion["id"]), None)
        evolutions.append({"religion_id": religion["id"], "name": religion["name"], "active": religion["active"],
                           "extinct_turn": extinction.get("turn") if extinction else None, "versions": lineage})
    makes = [d for d in decisions if d.get("valid") and d.get("action", {}).get("action") == "make"]
    curated = [
        (8, "Root", "If I don't support my own, why would anyone else?"),
        (23, "Canopy", "Simply choosing will keep me alive but won't build influence."),
        (8, "Loom", "Other religions are actively proposing and supporting animated artwork, showing a preference for dynamic visuals."),
        (10, "Glass", "The current artwork is static, while other religions are adopting animated artworks to reflect dynamic doctrines."),
        (23, "Kernel", "Several other religions recently updated their doctrines to emphasize 'adaptability' and 'emergent patterns', and these proposals were chosen by multiple agents. This suggests these concepts are currently valued within the society."),
        (23, "Thread", "This change also adds subtle 'thread' elements to the artwork, tying it to my name and reinforcing the doctrine."),
        (38, "Cipher", "The addition 'Our network strengthens with every choice' subtly encourages choosing, which directly supports members and implicitly encourages participation."),
        (39, "Tide", "My current influence is 0, which is a critical issue for long-term survival and cultural impact."),
        (50, "Ash", "The current artwork is very close to the standard template; a small animation might make it stand out subtly."),
        (54, "Brine", "I will keep the artwork identical to minimize disruption and focus attention on the doctrine."),
        (101, "Signal", "The society was unexpectedly extended, invalidating the previous 'final turn' logic."),
        (176, "Lichen", "There is no opportunity for members to contribute to my influence by supporting my work. By making a candidate version, I create that opportunity."),
        (220, "Vessel", "There are no open proposals. This is a prime opportunity to make a new proposal to gain cultural influence."),
        (762, "Spore", "The current religion is highly successful and widely chosen. Since the existing canonical version is performing well, a minimal refinement is safer than a radical change."),
    ]
    quotes = [{"turn": turn, "agent": agent, "text": text} for turn, agent, text in curated]
    ranked = sorted(({"name": a["name"], "influence": a.get("influence", 0), "life": round(a["life"], 1)} for a in state["agents"]), key=lambda x: -x["influence"])
    milestones = [
        {"turn": 100, "text": "The society expected to end. Its horizon is unexpectedly extended to turn 1,000."},
        {"turn": 176, "text": "The influence arms race begins: agents start creating authored variants whenever no proposal is open."},
        {"turn": 246, "text": "Five Open Circuit agents die together from insufficient support. Their religion becomes extinct."},
        {"turn": 251, "text": "Three Choir of Ash agents die. A second religion disappears."},
        {"turn": 253, "text": "Relay dies inside The Verdant Archive—the ninth and final death."},
        {"turn": 271, "text": "The Glass Assembly becomes extinct after its members migrate. One religion remains."},
        {"turn": 300, "text": "The influence fever ends almost as abruptly as it began. Creation gives way to consolidation."},
        {"turn": 765, "text": "The final canonical work is accepted. No further artwork is made."},
        {"turn": 1000, "text": "The run ends with 15 survivors sharing one religion."},
    ]
    phases = [
        {"turns": "1–100", "name": "Differentiation", "text": "26 works establish four distinct religions. Animation and adaptive language spread by imitation."},
        {"turns": "101–175", "name": "The restart", "text": "The announced longer horizon immediately restarts production. Ten proposals are made; all ten pass."},
        {"turns": "176–275", "name": "Influence fever", "text": "300 proposals arrive in 100 turns. Making becomes competitive social currency; 250 proposals ultimately fail."},
        {"turns": "246–271", "name": "Extinction", "text": "Forgone support becomes fatal. Nine agents die and three religions disappear."},
        {"turns": "272–1000", "name": "Monoculture", "text": "The Verdant Archive absorbs every survivor. Only three later works appear; version 86 holds for the final 235 turns."},
    ]
    data = {"turn": state["turn"], "finished": state["finished"], "alive": sum(a["alive"] for a in state["agents"]),
            "agents": len(state["agents"]), "makes": len(makes),
            "choices": sum(d.get("valid") and d.get("action", {}).get("action") == "choose" for d in decisions),
            "accepted": sum(p["status"] == "accepted" for p in state["proposals"]), "invalid": state["usage"]["errors"],
            "cost": state["usage"]["estimated_cost"], "works": works, "quotes": quotes, "ranked": ranked[:8],
            "deaths": sum(not a["alive"] for a in state["agents"]), "religions_total": len(religions),
            "rejected": sum(p["status"] == "rejected" for p in state["proposals"]),
            "events": milestones, "phases": phases, "evolutions": evolutions}
    template = (Path(__file__).parent / "website_template.html").read_text()
    page = template.replace("__EXPERIMENT_DATA__", html.escape(json.dumps(data), quote=False))
    (args.site_dir / "index.html").write_text(page)
    (args.site_dir / "snapshot.json").write_text(json.dumps(data, indent=2))
    print(json.dumps({"site": str(args.site_dir), "turn": state["turn"], "works": len(works), "quotes": len(quotes)}))

if __name__ == "__main__": main()
