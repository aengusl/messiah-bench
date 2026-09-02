"""Build the single quantitative figure used in the public essay."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
GROUND, INK, MUTED, LINE = "#f3f0e8", "#1e211d", "#66675f", "#cbc5b7"
RUST, PALE = "#9b3f28", "#e4ded2"


def blind_classification():
    cultures = ["Ascetic", "Baroque", "Nihilist", "Ancestor", "Futurist", "Control"]
    matrix = np.eye(6, dtype=int) * 6
    fig = plt.figure(figsize=(12, 7.2), facecolor=GROUND)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.5, .72], left=.10, right=.96,
                            top=.76, bottom=.20, wspace=.30)

    ax = fig.add_subplot(grid[0, 0])
    ax.set_facecolor(GROUND)
    ax.imshow(matrix > 0, cmap=ListedColormap([PALE, RUST]), vmin=0, vmax=1,
              aspect="equal")
    for row in range(6):
        for col in range(6):
            value = matrix[row, col]
            ax.text(col, row, str(value), ha="center", va="center",
                    color="white" if value else MUTED, fontsize=13,
                    fontweight="bold" if value else "normal")
    ax.set_xticks(range(6), cultures, rotation=40, ha="right", fontsize=10, color=INK)
    ax.set_yticks(range(6), cultures, fontsize=10, color=INK)
    ax.set_xlabel("Classifier's answer", fontsize=11, color=MUTED, labelpad=10)
    ax.set_ylabel("Culture that made the artwork", fontsize=11, color=MUTED, labelpad=10)
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which="minor", color=GROUND, linewidth=3)
    ax.tick_params(which="both", length=0)
    ax.spines[:].set_visible(False)

    score = fig.add_subplot(grid[0, 1])
    score.set_facecolor(GROUND)
    score.barh([1, 0], [36, 6], color=[RUST, PALE], height=.52)
    score.text(34.8, 1, "36 / 36", ha="right", va="center", color="white",
               fontsize=17, fontweight="bold")
    score.text(7.2, 0, "6 / 36", ha="left", va="center", color=MUTED,
               fontsize=14, fontweight="bold")
    score.set_yticks([1, 0], ["Observed", "Random guessing"], fontsize=11, color=INK)
    score.set_xlim(0, 38)
    score.set_xlabel("Correct answers", fontsize=11, color=MUTED, labelpad=10)
    score.set_xticks([0, 6, 12, 18, 24, 30, 36])
    score.tick_params(axis="x", colors=MUTED)
    score.tick_params(axis="y", length=0)
    score.grid(axis="x", color=LINE, linewidth=.7)
    score.spines[:].set_visible(False)

    fig.suptitle("Every anonymous artwork was matched to its culture", x=.10, y=.94,
                 ha="left", fontsize=22, fontweight="bold", color=INK)
    fig.text(.10, .86, "A fresh classifier sorted 36 shuffled works into six known cultural labels.",
             fontsize=12, color=MUTED)
    fig.text(.10, .07,
             "Six works per culture: two from each of three independently run worlds. The classifier saw art, not filenames or world labels.",
             fontsize=9.5, color=MUTED)
    fig.text(.10, .035,
             "The test shows a visible culture signature; creed and founding image changed together, so it cannot separate their effects.",
             fontsize=9.5, color=MUTED)
    fig.savefig(RESULTS / "blind_classification.png", dpi=190, facecolor=GROUND,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    blind_classification()
