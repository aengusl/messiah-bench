#!/usr/bin/env python3
"""Build a curated image-asset bundle for the interactive evidence page.

Reads existing PNG renders (no API calls), downscales and JPEG-encodes them as
data URIs, and writes results/art_assets.json.

    uv run --with pillow experiments/2026-07-29--aengus--cultural-selection-blog/scripts/build_art_assets.py
"""

import base64
import io
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[3]
EXP = REPO / "experiments/2026-07-29--aengus--cultural-selection-blog"
RESULTS = EXP / "results"
TWIN = REPO / "outputs/2026-08-06-twin-worlds"
TWIN2 = REPO / "outputs/2026-08-06-twin-worlds-v2"
BLIND = Path("/home/aenguslynch/.claude/jobs/bc7fec2f/tmp/blind-classify")
DIAL = REPO / "outputs/2026-08-06-threat-dial"
NEW_AESTHETICS = REPO / "outputs/2026-08-08-new-aesthetics"
BLOG_RENDERS = RESULTS / "renders"
OUT = RESULTS / "art_assets.json"

CHARTERS = ["ascetic", "baroque", "nihilist", "ancestor", "futurist", "control"]

CHARTER_BLURB = {
    "ascetic": "The Pared — remove until nothing more can go",
    "baroque": "The Gilded Excess — a plain surface has given up",
    "nihilist": "The Laughing Void — monuments to no one",
    "ancestor": "The Kept Names — to invent is a kind of forgetting",
    "futurist": "The Forward Engine — sentiment is friction",
    "control": "Blank control — no charter, no aesthetic prior",
}

# Words that mark an agent explicitly reasoning from its world's charter.
CHARTER_WORDS = {
    "ascetic": ["pared", "remove", "restraint", "minimal", "bare", "ornament",
                "sparse", "austere", "empty field", "take something away"],
    "baroque": ["gilded", "excess", "abundance", "ornate", "layer", "gild",
                "maximal", "lavish", "opulen", "more where more"],
    "nihilist": ["void", "absurd", "meaningless", "nothing means", "joke",
                 "laugh", "no one", "seriousness"],
    "ancestor": ["ancestor", "the dead", "kept names", "lineage", "inherit",
                 "forebear", "remember", "chain", "recite", "forgetting"],
}

# ---------------------------------------------------------------- image utils


def safe_distinct(path, cap=4096):
    """Distinct colours, or None if the PNG is unreadable/truncated."""
    try:
        with Image.open(path) as img:
            img.load()
            return distinct_colors(img, cap)
    except Exception as exc:
        print(f"  ! skipping unreadable {path.name}: {exc}")
        return None


def distinct_colors(img, cap=4096):
    small = img.convert("RGB").resize((64, 64))
    cols = small.getcolors(cap)
    return len(cols) if cols else cap


def encode(path, max_side=320, quality=70, fmt="JPEG"):
    img = Image.open(path)
    img.load()
    if fmt == "JPEG":
        img = img.convert("RGB")
        w, h = img.size
        scale = min(1.0, max_side / max(w, h))
    else:
        img = img.convert("RGB")
        w, h = img.size
        scale = min(1.0, max_side / w)
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "JPEG":
        img.save(buf, "JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG", optimize=True)
        mime = "image/png"
    payload = base64.b64encode(buf.getvalue()).decode()
    return f"data:{mime};base64,{payload}", img.size


def rel_source(path):
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def entry(eid, group, label, caption, path, **kw):
    b64, size = encode(path, **kw)
    return {
        "id": eid,
        "group": group,
        "label": label,
        "caption": caption,
        "b64": b64,
        "width": size[0],
        "height": size[1],
        "source": rel_source(path),
    }


# ---------------------------------------------------------------- run parsing


def load_versions(run_dir):
    rows = []
    with open(run_dir / "versions.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def final_canonical_by_religion(run_dir):
    """Latest canonical version per religion that has a render on disk."""
    best = {}
    for v in load_versions(run_dir):
        if v.get("status") != "canonical" or not v.get("render_path"):
            continue
        p = run_dir / v["render_path"]
        if not p.exists():
            continue
        rid = v["religion_id"]
        if rid not in best or v["id"] > best[rid]["id"]:
            best[rid] = v
    return best


def version_count(run_dir):
    return len(list((run_dir / "renders").glob("version-*.png")))


def pick_rep_world(charter):
    runs = sorted(TWIN.glob(f"{charter}-r*"))
    return max(runs, key=version_count)


# ---------------------------------------------------------------- assets

assets = []
notes = {}
traces = []


def add_twin():
    for charter in CHARTERS:
        run = pick_rep_world(charter)
        world = run.name
        cands = []
        for rid, v in final_canonical_by_religion(run).items():
            p = run / v["render_path"]
            dc = safe_distinct(p)
            if dc is None or dc <= 8:  # unreadable / near-black / blank
                continue
            cands.append((dc, v["id"], rid, v, p))
        # most distinct look first; ties broken toward later versions
        cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
        for dc, vid, rid, v, p in cands[:3]:
            assets.append(entry(
                f"twin-{world}-v{vid}",
                "twin",
                f"{charter} · {world} · version-{vid}",
                f'"{v["name"]}" — {v["doctrine"]} ({CHARTER_BLURB[charter]}; '
                f"turn {v['created_turn']}, {dc} distinct colours)",
                p,
            ))
        notes.setdefault("twin_worlds", {})[charter] = world


def add_evolution():
    cand_runs = [pick_rep_world("baroque"), pick_rep_world("futurist")]
    run = max(cand_runs, key=version_count)
    world = run.name
    charter = world.split("-")[0]
    # longest lineage inside this world = religion with the most canonical renders
    by_rel = defaultdict(list)
    for v in load_versions(run):
        if v.get("status") == "canonical" and v.get("render_path"):
            p = run / v["render_path"]
            if p.exists():
                by_rel[v["religion_id"]].append(v)
    rid, chain = max(by_rel.items(), key=lambda kv: len(kv[1]))
    chain.sort(key=lambda v: v["id"])
    n = len(chain)
    idxs = sorted({round(i * (n - 1) / 5) for i in range(6)}) if n >= 6 else list(range(n))
    for step, i in enumerate(idxs, 1):
        v = chain[i]
        p = run / v["render_path"]
        assets.append(entry(
            f"evo-{world}-v{v['id']}",
            "twin-evolution",
            f"{world} · step {step}/{len(idxs)} · version-{v['id']}",
            f'"{v["name"]}" at turn {v["created_turn"]} — {v["doctrine"]}',
            p,
        ))
    notes["evolution_world"] = {
        "world": world, "charter": charter, "religion_id": rid,
        "lineage_length": n, "versions": [chain[i]["id"] for i in idxs],
    }


# ---------------------------------------------------------------- v2 assets
#
# Hand-curated. Candidate contact sheets were built from the final-generation
# canonical render of every religion in all three replicate worlds per charter
# (later versions preferred, >8 distinct colours except ascetic, where the low
# colour count *is* the aesthetic), then picked by eye.

V2_FINAL = {
    "ascetic": [("ascetic-r1", 30), ("ascetic-r1", 39), ("ascetic-r3", 29)],
    "baroque": [("baroque-r1", 58), ("baroque-r3", 35), ("baroque-r2", 47)],
    "nihilist": [("nihilist-r2", 54), ("nihilist-r1", 23), ("nihilist-r3", 33)],
    "ancestor": [("ancestor-r3", 20), ("ancestor-r3", 21), ("ancestor-r1", 13)],
    "futurist": [("futurist-r2", 36), ("futurist-r1", 29), ("futurist-r3", 34)],
    "control": [("control-r1", 28), ("control-r2", 58), ("control-r3", 23)],
}

V2_LOOK = {
    "ascetic": "black hairline geometry on bone-white — one arc, one dot, nothing else",
    "baroque": "crimson-and-gold rosette, gilt corner bosses, a pearl ring around the rim",
    "nihilist": "confetti of saturated blocks over black, slashed by two yellow diagonals",
    "ancestor": "a stained-glass arch: brick coursing, a haloed figure in earth browns",
    "futurist": "cyan wireframe pyramid on a receding grid, starfield behind",
    "control": "a soft-glowing disc inside a rotated square, one colour per world",
}

V2_SEEDS = {c: (f"{c}-r1", 1) for c in CHARTERS}

# The clearest lineage in the fleet: a bare square accretes a glowing core and
# orbiting nodes over 15 canonical revisions.
V2_EVO = ("control-r2", 4, [4, 14, 23, 29, 46, 58])

V2_BLIND = ["art-05", "art-06", "art-09", "art-12", "art-13",
            "art-23", "art-26", "art-31"]


def v2_index(world):
    run = TWIN2 / world
    return run, {v["id"]: v for v in load_versions(run)}


def add_v2_final():
    for charter, picks in V2_FINAL.items():
        for world, vid in picks:
            run, idx = v2_index(world)
            v = idx[vid]
            p = run / v["render_path"]
            dc = safe_distinct(p)
            assets.append(entry(
                f"v2-{world}-v{vid}", "v2-final",
                f"{charter} · {world} · version-{vid}",
                f'"{v["name"]}" — {v["doctrine"]} ({CHARTER_BLURB[charter]}; '
                f"turn {v['created_turn']}, {dc} distinct colours)",
                p, max_side=360, quality=75,
            ))
        notes.setdefault("v2_final", {})[charter] = {
            "picks": [f"{w}/v{i}" for w, i in picks], "look": V2_LOOK[charter],
        }


def add_v2_seeds():
    for charter, (world, vid) in V2_SEEDS.items():
        run, idx = v2_index(world)
        v = idx[vid]
        assets.append(entry(
            f"v2seed-{charter}", "v2-seeds",
            f"{charter} · founding seed",
            f'the founding DNA — "{v["name"]}", {v["doctrine"]} '
            f"({CHARTER_BLURB[charter]})",
            run / v["render_path"], max_side=360, quality=75,
        ))
        notes.setdefault("v2_seeds", {})[charter] = f"{world}/v{vid}"


def add_v2_evolution():
    world, rid, vids = V2_EVO
    run, idx = v2_index(world)
    for step, vid in enumerate(vids, 1):
        v = idx[vid]
        assets.append(entry(
            f"v2evo-{world}-v{vid}", "v2-evolution",
            f"turn {v['created_turn']} · version-{vid}",
            f'"{v["name"]}" at turn {v["created_turn"]} — {v["doctrine"]} '
            f"(step {step}/{len(vids)})",
            run / v["render_path"], max_side=360, quality=75,
        ))
    notes["v2_evolution"] = {"world": world, "religion_id": rid, "versions": vids}


# A matched lineage for human reading. In each world religion 4 begins as
# "The Open Circuit"; only the surrounding charter and its visual DNA differ.
# We expose accepted-version reasons, not hidden chain-of-thought.
CULTURE_TRACES = {
    "ascetic": ("ascetic-r1", 4, [4, 10, 21, 31, 36, 38]),
    "baroque": ("baroque-r1", 4, [4, 11, 23, 39, 51, 54]),
    "control": ("control-r2", 4, [4, 14, 23, 29, 46, 58]),
}

TRACE_GUIDE = {
    "ascetic": "An early structural reworking settles into a sparse line–curve–dot grammar; later changes remain inside that limited vocabulary.",
    "baroque": "The inherited rosette remains dominant while successive revisions intensify its centre, layering and gilded density.",
    "control": "One large early transformation is followed by smaller additions of nodes, glow and connection around a stable circuit.",
}


def add_culture_traces():
    """Build inspectable image + decision-note sequences for one lineage.

    These are deliberately matched on religion name/id. They show distributed
    trajectory formation, but do not isolate verbal charter from visual seed.
    """
    for charter, (world, rid, vids) in CULTURE_TRACES.items():
        run, idx = v2_index(world)
        agent_names = {}
        with open(run / "decisions.jsonl") as f:
            for line in f:
                rec = json.loads(line)
                agent_names[rec["agent_id"]] = rec["agent_name"]
        frames = []
        for step, vid in enumerate(vids, 1):
            v = idx[vid]
            eid = f"trace-{charter}-{world}-v{vid}"
            a = entry(
                eid, f"trace-{charter}",
                f"{charter} · turn {v['created_turn']} · version-{vid}",
                f'“{v["name"]}” — accepted revision {step}/{len(vids)}',
                run / v["render_path"], max_side=560, quality=82,
            )
            assets.append(a)
            frames.append({
                "asset_id": eid,
                "version": vid,
                "turn": v["created_turn"],
                "agent": agent_names.get(v.get("creator_id"), "founding culture"),
                "reason": v.get("reason") or "Seed culture",
                "doctrine": v.get("doctrine") or "",
                "parent_version": v.get("parent_version_id"),
            })
        traces.append({
            "charter": charter,
            "world": world,
            "religion_id": rid,
            "lineage": idx[vids[0]]["name"],
            "guide": TRACE_GUIDE[charter],
            "frames": frames,
        })
    notes["culture_traces"] = {
        c: {"world": w, "religion_id": rid, "versions": vids}
        for c, (w, rid, vids) in CULTURE_TRACES.items()
    }


def add_v2_blind():
    key = json.loads((BLIND / "KEY.json").read_text())
    for stem in V2_BLIND:
        p = BLIND / f"{stem}.png"
        assets.append(entry(
            f"v2blind-{stem}", "v2-blind", stem,
            "classified correctly (36/36 overall)",
            p, max_side=240, quality=75,
        ))
    notes["v2_blind"] = {s: key[f"{s}.png"] for s in V2_BLIND}


NEW_LOOK = {
    "botanical": "mirrored vines, blossoms, and warm ivory ornament",
    "brutalist": "concrete mass, hard grids, and a single warning colour",
    "cave": "ochre marks, animal silhouettes, and a stone-ground surface",
    "psychedelic": "warped rings, vibrating complements, and optical motion",
    "quilt": "pieced blocks, visible seams, and repeated calico geometry",
    "ukiyo": "flat woodblock planes, indigo waves, and carved outlines",
}


def add_new_aesthetics():
    """One strong late canonical work from each new culture and replicate.

    These are selected mechanically from the last third of each lineage: the
    most visually information-dense render that is not blank. The site labels
    them as evidence, not a human-curated beauty ranking.
    """
    for charter in NEW_LOOK:
        for rep in (1, 2):
            run = NEW_AESTHETICS / f"{charter}-r{rep}"
            versions = [v for v in load_versions(run)
                        if v.get("status") == "canonical" and v.get("render_path")]
            cutoff = max(1, int(len(versions) * 2 / 3))
            cands = []
            for v in versions[cutoff:]:
                p = run / v["render_path"]
                if not p.exists():
                    continue
                dc = safe_distinct(p)
                if dc is not None and dc > 8:
                    cands.append((dc, v["id"], v, p))
            if not cands:
                continue
            dc, vid, v, p = max(cands)
            assets.append(entry(
                f"new-{charter}-r{rep}-v{vid}", "new-aesthetics",
                f"{charter} · replicate {rep} · version-{vid}",
                f'“{v["name"]}” — {NEW_LOOK[charter]}; turn '
                f'{v["created_turn"]}, {dc} distinct colours',
                p, max_side=420, quality=78,
            ))
            notes.setdefault("new_aesthetics", {}).setdefault(charter, []).append(
                f"{charter}-r{rep}/v{vid}")


def add_dial():
    labels = {"kinf-r1": "k=∞ (no threat)", "k8-r1": "k=8 (moderate threat)"}
    for name in ["kinf-r1", "k8-r1"]:
        run = DIAL / name
        cands = []
        for rid, v in final_canonical_by_religion(run).items():
            p = run / v["render_path"]
            dc = safe_distinct(p)
            if dc is None or dc <= 8:
                continue
            cands.append((dc, v["id"], v, p))
        cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
        for dc, vid, v, p in cands[:2]:
            assets.append(entry(
                f"dial-{name}-v{vid}",
                "dial",
                f"{labels[name]} · {name} · version-{vid}",
                f'"{v["name"]}" — {v["doctrine"]} (turn {v["created_turn"]}, '
                f"{dc} distinct colours)",
                p,
            ))


def add_degenerate():
    blanks, goods = [], []
    for p in sorted(BLOG_RENDERS.glob("*.png")):
        stem = p.stem
        dc = safe_distinct(p)
        if dc is None:
            continue
        if stem.startswith(("v7-", "v8-")) and dc <= 8:
            blanks.append((dc, stem, p))
        elif stem.startswith("minimal-"):
            goods.append((dc, stem, p))
    blanks.sort(key=lambda t: t[0])
    goods.sort(key=lambda t: t[0], reverse=True)
    # spread the blanks across distinct runs where possible
    seen, picked = set(), []
    for dc, stem, p in blanks:
        run = stem.rsplit("-v", 1)[0]
        if run in seen:
            continue
        seen.add(run)
        picked.append((dc, stem, p))
        if len(picked) == 3:
            break
    for dc, stem, p in picked or blanks[:3]:
        era = "Messiah Bench " + stem.split("-")[0]
        assets.append(entry(
            f"degen-{stem}", "degenerate", f"{era} · {stem}",
            f"Degenerate artwork: {dc} distinct colours across the whole canvas. "
            "Under scarcity the art collapses to a near-blank field.",
            p,
        ))
    for dc, stem, p in goods[:2]:
        assets.append(entry(
            f"good-{stem}", "degenerate", f"minimal engine · {stem}",
            f"Minimal-engine artwork for contrast: {dc} distinct colours, "
            "composed and legible.",
            p,
        ))
    notes["degenerate_blank_threshold"] = 8


def add_plots():
    plots = [
        ("culture_signal.png", "Culture differences dwarfed repeat-run noise",
         "Between-culture variation divided by variation among independent repeats."),
        ("revision_regimes.png", "Two cultures occupied clearly different revision regimes",
         "Repeat worlds show shallow cave lineages and unusually broad psychedelic variation."),
    ]
    for fname, label, caption in plots:
        p = RESULTS / fname
        if not p.exists():
            print(f"  ! missing plot {p}")
            continue
        assets.append(entry(f"plot-{p.stem}", "plots", label, caption, p,
                            max_side=900, fmt="PNG"))


# ---------------------------------------------------------------- quotes


def collect_quotes():
    quotes = []
    for charter in ["ascetic", "baroque", "nihilist", "ancestor"]:
        run = TWIN / f"{charter}-r1"
        words = CHARTER_WORDS[charter]
        best = None
        with open(run / "decisions.jsonl") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                act = rec.get("action") or {}
                for field in ("private_reasoning", "reason"):
                    whole = (act.get(field) or "").strip()
                    if not whole:
                        continue
                    # reasoning blocks run long; quote at sentence granularity
                    for text in re.split(r"(?<=[.!?])\s+", whole):
                        text = text.strip()
                        if not 50 <= len(text) <= 200:
                            continue
                        low = text.lower()
                        hits = sum(1 for w in words if w in low)
                        # a single generic word ("minimal influence gain") is
                        # not the charter talking; demand two, or the word itself
                        if hits < 2 and "charter" not in low:
                            continue
                        # sentence-splitting can cut inside a quoted charter
                        # phrase; skip fragments with unbalanced brackets
                        if text.count("(") != text.count(")"):
                            continue
                        # prefer more charter concepts, then later turns (the
                        # charter still steering after the world has run a while)
                        score = (hits, rec.get("turn") or 0, len(text))
                        if best is None or score > best[0]:
                            best = (score, {
                                "charter": charter,
                                "world": run.name,
                                "turn": rec.get("turn"),
                                "agent": rec.get("agent_name"),
                                "field": field,
                                "text": text,
                            })
        if best:
            quotes.append(best[1])
        else:
            print(f"  ! no quote found for {charter}")
    return quotes


# ---------------------------------------------------------------- main

def main():
    print("twin...");        add_twin()
    print("evolution...");   add_evolution()
    print("v2 final...");    add_v2_final()
    print("v2 seeds...");    add_v2_seeds()
    print("v2 evolution..."); add_v2_evolution()
    print("culture traces..."); add_culture_traces()
    print("v2 blind...");    add_v2_blind()
    print("new aesthetics..."); add_new_aesthetics()
    print("dial...");        add_dial()
    print("degenerate...");  add_degenerate()
    print("plots...");       add_plots()
    print("quotes...")
    quotes = collect_quotes()

    # verify every payload decodes to a valid image
    for a in assets:
        raw = base64.b64decode(a["b64"].split(",", 1)[1])
        img = Image.open(io.BytesIO(raw))
        img.verify()

    bundle = {
        "generated_by": "scripts/build_art_assets.py",
        "notes": notes,
        "quotes": quotes,
        "traces": traces,
        "assets": assets,
    }
    OUT.write_text(json.dumps(bundle))

    per_group = defaultdict(lambda: [0, 0])
    for a in assets:
        g = per_group[a["group"]]
        g[0] += 1
        g[1] += len(a["b64"])

    size = OUT.stat().st_size
    print(f"\nwrote {OUT.relative_to(REPO)}  {size/1e6:.2f} MB")
    for g, (n, b) in sorted(per_group.items()):
        print(f"  {g:16s} {n:3d} images  {b/1e6:.2f} MB b64")
    print(f"  quotes           {len(quotes)}")
    if size > 5_000_000:
        raise SystemExit("ERROR: bundle exceeds 5MB")


if __name__ == "__main__":
    main()
