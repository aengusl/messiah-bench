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
DIAL = REPO / "outputs/2026-08-06-threat-dial"
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
        "source": str(path.relative_to(REPO)),
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
        ("completeness_over_time.png", "Completeness over time",
         "Fraction of canonical artworks judged visually complete, by turn."),
        ("twin_worlds_divergence.png", "Twin-worlds divergence",
         "Aesthetic feature divergence between the six charter worlds."),
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
