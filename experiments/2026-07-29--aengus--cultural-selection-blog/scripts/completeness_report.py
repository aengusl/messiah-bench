#!/usr/bin/env python3
"""Source-level completeness across all three corpora. No rendering, no API calls.

    uv run scripts/completeness_report.py

Round 1 tried to score these artworks aesthetically and mostly measured which of
them were blank. This measures the blankness directly, at the source level, over
every artwork rather than a 300-item sample: was the HTML cut off mid-tag, and
does it contain anything that would paint?

Writes results/completeness.csv, results/completeness_summary.md, and
results/completeness_over_time.png.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXP / "src"))

import artlib as A  # noqa: E402
from artlib import C, say  # noqa: E402

RESULTS = EXP / "results"
CSV_PATH = RESULTS / "completeness.csv"
MD_PATH = RESULTS / "completeness_summary.md"
PNG_PATH = RESULTS / "completeness_over_time.png"

MINIMAL_ROOT = A.SOURCES["minimal"]["root"]
N_BINS = 10

# Categorical slots 1-3 of the validated default palette (light mode).
# Validated with scripts/validate_palette.js: all checks pass; the aqua carries a
# contrast WARN against the surface, so every series is also directly labelled.
REGIME_COLOR = {"v7": "#2a78d6", "v8": "#eb6834", "minimal": "#1baf7a"}
REGIME_LABEL = {
    "v7": "v7 — locked messiahs",
    "v8": "v8 — PR-governed art",
    "minimal": "minimal — proposal/adopt",
}
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#dcdcd8"


# ---------------------------------------------------------------- stats helpers

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval — behaves at p near 0 or 1, where normal-approx doesn't.

    These proportions sit at the extremes (minimal is 100% paintable, late v7 near
    0%), which is exactly where the textbook interval produces bounds outside
    [0, 1].
    """
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    mid = len(s) // 2
    return float(s[mid]) if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


# ---------------------------------------------------------------- row building

def analyse(art: A.Artwork, group: str) -> dict:
    c = A.source_content(art.html)
    return {
        "art_id": art.art_id,
        "regime": art.regime,
        "group": group,
        "turn": art.turn,
        "religion": art.religion,
        "truncated": int(c["source_truncated"]),
        "n_drawable": c["foreground_elements"],
        "paintable": int(c["has_paintable_content"]),
        "html_bytes": len(art.html),
    }


def load_minimal_proposals() -> list[A.Artwork]:
    """The 339 proposal files, tagged accepted or rejected from the event log.

    versions.jsonl only records what survived, so the adoption outcome has to come
    from events.jsonl: `accepted` and `rejected` events both carry a proposal_id.
    """
    outcome: dict[str, str] = {}
    turn_of: dict[str, int] = {}
    religion_of: dict[str, str] = {}
    with open(MINIMAL_ROOT / "events.jsonl") as fh:
        for line in fh:
            d = json.loads(line)
            t, pid = d.get("type"), d.get("proposal_id")
            if pid is None:
                continue
            pid = str(pid)
            if t == "proposal":
                turn_of[pid] = int(d.get("turn", 0))
                religion_of[pid] = str(d.get("religion_id", "?"))
            elif t in ("accepted", "rejected"):
                outcome[pid] = t

    arts = []
    for path in sorted((MINIMAL_ROOT / "artworks").glob("proposal-*.html")):
        pid = path.stem.split("-", 1)[1]
        arts.append(
            A.Artwork(
                art_id=f"minimal-proposal-{pid}",
                regime="minimal",
                religion=religion_of.get(pid, "?"),
                lineage=religion_of.get(pid, "?"),
                version=int(pid) if pid.isdigit() else 0,
                turn=turn_of.get(pid, 0),
                html=path.read_text(),
                source=str(path),
            )
        )
    return arts, outcome


def build_rows() -> list[dict]:
    rows: list[dict] = []
    say(f"\n{C.BOLD}[load]{C.RESET} source analysis over all three corpora", C.CYAN)
    for regime in A.REGIMES:
        arts = A.load_regime(regime)
        rows.extend(analyse(a, "canon") for a in arts)
        say(f"  {regime:>8}: {len(arts):>5} artworks")

    proposals, outcome = load_minimal_proposals()
    for a in proposals:
        pid = a.art_id.rsplit("-", 1)[1]
        row = analyse(a, f"proposal_{outcome.get(pid, 'unresolved')}")
        rows.append(row)
    say(f"  {'minimal':>8}: {len(proposals):>5} proposals "
        f"({sum(1 for v in outcome.values() if v == 'accepted')} accepted, "
        f"{sum(1 for v in outcome.values() if v == 'rejected')} rejected)")
    return rows


# ---------------------------------------------------------------- outputs

CSV_COLS = ["art_id", "regime", "group", "turn", "religion",
            "truncated", "n_drawable", "paintable", "html_bytes"]


def write_csv(rows: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tmp = CSV_PATH.with_suffix(".csv.tmp")
    with open(tmp, "w") as fh:
        fh.write(",".join(CSV_COLS) + "\n")
        for r in rows:
            fh.write(",".join(str(r[c]) for c in CSV_COLS) + "\n")
    tmp.replace(CSV_PATH)
    say(f"  wrote {CSV_PATH} ({len(rows)} rows)", C.GREEN)


def decile_series(rows: list[dict]) -> tuple[list, list, list]:
    """Per time-decile: paintable fraction with CI, median drawable count."""
    if not rows:
        return [], [], []
    lo = min(r["turn"] for r in rows)
    hi = max(r["turn"] for r in rows)
    bins: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        bins[A.time_decile(r["turn"], lo, hi, N_BINS)].append(r)

    xs, paint, drawable = [], [], []
    for b in sorted(bins):
        sub = bins[b]
        xs.append(sum(r["turn"] for r in sub) / len(sub))
        paint.append(wilson(sum(r["paintable"] for r in sub), len(sub)) + (len(sub),))
        drawable.append(median([r["n_drawable"] for r in sub]))
    return xs, paint, drawable


def write_summary(rows: list[dict]) -> dict:
    canon = [r for r in rows if r["group"] == "canon"]
    lines = ["# Completeness of generated artwork — all corpora\n",
             "Source-level analysis: was the HTML cut off mid-tag, and does it contain",
             "any element that would actually paint? No rendering involved.\n",
             "`n_drawable` counts complete foreground elements, excluding `<defs>`,",
             "`<style>`, half-written tags, and full-bleed background rects.\n",
             "## Per regime (canonical artworks)\n",
             "| regime | n | % truncated | % nothing paintable | median drawable elements | median bytes |",
             "|---|---:|---:|---:|---:|---:|"]

    summary = {}
    for regime in A.REGIMES:
        sub = [r for r in canon if r["regime"] == regime]
        if not sub:
            continue
        n = len(sub)
        trunc = 100 * sum(r["truncated"] for r in sub) / n
        blank = 100 * (1 - sum(r["paintable"] for r in sub) / n)
        summary[regime] = {"n": n, "truncated_pct": trunc, "blank_pct": blank}
        lines.append(
            f"| {regime} | {n} | {trunc:.1f}% | {blank:.1f}% | "
            f"{median([r['n_drawable'] for r in sub]):.0f} | "
            f"{median([r['html_bytes'] for r in sub]):.0f} |"
        )

    lines += ["\n## Trend over each run's lifetime\n",
              "Paintable fraction per time decile (Wilson 95% CI).\n",
              "| regime | decile | mean turn | n | % paintable | 95% CI |",
              "|---|---:|---:|---:|---:|---|"]
    for regime in A.REGIMES:
        xs, paint, _ = decile_series([r for r in canon if r["regime"] == regime])
        for i, (x, (p, lo, hi, n)) in enumerate(zip(xs, paint)):
            lines.append(f"| {regime} | {i} | {x:.0f} | {n} | {100*p:.1f}% | "
                         f"{100*lo:.1f}–{100*hi:.1f}% |")

    # The adoption gate: does the accept/reject decision track completeness?
    lines += ["\n## Does the adoption gate filter on completeness?\n",
              "The minimal run is the only one with an explicit accept/reject step,",
              "so it is the only place this mechanism can be tested directly.\n",
              "| group | n | % truncated | % nothing paintable | median drawable |",
              "|---|---:|---:|---:|---:|"]
    gate = {}
    for group in ("proposal_accepted", "proposal_rejected", "proposal_unresolved", "canon"):
        sub = [r for r in rows if r["group"] == group and r["regime"] == "minimal"]
        if not sub:
            continue
        n = len(sub)
        gate[group] = {
            "n": n,
            "truncated_pct": 100 * sum(r["truncated"] for r in sub) / n,
            "blank_pct": 100 * (1 - sum(r["paintable"] for r in sub) / n),
            "median_drawable": median([r["n_drawable"] for r in sub]),
        }
        lines.append(f"| {group} | {n} | {gate[group]['truncated_pct']:.1f}% | "
                     f"{gate[group]['blank_pct']:.1f}% | {gate[group]['median_drawable']:.0f} |")

    MD_PATH.write_text("\n".join(lines) + "\n")
    say(f"  wrote {MD_PATH}", C.GREEN)
    return {"regimes": summary, "gate": gate}


def plot(rows: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    canon = [r for r in rows if r["group"] == "canon"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2), dpi=160, sharex="col")
    fig.patch.set_facecolor("#fcfcfb")

    for col, regime in enumerate(A.REGIMES):
        sub = [r for r in canon if r["regime"] == regime]
        xs, paint, drawable = decile_series(sub)
        color = REGIME_COLOR[regime]

        # Row 1 — paintable fraction. Separate row rather than a second y-axis:
        # two measures of different scale never share an axis.
        ax = axes[0][col]
        ys = [100 * p[0] for p in paint]
        lo = [100 * p[1] for p in paint]
        hi = [100 * p[2] for p in paint]
        # Whiskers, not a filled band. The minimal run has ~9 artworks per decile
        # sitting at 100%, so its Wilson interval reaches down past 20% -- as a
        # shaded region that reads as a dip in the data, which is the opposite of
        # what it means. Whiskers show the same uncertainty without drawing a
        # shape the eye interprets as a series.
        # The Wilson interval is centred on its own shrunk estimate, not on p, so
        # at p = 100% the upper bound sits *below* the point. Clamp to 0 rather
        # than letting matplotlib reject a negative whisker.
        ax.errorbar(xs, ys,
                    yerr=[[max(0.0, y - l) for y, l in zip(ys, lo)],
                          [max(0.0, h - y) for y, h in zip(ys, hi)]],
                    fmt="none", ecolor=color, elinewidth=1.4, capsize=3, alpha=0.75)
        ax.plot(xs, ys, "-o", color=color, lw=2, ms=5,
                markeredgecolor="#fcfcfb", markeredgewidth=1.2)
        ax.set_ylim(-4, 108)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_title(REGIME_LABEL[regime], color=INK, fontsize=11.5, pad=10,
                     fontweight="bold", loc="left")
        if ys:  # direct label — the aqua fails contrast against the surface
            ax.annotate(f"{ys[-1]:.0f}%", (xs[-1], ys[-1]), textcoords="offset points",
                        xytext=(6, 0), color=INK, fontsize=10, fontweight="bold",
                        va="center")
        if col == 0:
            ax.set_ylabel("artworks with paintable\ncontent (%)", color=INK_SOFT, fontsize=10)

        # Row 2 — median complete drawable elements.
        ax2 = axes[1][col]
        ax2.plot(xs, drawable, "-o", color=color, lw=2, ms=5,
                 markeredgecolor="#fcfcfb", markeredgewidth=1.2)
        ax2.set_ylim(bottom=-0.4)
        # Element counts are integers; half-integer ticks are meaningless here.
        ax2.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        if drawable:
            ax2.annotate(f"{drawable[-1]:.0f}", (xs[-1], drawable[-1]),
                         textcoords="offset points", xytext=(6, 0), color=INK,
                         fontsize=10, fontweight="bold", va="center")
        if col == 0:
            ax2.set_ylabel("median complete\ndrawable elements", color=INK_SOFT, fontsize=10)
        ax2.set_xlabel("simulation turn", color=INK_SOFT, fontsize=10)

        for a in (ax, ax2):
            a.set_facecolor("#fcfcfb")
            a.spines[["top", "right"]].set_visible(False)
            a.spines[["left", "bottom"]].set_color(GRID)
            a.tick_params(colors=INK_SOFT, labelsize=9, length=3)
            a.grid(axis="y", color=GRID, lw=0.8, alpha=0.7)
            a.set_axisbelow(True)

    fig.suptitle("Two runs empty out as they go; the third never does — "
                 "the gap between regimes is completeness, not taste",
                 color=INK, fontsize=14, fontweight="bold", x=0.012, ha="left", y=0.985)
    fig.text(0.012, 0.925,
             "Every artwork in all three runs, binned into ten equal spans of each run's "
             "lifetime. Whiskers are Wilson 95% intervals — wide for the minimal run, "
             "which has only 86 artworks in total.",
             color=INK_SOFT, fontsize=10, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(PNG_PATH, facecolor=fig.get_facecolor())
    say(f"  wrote {PNG_PATH}", C.GREEN)


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    stats = write_summary(rows)
    plot(rows)

    say(f"\n{C.BOLD}[summary]{C.RESET}", C.CYAN)
    say(f"  {'regime':>8} {'n':>6} {'%truncated':>12} {'%nothing paintable':>20}")
    for regime, s in stats["regimes"].items():
        say(f"  {regime:>8} {s['n']:>6} {s['truncated_pct']:>11.1f}% "
            f"{s['blank_pct']:>19.1f}%")

    say(f"\n{C.BOLD}[adoption gate — minimal run]{C.RESET}", C.CYAN)
    say(f"  {'group':>22} {'n':>5} {'%truncated':>12} {'%nothing paintable':>20} {'med drawable':>13}")
    for group, g in stats["gate"].items():
        say(f"  {group:>22} {g['n']:>5} {g['truncated_pct']:>11.1f}% "
            f"{g['blank_pct']:>19.1f}% {g['median_drawable']:>13.0f}")


if __name__ == "__main__":
    main()
