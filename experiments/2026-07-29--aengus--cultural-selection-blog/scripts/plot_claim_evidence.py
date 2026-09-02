"""Build claim-first figures used in the public essay."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
GROUND, INK, MUTED, LINE = "#f3f0e8", "#1e211d", "#66675f", "#cbc5b7"
RUST, TEAL = "#9b3f28", "#245c62"


def save(fig, name):
    fig.savefig(RESULTS / name, dpi=190, facecolor=GROUND, bbox_inches="tight")
    plt.close(fig)


def culture_signal():
    labels = ["Artwork structure", "Artwork length", "Palette size"]
    values = [449, 212, 90]  # audited v2 results
    fig, ax = plt.subplots(figsize=(10, 5.8), facecolor=GROUND)
    ax.set_facecolor(GROUND)
    y = np.arange(3)
    ax.hlines(y, 1, values, color=LINE, linewidth=3)
    ax.scatter(values, y, s=170, color=RUST, edgecolor=GROUND, linewidth=2, zorder=3)
    ax.axvline(1, color=INK, linewidth=1.2, alpha=.75)
    for yi, value in zip(y, values):
        ax.text(value * 1.12, yi, f"{value}×", va="center", fontsize=18,
                fontweight="bold", color=RUST)
    ax.text(1, 2.62, "repeat-run noise", ha="center", va="top", fontsize=9, color=MUTED)
    ax.set_xscale("log")
    ax.set_xlim(.65, 900)
    ax.set_yticks(y, labels, fontsize=13, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Between-culture variation ÷ variation among repeated worlds",
                  fontsize=11, color=MUTED, labelpad=13)
    ax.tick_params(axis="x", colors=MUTED)
    ax.grid(axis="x", color=LINE, linewidth=.7, alpha=.65)
    ax.spines[:].set_visible(False)
    fig.suptitle("Culture differences dwarfed repeat-run noise", x=.11, y=.98,
                 ha="left", fontsize=21, fontweight="bold", color=INK)
    fig.text(.11, .90, "The same model varied far more between inherited traditions than within them.",
             fontsize=11, color=MUTED)
    fig.text(.11, .015,
             "18 worlds: six cultures × three repeats. Descriptive ratios; creed and founding image varied together.",
             fontsize=9, color=MUTED)
    fig.subplots_adjust(left=.25, right=.91, top=.79, bottom=.22)
    save(fig, "culture_signal.png")


def revision_regimes():
    raw = json.loads((RESULTS / "_depth_breadth_raw.json").read_text())
    charters = ["botanical", "brutalist", "cave", "psychedelic", "quilt", "ukiyo"]
    depth, variation = [], []
    for charter in charters:
        worlds = raw["charter_stats"][charter]["reps"]
        depth.append([raw["world_stats"][w]["mean_depth"] for w in worlds])
        variation.append([100 * raw["world_stats"][w]["mean_cv"] for w in worlds])
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 6.7), sharey=True, facecolor=GROUND)
    highlights = {"cave": RUST, "psychedelic": TEAL}
    panels = [(depth, "How long lineages kept revising", "Accepted versions per lineage"),
              (variation, "How widely the artworks varied", "Relative variation in size, structure and palette (%)")]
    for ax, (data, title, xlabel) in zip(axes, panels):
        ax.set_facecolor(GROUND)
        for i, (charter, pair) in enumerate(zip(charters, data)):
            color = highlights.get(charter, "#87877f")
            ax.plot(pair, [i, i], color=color, linewidth=2.4, alpha=.55)
            ax.scatter(pair, [i, i], s=82, color=color, edgecolor=GROUND, linewidth=1.5, zorder=2)
        ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=INK, pad=12)
        ax.set_xlabel(xlabel, fontsize=10, color=MUTED, labelpad=10)
        ax.grid(axis="x", color=LINE, linewidth=.7, alpha=.7)
        ax.tick_params(axis="x", colors=MUTED)
        ax.tick_params(axis="y", length=0)
        ax.spines[:].set_visible(False)
    axes[0].set_yticks(np.arange(6), [c.title() for c in charters], fontsize=11, color=INK)
    axes[0].invert_yaxis()
    axes[0].annotate("shallow", (3.0, 2), xytext=(4.5, 2.35), color=RUST, fontsize=9,
                     arrowprops={"arrowstyle": "-", "color": RUST})
    axes[1].annotate("broad", (59.4, 3), xytext=(39, 3.4), color=TEAL, fontsize=9,
                     arrowprops={"arrowstyle": "-", "color": TEAL})
    fig.suptitle("Two cultures occupied clearly different revision regimes", x=.10, y=.99,
                 ha="left", fontsize=20, fontweight="bold", color=INK)
    fig.text(.10, .925, "The extremes repeat; the four cultures in the middle overlap.", fontsize=11, color=MUTED)
    fig.text(.10, .015,
             "Two dots = two worlds per culture. Exploratory: n=12 worlds; cave-r1 contains only five accepted works.",
             fontsize=9, color=MUTED)
    fig.subplots_adjust(left=.18, right=.98, top=.82, bottom=.18, wspace=.17)
    save(fig, "revision_regimes.png")


if __name__ == "__main__":
    culture_signal()
    revision_regimes()
