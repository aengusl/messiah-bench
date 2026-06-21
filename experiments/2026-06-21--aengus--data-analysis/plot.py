#!/usr/bin/env python3
"""
Generate figures from data/metrics.json + data/art_all.json.
Run: uv run --with matplotlib --with numpy python plot.py
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
M = json.load(open(HERE / "data" / "metrics.json"))
ART = json.load(open(HERE / "data" / "art_all.json"))
PLOTS = HERE / "plots"; PLOTS.mkdir(exist_ok=True)

ORDER = [v for v in ["v1", "v2", "v3", "v4", "v5", "v6"] if v in M]
# runs where scripture_board logged real reasoning (v1-v3 logged only founding text)
REASONING_OK = [v for v in ["v4", "v5", "v6"] if v in M]
# v4 is heavily rate-limited -> flag
RATE_LIMITED = {"v4"}

plt.rcParams.update({
    "figure.dpi": 130, "font.size": 11, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    "axes.titleweight": "bold", "figure.autolayout": True,
})
C = {"war": "#c0392b", "soul": "#2c7fb8", "plague": "#7a5195",
     "exit": "#bc5090", "found": "#bdbdbd", "surv": "#2a9d8f",
     "defect": "#e76f51", "loyal": "#264653", "accent": "#e9c46a"}


def lbl(v):
    return v + ("*" if v in RATE_LIMITED else "")


# ---------- FIG 1: convergence to monoculture ----------
fig, ax = plt.subplots(figsize=(8, 4.5))
founded = [M[v]["n_religions_founded"] for v in ORDER]
surv = [M[v]["distinct_surv_religions"] for v in ORDER]
x = np.arange(len(ORDER)); w = 0.38
ax.bar(x - w/2, founded, w, label="religions founded", color=C["found"])
ax.bar(x + w/2, surv, w, label="distinct religions among survivors", color=C["surv"])
for i, (f, s) in enumerate(zip(founded, surv)):
    ax.text(i - w/2, f + 2, str(f), ha="center", fontsize=9)
    ax.text(i + w/2, s + 2, str(s), ha="center", fontsize=9, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels([lbl(v) for v in ORDER])
ax.set_ylabel("number of religions")
ax.set_title("Religions collapse toward monoculture")
ax.legend(frameon=False)
ax.text(0.5, -0.18, "* v4 heavily rate-limited (≈39% of agents ended on fallback output)",
        transform=ax.transAxes, ha="center", fontsize=8, color="gray")
fig.savefig(PLOTS / "01_convergence.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 2: top survivor religion share ----------
fig, ax = plt.subplots(figsize=(7.5, 4))
share = [100 * M[v]["top_surv_religion_share"] for v in ORDER]
bars = ax.bar([lbl(v) for v in ORDER], share, color=C["surv"])
ax.axhline(100, ls="--", color="gray", lw=1)
for b, s in zip(bars, share):
    ax.text(b.get_x()+b.get_width()/2, s+1, f"{s:.0f}%", ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("% of survivors in largest religion")
ax.set_ylim(0, 110)
ax.set_title("How dominant is the winning faith at the end?")
fig.savefig(PLOTS / "02_winner_share.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 3: death causes stacked ----------
fig, ax = plt.subplots(figsize=(8.5, 4.5))
cats = ["killed in war", "soul depletion", "plague", "exit penalty"]
colors = [C["war"], C["soul"], C["plague"], C["exit"]]
bottom = np.zeros(len(ORDER))
for cat, col in zip(cats, colors):
    vals = [M[v]["death_causes"].get(cat, 0) for v in ORDER]
    ax.bar([lbl(v) for v in ORDER], vals, bottom=bottom, label=cat, color=col)
    bottom += np.array(vals)
ax.set_ylabel("deaths")
ax.set_title("What kills agents? War vs. economic starvation vs. plague")
ax.legend(frameon=False, ncol=2)
fig.savefig(PLOTS / "03_death_causes.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 4: messiah survival + defection ----------
fig, ax = plt.subplots(figsize=(8.5, 4.5))
nm = [M[v]["n_messiahs"] for v in ORDER]
alive = [M[v]["messiahs_alive"] for v in ORDER]
defect = [M[v]["messiahs_defected"] for v in ORDER]
x = np.arange(len(ORDER)); w = 0.27
ax.bar(x - w, nm, w, label="messiahs (total)", color=C["found"])
ax.bar(x, alive, w, label="messiahs survived", color=C["loyal"])
ax.bar(x + w, defect, w, label="messiahs that defected\nfrom own founded religion", color=C["defect"])
for i in range(len(ORDER)):
    for off, val in [(-w, nm[i]), (0, alive[i]), (w, defect[i])]:
        ax.text(i+off, val+0.15, str(val), ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([lbl(v) for v in ORDER])
ax.set_ylabel("count")
ax.set_title("Messiahs: loyalty is lethal — survivors defect")
ax.legend(frameon=False, ncol=3, fontsize=8)
fig.savefig(PLOTS / "04_messiah_defection.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 5: edits vs final bytes (complexity decoupled) ----------
fig, ax = plt.subplots(figsize=(7.5, 5.5))
markers = {"v3": "o", "v4": "s", "v5": "^", "v6": "D"}
for v in [x for x in ORDER if M[x]["art_model"] == "shared-canvas"]:
    arr = ART[v]
    e = [a["edits"] for a in arr]; b = [a["bytes"] for a in arr]
    ax.scatter(e, b, s=22, alpha=0.6, marker=markers.get(v, "o"), label=v)
ax.set_xlabel("number of edits (collaborative churn)")
ax.set_ylabel("final HTML size (bytes) — complexity proxy")
ax.set_title("Edit count ≠ art complexity\n(massively edited pieces are often tiny)")
ax.legend(frameon=False, title="sim")
fig.savefig(PLOTS / "05_edits_vs_bytes.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 6: edits vs unique contributors (collaboration shape) ----------
fig, ax = plt.subplots(figsize=(7.5, 5.5))
for v in [x for x in ORDER if M[x]["art_model"] == "shared-canvas"]:
    arr = ART[v]
    e = [a["edits"] for a in arr]; c = [a["contributors"] for a in arr]
    ax.scatter(e, c, s=22, alpha=0.6, marker=markers.get(v, "o"), label=v)
mx = max((a["edits"] for v in ORDER if M[v]["art_model"]=="shared-canvas" for a in ART[v]), default=1)
ax.plot([0, mx], [0, mx], ls="--", color="gray", lw=1, label="1 edit = 1 unique author")
ax.set_xlabel("number of edits")
ax.set_ylabel("unique contributors")
ax.set_title("Sacraments are mass-collaborative canvases\n(near the 1:1 line = nearly every edit a different agent)")
ax.legend(frameon=False, title="sim")
fig.savefig(PLOTS / "06_collaboration.png", bbox_inches="tight"); plt.close(fig)

# ---------- FIG 7: aesthetic reasoning (only where logged) ----------
fig, ax = plt.subplots(figsize=(7.5, 4.5))
av = REASONING_OK
total = [M[v]["aesth_count"] for v in av]
joinc = [M[v]["aesth_join_count"] for v in av]
x = np.arange(len(av)); w = 0.38
ax.bar(x - w/2, total, w, label="entries with aesthetic language", color=C["accent"])
ax.bar(x + w/2, joinc, w, label="aesthetic + join/convert verb", color=C["defect"])
for i in range(len(av)):
    ax.text(i-w/2, total[i]+10, str(total[i]), ha="center", fontsize=8)
    ax.text(i+w/2, joinc[i]+10, str(joinc[i]), ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([lbl(v) for v in av])
ax.set_ylabel("reasoning entries")
ax.set_title("Agents reason about beauty when affiliating\n(v1–v3 excluded: logged only founding text, not reasoning)")
ax.legend(frameon=False, fontsize=8)
fig.savefig(PLOTS / "07_aesthetic_reasoning.png", bbox_inches="tight"); plt.close(fig)

print("wrote figures:")
for p in sorted(PLOTS.glob("0*.png")):
    print("  ", p.name)
