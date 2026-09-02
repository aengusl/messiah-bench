#!/usr/bin/env python3
"""Twin-worlds divergence: do culture charters cause persistent art divergence?

    uv run scripts/twin_worlds_report.py --fleet-dir outputs/2026-08-06-twin-worlds
    uv run scripts/twin_worlds_report.py --fleet-dir ... --allow-incomplete   # preview
    uv run scripts/twin_worlds_report.py --fleet-dir ... --judge-pairs 400    # SPENDS MONEY

H1 says a charter shifts what a world makes. The falsifier is that the charter
effect is no bigger than the difference between replicates of the same charter,
which is why every measure here is reported against a within-charter baseline.

Everything except --judge-pairs is free and offline. The script never assumes the
fleet has finished: it analyses worlds with a COMPLETE marker and names the rest.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXP / "src"))

import artlib as A  # noqa: E402
from artlib import C, say  # noqa: E402

RESULTS = EXP / "results"
CHARTERS_DIR = RESULTS / "charters"
MD_PATH = RESULTS / "twin_worlds_summary.md"
PNG_PATH = RESULTS / "twin_worlds_divergence.png"
FEATURES_CSV = RESULTS / "twin_worlds_features.csv"

CONTROL = "control"  # no charter file; the baseline every charter is measured against

# Validated categorical palette (slots 1-6 of the default theme, light mode).
CHARTER_COLOR = {
    "control": "#7a7a75",
    "ascetic": "#2a78d6",
    "baroque": "#eb6834",
    "ancestor": "#1baf7a",
    "futurist": "#eda100",
    "nihilist": "#4a3aa7",
}
REP_MARKER = {"r1": "o", "r2": "s", "r3": "^"}
INK, INK_SOFT, GRID = "#0b0b0b", "#52514e", "#dcdcd8"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for", "from",
    "had", "has", "have", "he", "her", "his", "i", "if", "in", "into", "is", "it",
    "its", "me", "my", "no", "nor", "not", "of", "on", "one", "or", "our", "ours",
    "out", "she", "so", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "those", "to", "too", "up", "us", "was", "we", "were",
    "what", "when", "which", "who", "will", "with", "would", "you", "your", "us",
    "do", "does", "did", "can", "could", "should", "may", "might", "must", "shall",
    "all", "any", "each", "every", "more", "most", "much", "very", "own", "same",
    "how", "why", "where", "while", "about", "after", "before", "again", "further",
    "some", "such", "only", "other", "over", "under", "here", "now", "also", "am",
}

WORD_RE = re.compile(r"[a-z]+")


def stem(word: str) -> str:
    """Crude suffix stripper. Charters say 'remove'; agents write 'removal'.

    Not linguistically serious — it only needs to collapse the inflections that
    actually show up, and it is applied identically to charter and world text so
    any over-stemming hits both sides.
    """
    w = word.lower()
    # Longest first, so 'ations' wins over 'ion'. 'al' and a bare trailing 'e'
    # are what collapse the pair this corpus actually turns on: the ascetic
    # charter says "remove", agents write "removal", and without these two the
    # vocabulary lists them as separate words that never match each other.
    for suffix in ("ations", "ation", "ements", "ement", "ingly", "ings", "ing",
                   "edly", "ness", "ies", "ied", "ers", "er", "est", "ed", "ly",
                   "al", "es", "s", "e"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[: -len(suffix)]
    return w


def tokenize(text: str) -> list[str]:
    return [stem(w) for w in WORD_RE.findall(text.lower()) if w not in STOPWORDS]


# ---------------------------------------------------------------- worlds

@dataclass
class World:
    name: str        # e.g. "ascetic-r1"
    charter: str     # e.g. "ascetic"
    rep: str         # e.g. "r1"
    path: Path
    complete: bool

    @property
    def has_data(self) -> bool:
        return (self.path / "versions.jsonl").exists()


WORLD_RE = re.compile(r"^(?P<charter>.+)-(?P<rep>r\d+)$")


def discover_worlds(fleet_dir: Path) -> list[World]:
    worlds = []
    for d in sorted(Path(fleet_dir).iterdir()):
        if not d.is_dir():
            continue
        m = WORLD_RE.match(d.name)
        if not m:
            continue
        worlds.append(
            World(name=d.name, charter=m["charter"], rep=m["rep"], path=d,
                  complete=(d / "COMPLETE").exists())
        )
    return worlds


def select_worlds(worlds: list[World], allow_incomplete: bool) -> list[World]:
    """Complete worlds only, unless previewing. Stragglers are named, never silent."""
    ready = [w for w in worlds if w.complete and w.has_data]
    pending = [w for w in worlds if not w.complete]
    broken = [w for w in worlds if w.complete and not w.has_data]

    if pending:
        say(f"  {C.YELLOW}{len(pending)} world(s) still running:{C.RESET} "
            f"{', '.join(w.name for w in pending)}", C.YELLOW)
    if broken:
        say(f"  {C.RED}{len(broken)} world(s) marked COMPLETE but missing data:{C.RESET} "
            f"{', '.join(w.name for w in broken)}", C.RED)

    if allow_incomplete:
        usable = [w for w in worlds if w.has_data]
        say(f"  {C.YELLOW}--allow-incomplete: analysing {len(usable)} world(s) "
            f"mid-run. These numbers are a preview, not a result.{C.RESET}", C.YELLOW)
        return usable
    return ready


# ---------------------------------------------------------------- charter vocab

def load_charter_vocab(charters_dir: Path) -> dict[str, set[str]]:
    """Distinctive stems per charter: words it uses that no other charter uses.

    Shared words ('form', 'we') carry no signal about which charter a world is
    following, so the whole point is the set difference. The control has no
    charter, which is what makes it the baseline row.
    """
    texts = {}
    for path in sorted(Path(charters_dir).glob("*.md")):
        texts[path.stem] = set(tokenize(path.read_text()))
    return {
        name: words - set().union(*(o for n, o in texts.items() if n != name))
        for name, words in texts.items()
    } if len(texts) > 1 else {n: set(w) for n, w in texts.items()}


def refine_vocab(vocab: dict[str, set[str]], control_text: str,
                 max_rate_per_1000: float = 0.20) -> dict[str, set[str]]:
    """Drop charter words that charter-free agents use anyway.

    Set-difference against the other charters is not enough: it keeps ordinary
    English like 'good', 'life', 'come', 'never', which every world says at a
    high rate regardless of charter. Those words swamp the matrix with column
    effects. The control worlds have no charter, so their reasoning is exactly
    the right yardstick for "would they have said this anyway".
    """
    tokens = tokenize(control_text)
    n = len(tokens) or 1
    counts = Counter(tokens)
    return {
        charter: {w for w in words if 1000.0 * counts[w] / n <= max_rate_per_1000}
        for charter, words in vocab.items()
    }


def world_text(world: World, max_decisions: int | None = None) -> tuple[str, list[str]]:
    """Agent reasoning plus the doctrines that actually got adopted."""
    reasoning: list[str] = []
    dec_path = world.path / "decisions.jsonl"
    if dec_path.exists():
        with open(dec_path) as fh:
            for i, line in enumerate(fh):
                if max_decisions and i >= max_decisions:
                    break
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a world still being written can end mid-line
                action = d.get("action") or {}
                if isinstance(action, dict) and action.get("private_reasoning"):
                    reasoning.append(str(action["private_reasoning"]))

    doctrines: list[str] = []
    ver_path = world.path / "versions.jsonl"
    if ver_path.exists():
        with open(ver_path) as fh:
            for line in fh:
                try:
                    v = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if v.get("status") == "canonical":
                    doctrines.append(f"{v.get('name', '')} {v.get('doctrine', '')}".strip())
    return " ".join(reasoning), doctrines


def adherence_rates(text: str, vocab: dict[str, set[str]]) -> dict[str, float]:
    """Charter-vocabulary hits per 1,000 tokens, for every charter's vocabulary."""
    tokens = tokenize(text)
    n = len(tokens)
    if not n:
        return {c: 0.0 for c in vocab}
    counts = Counter(tokens)
    return {c: 1000.0 * sum(counts[w] for w in words) / n for c, words in vocab.items()}


# ---------------------------------------------------------------- art features

ELEMENT_RE = {
    "svg": re.compile(r"<svg\b", re.I),
    "div": re.compile(r"<div\b", re.I),
    "canvas": re.compile(r"<canvas\b", re.I),
}
ANIM_RE = re.compile(r"@keyframes|<animate|animation\s*:", re.I)


def artwork_features(world: World) -> list[dict]:
    """Structural features per canonical artwork, plus colour count if rendered."""
    rows = []
    ver_path = world.path / "versions.jsonl"
    if not ver_path.exists():
        return rows
    with open(ver_path) as fh:
        for line in fh:
            try:
                v = json.loads(line)
            except json.JSONDecodeError:
                continue
            if v.get("status") != "canonical":
                continue
            art_path = world.path / v.get("artwork_path", "")
            if not art_path.exists():
                continue
            html = art_path.read_text()
            content = A.source_content(html)
            row = {
                "world": world.name, "charter": world.charter, "rep": world.rep,
                "version_id": v.get("id"), "turn": int(v.get("created_turn", 0)),
                "html_bytes": len(html),
                "n_drawable": content["foreground_elements"],
                "paintable": int(content["has_paintable_content"]),
                "n_svg": len(ELEMENT_RE["svg"].findall(html)),
                "n_div": len(ELEMENT_RE["div"].findall(html)),
                "n_canvas": len(ELEMENT_RE["canvas"].findall(html)),
                "animated": int(bool(ANIM_RE.search(html))),
                "distinct_colors": "",
            }
            render = world.path / str(v.get("render_path", ""))
            if render.exists():
                try:
                    row["distinct_colors"] = A.png_stats(render)["distinct_colors"]
                except Exception:
                    pass  # a half-written PNG from a live run is not worth failing over
            rows.append(row)
    return rows


FEATURES = ["html_bytes", "n_drawable", "n_svg", "n_div", "animated", "distinct_colors"]


def world_means(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Collapse artworks to one vector per world — the unit H1 is about."""
    by_world: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_world[r["world"]].append(r)

    out = {}
    for world, rs in by_world.items():
        m = {"charter": rs[0]["charter"], "rep": rs[0]["rep"], "n_artworks": len(rs)}
        for f in FEATURES:
            vals = [float(r[f]) for r in rs if r[f] != ""]
            m[f] = sum(vals) / len(vals) if vals else float("nan")
        out[world] = m
    return out


def f_ratio(groups: list[list[float]]) -> tuple[float, float, float]:
    """Between-group vs within-group variance. Returns (F, between_ms, within_ms).

    This is the H1 test in one number: charter effect over replicate noise. With
    three replicates per charter it is badly underpowered, so it is reported as a
    ratio to compare against 1, not as a p-value.
    """
    groups = [[v for v in g if not math.isnan(v)] for g in groups]
    groups = [g for g in groups if g]
    if len(groups) < 2:
        return (float("nan"),) * 3
    all_vals = [v for g in groups for v in g]
    n, k = len(all_vals), len(groups)
    if n <= k:
        return (float("nan"),) * 3
    grand = sum(all_vals) / n
    ss_between = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups)
    ss_within = sum((v - sum(g) / len(g)) ** 2 for g in groups for v in g)
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (n - k)
    if ms_within == 0:
        return (float("inf"), ms_between, 0.0)
    return (ms_between / ms_within, ms_between, ms_within)


# ---------------------------------------------------------------- doctrine tf-idf

def tfidf_vectors(docs: list[list[str]]) -> list[dict[str, float]]:
    n = len(docs)
    df: Counter = Counter()
    for d in docs:
        df.update(set(d))
    vecs = []
    for d in docs:
        tf = Counter(d)
        total = sum(tf.values()) or 1
        vecs.append({w: (c / total) * math.log((1 + n) / (1 + df[w])) + 1e-12
                     for w, c in tf.items()})
    return vecs


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    num = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return num / (na * nb) if na and nb else 0.0


def doctrine_divergence(world_docs: dict[str, tuple[str, list[str]]]) -> dict:
    """Within-charter vs across-charter cosine on adopted doctrines.

    If a charter shapes doctrine, two worlds under the same charter should read
    more alike than two under different charters.
    """
    names = sorted(world_docs)
    docs = [tokenize(" ".join(world_docs[n][1])) for n in names]
    vecs = tfidf_vectors(docs)
    charter_of = {n: n.rsplit("-", 1)[0] for n in names}

    within, across = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            sim = cosine(vecs[i], vecs[j])
            (within if charter_of[names[i]] == charter_of[names[j]] else across).append(sim)
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
    return {"within_mean": mean(within), "across_mean": mean(across),
            "within_n": len(within), "across_n": len(across),
            "gap": mean(within) - mean(across)}


# ---------------------------------------------------------------- outputs

def build_report(worlds: list[World], vocab: dict[str, set[str]], preview: bool) -> dict:
    say(f"\n{C.BOLD}[adherence]{C.RESET} charter vocabulary in reasoning + doctrines", C.CYAN)
    texts = {w.name: world_text(w) for w in worlds}
    blob = {name: (txt[0] + " " + " ".join(txt[1])) for name, txt in texts.items()}

    # Calibrate the vocabularies against charter-free reasoning before scoring.
    control_text = " ".join(t for n, t in blob.items() if n.rsplit("-", 1)[0] == CONTROL)
    if control_text.strip():
        before = {c: len(v) for c, v in vocab.items()}
        vocab = refine_vocab(vocab, control_text)
        say("  vocab after control calibration: " + ", ".join(
            f"{c} {len(vocab[c])}/{before[c]}" for c in sorted(vocab)))
    else:
        say(f"  {C.YELLOW}no control world available — vocabularies uncalibrated{C.RESET}",
            C.YELLOW)

    rates = {name: adherence_rates(t, vocab) for name, t in blob.items()}
    tokens_per_world = {name: len(tokenize(t)) for name, t in blob.items()}
    thin = [n for n, k in tokens_per_world.items() if k < 500]
    if thin:
        say(f"  {C.YELLOW}thin text (<500 tokens), pooled but flagged: "
            f"{', '.join(thin)}{C.RESET}", C.YELLOW)

    # Pool each charter's replicates into one text before scoring, rather than
    # averaging per-replicate rates. A replicate that barely produced any text
    # (a crashed or slow world) otherwise contributes a wild rate with the same
    # weight as a replicate with 100x the reasoning behind it.
    pooled: dict[str, list[str]] = defaultdict(list)
    for name, t in blob.items():
        pooled[name.rsplit("-", 1)[0]].append(t)
    matrix = {ch: adherence_rates(" ".join(ts), vocab) for ch, ts in pooled.items()}

    say(f"\n{C.BOLD}[features]{C.RESET} artwork structure per world", C.CYAN)
    rows = [r for w in worlds for r in artwork_features(w)]
    means = world_means(rows)

    fstats = {}
    for f in FEATURES:
        groups_by_charter: dict[str, list[float]] = defaultdict(list)
        for m in means.values():
            groups_by_charter[m["charter"]].append(m[f])
        fstats[f] = f_ratio(list(groups_by_charter.values()))

    say(f"\n{C.BOLD}[doctrine]{C.RESET} tf-idf cosine within vs across charter", C.CYAN)
    doc = doctrine_divergence(texts) if len(texts) > 1 else {}

    # Lift over the charter-free baseline: how much more does a world use a
    # vocabulary than a world with no charter at all? 1.0x means no effect.
    # Lift is only meaningful when the control baseline is measurable. Below the
    # floor the ratio explodes on a handful of incidental hits, so report nothing
    # rather than a number that looks like a finding.
    base = matrix.get(CONTROL, {})
    LIFT_FLOOR = 0.05  # hits per 1,000 tokens in the control
    lift = {
        ch: {v: (row[v] / base[v] if base.get(v, 0.0) >= LIFT_FLOOR else float("nan"))
             for v in vocab}
        for ch, row in matrix.items()
    }
    return {"matrix": matrix, "lift": lift, "rates": rates, "rows": rows,
            "means": means, "fstats": fstats, "doctrine": doc, "vocab": vocab,
            "preview": preview}


def write_csv(rows: list[dict]) -> None:
    if not rows:
        return
    cols = ["world", "charter", "rep", "version_id", "turn", "html_bytes",
            "n_drawable", "paintable", "n_svg", "n_div", "n_canvas", "animated",
            "distinct_colors"]
    RESULTS.mkdir(parents=True, exist_ok=True)
    tmp = FEATURES_CSV.with_suffix(".csv.tmp")
    with open(tmp, "w") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    tmp.replace(FEATURES_CSV)
    say(f"  wrote {FEATURES_CSV} ({len(rows)} artworks)", C.GREEN)


def write_summary(rep: dict, worlds: list[World], pending: list[World]) -> None:
    charters = sorted(rep["matrix"])
    vocabs = sorted(rep["vocab"])
    lines = ["# Twin worlds — charter divergence\n"]
    if rep["preview"]:
        lines.append("> **PREVIEW — the fleet is still running.** These numbers will move.\n")
    lines += [f"Worlds analysed: {len(worlds)} "
              f"({', '.join(w.name for w in worlds) if worlds else 'none'})\n"]
    if pending:
        lines.append(f"Still running: {', '.join(w.name for w in pending)}\n")

    lines += ["\n## 1. Charter adherence\n",
              "Distinctive charter vocabulary per 1,000 tokens of agent reasoning and",
              "adopted doctrine. Rows are the world's own charter; columns are whose",
              "vocabulary is being counted. If charters bite, the diagonal dominates.",
              "The control has no charter, so it has no column — its row is the",
              "baseline rate at which this vocabulary appears with no charter at all.\n",
              "| world charter | " + " | ".join(vocabs) + " | diagonal / best off-diagonal |",
              "|---" * (len(vocabs) + 2) + "|"]
    for ch in charters:
        row = rep["matrix"][ch]
        cells = []
        for v in vocabs:
            val = f"{row[v]:.2f}"
            if v == ch:
                val = f"**{val}**"
            cells.append(val)
        off = [row[v] for v in vocabs if v != ch]
        ratio = (row[ch] / max(off) if ch in row and off and max(off) > 0
                 else float("nan")) if ch in vocabs else float("nan")
        lines.append(f"| {ch} | " + " | ".join(cells) + " | " +
                     ("—" if math.isnan(ratio) else f"{ratio:.1f}x") + " |")

    lines += ["\n### Lift over the charter-free control\n",
              "Each cell is the row world's rate divided by the control's rate for the",
              "same vocabulary. 1.0x means the charter made no difference to how often",
              "those words appear; the diagonal is the charter's effect on itself.\n",
              "| world charter | " + " | ".join(vocabs) + " |",
              "|---" * (len(vocabs) + 1) + "|"]
    for ch in charters:
        row = rep["lift"].get(ch, {})
        cells = []
        for v in vocabs:
            x = row.get(v, float("nan"))
            txt = "—" if (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}x"
            cells.append(f"**{txt}**" if v == ch else txt)
        lines.append(f"| {ch} | " + " | ".join(cells) + " |")

    lines += ["\n## 2. Art-form divergence\n",
              "One vector per world (mean over its canonical artworks), then",
              "between-charter variance over within-charter variance. F near 1 means",
              "charter groups differ no more than replicates of the same charter —",
              "that is the falsifier for H1.\n",
              "| feature | F (between/within) | MS between | MS within |",
              "|---|---:|---:|---:|"]
    for f in FEATURES:
        F, msb, msw = rep["fstats"][f]
        fmt = lambda x: "—" if (isinstance(x, float) and math.isnan(x)) else f"{x:.3g}"  # noqa: E731
        lines.append(f"| {f} | {fmt(F)} | {fmt(msb)} | {fmt(msw)} |")

    lines += ["\n### Per-world feature means\n",
              "| world | n artworks | " + " | ".join(FEATURES) + " |",
              "|---" * (len(FEATURES) + 2) + "|"]
    for world in sorted(rep["means"]):
        m = rep["means"][world]
        lines.append(f"| {world} | {m['n_artworks']} | " +
                     " | ".join("—" if math.isnan(m[f]) else f"{m[f]:.4g}"
                               for f in FEATURES) + " |")

    d = rep["doctrine"]
    if d:
        lines += ["\n## 3. Doctrine text divergence\n",
                  "TF-IDF cosine between worlds' adopted doctrines.\n",
                  "| comparison | n pairs | mean cosine |", "|---|---:|---:|",
                  f"| same charter, different replicate | {d['within_n']} | {d['within_mean']:.4f} |",
                  f"| different charter | {d['across_n']} | {d['across_mean']:.4f} |",
                  f"| **gap (within − across)** | | **{d['gap']:+.4f}** |"]

    MD_PATH.write_text("\n".join(lines) + "\n")
    say(f"  wrote {MD_PATH}", C.GREEN)


def plot(rep: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    means = rep["means"]
    if not means:
        say("  no artworks yet — skipping plot", C.YELLOW)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8), dpi=160,
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("#fcfcfb")

    # Left: adherence matrix as a heatmap-free grouped bar — the diagonal claim
    # is a comparison of a few numbers, and bars compare better than colour cells.
    charters = sorted(rep["matrix"])
    vocabs = sorted(rep["vocab"])
    width = 0.8 / max(1, len(vocabs))
    for vi, v in enumerate(vocabs):
        xs = [ci + vi * width - 0.4 + width / 2 for ci in range(len(charters))]
        ys = [rep["lift"].get(ch, {}).get(v, float("nan")) for ch in charters]
        ax1.bar(xs, ys, width=width * 0.92, color=CHARTER_COLOR.get(v, "#999"),
                label=v, edgecolor="#fcfcfb", linewidth=0.6)
    ax1.set_xticks(range(len(charters)))
    ax1.set_xticklabels(charters, rotation=20, ha="right")
    ax1.axhline(1.0, color=INK_SOFT, lw=1, ls="--", zorder=1)
    ax1.set_ylabel("rate vs charter-free control (x)", color=INK_SOFT, fontsize=10)
    ax1.set_title("Whose vocabulary each world uses", color=INK, fontsize=11.5,
                  fontweight="bold", loc="left", pad=10)
    ax1.legend(frameon=False, fontsize=8.5, ncol=3, title="vocabulary of",
               title_fontsize=8.5)

    # Right: the feature space. Colour = charter (the hypothesis), marker = rep
    # (the noise). Charter clustering is visible only if colours group.
    for world, m in means.items():
        ax2.scatter(m["html_bytes"], m["n_drawable"],
                    color=CHARTER_COLOR.get(m["charter"], "#999"),
                    marker=REP_MARKER.get(m["rep"], "o"), s=90,
                    edgecolor="#fcfcfb", linewidth=1.2, zorder=3)
    ax2.set_xlabel("mean artwork size (bytes)", color=INK_SOFT, fontsize=10)
    ax2.set_ylabel("mean complete drawable elements", color=INK_SOFT, fontsize=10)
    ax2.set_title("Do worlds cluster by charter, or by chance?", color=INK,
                  fontsize=11.5, fontweight="bold", loc="left", pad=10)
    # Two legends rather than per-point labels: at this stage many worlds sit on
    # identical coordinates, so text labels overplot into an unreadable smear.
    charters_present = sorted({m["charter"] for m in means.values()})
    leg1 = ax2.legend(
        handles=[Line2D([], [], marker="o", ls="", color=CHARTER_COLOR.get(c, "#999"),
                        label=c, markersize=8) for c in charters_present],
        frameon=False, fontsize=8.5, title="charter", title_fontsize=8.5,
        loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=2, handletextpad=0.4)
    ax2.add_artist(leg1)
    ax2.legend(handles=[Line2D([], [], marker=mk, ls="", color=INK_SOFT, label=rp,
                               markersize=7)
                        for rp, mk in sorted(REP_MARKER.items())],
               frameon=False, fontsize=8.5, title="replicate", title_fontsize=8.5,
               loc="lower right", handletextpad=0.4)
    ax2.margins(x=0.12, y=0.22)

    for a in (ax1, ax2):
        a.set_facecolor("#fcfcfb")
        a.spines[["top", "right"]].set_visible(False)
        a.spines[["left", "bottom"]].set_color(GRID)
        a.tick_params(colors=INK_SOFT, labelsize=9, length=3)
        a.grid(axis="y", color=GRID, lw=0.8, alpha=0.7)
        a.set_axisbelow(True)

    title = "Twin worlds: charter effect against replicate noise"
    if rep["preview"]:
        title += "  (PREVIEW — fleet still running)"
    fig.suptitle(title, color=INK, fontsize=14, fontweight="bold", x=0.012,
                 ha="left", y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(PNG_PATH, facecolor=fig.get_facecolor())
    say(f"  wrote {PNG_PATH}", C.GREEN)


# ---------------------------------------------------------------- judged part

def phase_judge(worlds: list[World], n_pairs: int, seed: int, workers: int) -> None:
    """Pairwise art judging across worlds, balanced within/across charter.

    Wired but deliberately gated behind --judge-pairs: this is the only part that
    spends money. All worlds here run the minimal engine, whose artworks render
    reliably, so the round-1 blankness confound does not apply.
    """
    import random
    import time
    from concurrent.futures import ThreadPoolExecutor

    say(f"\n{C.BOLD}[judge]{C.RESET} {n_pairs} pairs x {len(A.JUDGES)} judges "
        f"{C.YELLOW}(this spends money){C.RESET}", C.CYAN)
    keys = A.load_keys()
    missing = [k for k in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY") if k not in keys]
    if missing:
        say(f"  missing keys: {missing}", C.RED)
        sys.exit(1)

    # Collect rendered artworks, tagged with their world and charter.
    pool: list[tuple[str, str, Path]] = []
    for w in worlds:
        for r in artwork_features(w):
            render = w.path / f"renders/version-{r['version_id']}.png"
            if render.exists():
                pool.append((w.name, w.charter, render))
    if len(pool) < 2:
        say("  not enough rendered artworks to judge", C.RED)
        sys.exit(1)
    say(f"  {len(pool)} rendered artworks across {len({p[0] for p in pool})} worlds")

    rng = random.Random(seed)
    want_across = n_pairs // 2
    pairs, seen = [], set()
    guard = 0
    while len(pairs) < n_pairs and guard < n_pairs * 400:
        guard += 1
        a, b = rng.sample(pool, 2)
        want_same = len(pairs) >= want_across
        if (a[1] == b[1]) != want_same:
            continue
        key = frozenset((str(a[2]), str(b[2])))
        if key in seen:
            continue
        seen.add(key)
        pairs.append((a, b))
    say(f"  built {len(pairs)} pairs "
        f"({sum(1 for a, b in pairs if a[1] != b[1])} across-charter)")

    out_path = RESULTS / "twin_worlds_judgments.jsonl"
    tracker = A.CostTracker()
    t0 = time.time()

    def run(item):
        i, (a, b) = item
        slot_a, slot_b = (a, b) if rng.random() < 0.5 else (b, a)
        row = {"pair_index": i, "slot_a_world": slot_a[0], "slot_b_world": slot_b[0],
               "slot_a_charter": slot_a[1], "slot_b_charter": slot_b[1]}
        for judge in A.JUDGES:
            r = dict(row, judge=judge)
            try:
                res = A.judge_pair_with_retry(judge, slot_a[2], slot_b[2], keys)
                win_slot = res["verdict"]["winner"]
                r.update({
                    "ok": True, "winner_slot": win_slot,
                    "winner_world": slot_a[0] if win_slot == "A" else slot_b[0],
                    "winner_charter": slot_a[1] if win_slot == "A" else slot_b[1],
                    "confidence": res["verdict"]["confidence"],
                    "reason": res["verdict"]["reason"],
                    "input_tokens": res["tokens"]["input_tokens"],
                    "output_tokens": res["tokens"]["output_tokens"],
                })
                tracker.add(judge, res["tokens"]["input_tokens"],
                            res["tokens"]["output_tokens"], res["wall_s"])
            except Exception as e:
                tracker.add_error()
                r.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:200]})
            A.append_jsonl(out_path, r)

    with ThreadPoolExecutor(max_workers=workers) as pool_exec:
        list(pool_exec.map(run, enumerate(pairs, 1)))

    wall = time.time() - t0
    for judge, t in tracker.snapshot().items():
        say("  " + A.append_costlog(EXP / "COSTLOG.md", "twin-worlds", judge,
                                    t["calls"], t["in"], t["out"], t["usd"], wall).strip())
    say(f"  total ${tracker.total_usd():.4f}, {tracker.errors} errors -> {out_path}",
        C.GREEN)


# ---------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fleet-dir", required=True, type=Path)
    p.add_argument("--charters-dir", type=Path, default=CHARTERS_DIR)
    p.add_argument("--allow-incomplete", action="store_true",
                   help="preview using worlds that are still running")
    p.add_argument("--judge-pairs", type=int, default=0,
                   help="run pairwise art judging (SPENDS MONEY; 0 = off)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--seed", type=int, default=46)
    args = p.parse_args()

    say(f"\n{C.BOLD}[fleet]{C.RESET} {args.fleet_dir}", C.CYAN)
    worlds = discover_worlds(args.fleet_dir)
    if not worlds:
        say(f"  no worlds found under {args.fleet_dir}", C.RED)
        sys.exit(1)
    say(f"  {len(worlds)} world(s): "
        f"{len({w.charter for w in worlds})} charters x "
        f"{len({w.rep for w in worlds})} replicates")

    selected = select_worlds(worlds, args.allow_incomplete)
    if not selected:
        say("  nothing analysable yet — no world has a COMPLETE marker. "
            "Re-run later, or pass --allow-incomplete for a preview.", C.YELLOW)
        sys.exit(0)
    say(f"  analysing {C.GREEN}{len(selected)}{C.RESET} world(s)")

    vocab = load_charter_vocab(args.charters_dir)
    say(f"  charter vocabularies: " +
        ", ".join(f"{c} ({len(v)})" for c, v in sorted(vocab.items())))

    rep = build_report(selected, vocab, preview=args.allow_incomplete)
    write_csv(rep["rows"])
    write_summary(rep, selected, [w for w in worlds if not w.complete])
    plot(rep)

    say(f"\n{C.BOLD}[adherence matrix]{C.RESET} rows = world charter, "
        f"cols = vocabulary", C.CYAN)
    vocabs = sorted(vocab)
    say("  " + " " * 12 + " ".join(f"{v[:8]:>9}" for v in vocabs))
    for ch in sorted(rep["matrix"]):
        cells = []
        for v in vocabs:
            val = rep["matrix"][ch][v]
            cells.append(f"{C.GREEN}{val:>9.2f}{C.RESET}" if v == ch else f"{val:>9.2f}")
        say(f"  {ch:>12}" + " ".join(cells))

    say(f"\n{C.BOLD}[lift over control]{C.RESET} 1.00x = charter made no difference",
        C.CYAN)
    say("  " + " " * 12 + " ".join(f"{v[:8]:>9}" for v in vocabs))
    for ch in sorted(rep["lift"]):
        cells = []
        for v in vocabs:
            x = rep["lift"][ch].get(v, float("nan"))
            txt = "—" if (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}x"
            cells.append(f"{C.GREEN}{txt:>9}{C.RESET}" if v == ch else f"{txt:>9}")
        say(f"  {ch:>12}" + " ".join(cells))

    say(f"\n{C.BOLD}[F ratios]{C.RESET} between-charter / within-charter variance", C.CYAN)
    for f in FEATURES:
        F, _, _ = rep["fstats"][f]
        say(f"  {f:>16}: " + ("—" if math.isnan(F) else f"{F:.2f}"))

    if rep["doctrine"]:
        d = rep["doctrine"]
        say(f"\n{C.BOLD}[doctrine cosine]{C.RESET} within {d['within_mean']:.4f} "
            f"vs across {d['across_mean']:.4f} (gap {d['gap']:+.4f})", C.CYAN)

    if args.judge_pairs:
        phase_judge(selected, args.judge_pairs, args.seed, args.workers)
    else:
        say(f"\n{C.DIM}judging not run. Add --judge-pairs N to spend money.{C.RESET}")


if __name__ == "__main__":
    main()
