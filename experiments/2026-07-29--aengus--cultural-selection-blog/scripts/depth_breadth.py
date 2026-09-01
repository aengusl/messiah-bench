"""Describe accepted-revision depth and visual breadth in the new fleet.

Run from the repository root with:
    uv run --project experiments/2026-07-29--aengus--cultural-selection-blog \
      python experiments/2026-07-29--aengus--cultural-selection-blog/scripts/depth_breadth.py
"""

import json, csv, math
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / ".." / ".." / "outputs" / "2026-08-08-new-aesthetics"
OUT = OUT.resolve()
FEATURES = BASE / "results" / "twin_worlds_features.csv"

worlds = sorted([p.name for p in OUT.iterdir() if p.is_dir()])

# --- load features per world for dispersion stats ---
feat_rows = defaultdict(list)
with open(FEATURES) as f:
    for row in csv.DictReader(f):
        feat_rows[row["world"]].append(row)

def cv(vals):
    vals = [float(v) for v in vals]
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    if m == 0:
        return None
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return (var ** 0.5) / m

world_stats = {}
for w in worlds:
    vpath = OUT / w / "versions.jsonl"
    versions = [json.loads(l) for l in open(vpath)]
    canonical = [v for v in versions if v.get("status") == "canonical"]

    # lineage: chase parent_version_id chains, restricted to canonical versions.
    # A "lineage" = a religion_id (each seed religion starts one lineage; revisions
    # to a canonical version increase its depth but do not start a new lineage).
    by_religion = defaultdict(list)
    for v in canonical:
        by_religion[v["religion_id"]].append(v)

    depths = []
    for rid, vs in by_religion.items():
        vs_sorted = sorted(vs, key=lambda v: v["id"])
        depths.append(len(vs_sorted))  # number of canonical versions accepted in this lineage

    n_lineages = len(by_religion)  # breadth: distinct lineages reaching canonical status
    mean_depth = sum(depths) / len(depths) if depths else 0.0
    max_depth = max(depths) if depths else 0

    rows = feat_rows[w]
    cv_bytes = cv([r["html_bytes"] for r in rows])
    cv_drawable = cv([r["n_drawable"] for r in rows])
    cv_colors = cv([r["distinct_colors"] for r in rows])
    cvs = [x for x in (cv_bytes, cv_drawable, cv_colors) if x is not None]
    mean_cv = sum(cvs) / len(cvs) if cvs else None

    world_stats[w] = dict(
        n_canonical=len(canonical),
        n_total_versions=len(versions),
        n_lineages=n_lineages,
        mean_depth=mean_depth,
        max_depth=max_depth,
        cv_html_bytes=cv_bytes,
        cv_n_drawable=cv_drawable,
        cv_distinct_colors=cv_colors,
        mean_cv=mean_cv,
        n_artworks_features=len(rows),
    )

for w, s in world_stats.items():
    print(w, s)

# --- charter-level pooling (rep-level average and pooled) ---
charters = sorted(set(w.split("-r")[0] for w in worlds))
charter_stats = {}
for c in charters:
    reps = [w for w in worlds if w.startswith(c + "-r")]
    depth_vec = [world_stats[r]["mean_depth"] for r in reps]
    breadth_vec_lineages = [world_stats[r]["n_lineages"] for r in reps]
    breadth_vec_cv = [world_stats[r]["mean_cv"] for r in reps if world_stats[r]["mean_cv"] is not None]
    charter_stats[c] = dict(
        reps=reps,
        mean_depth=sum(depth_vec) / len(depth_vec),
        mean_n_lineages=sum(breadth_vec_lineages) / len(breadth_vec_lineages),
        mean_cv=(sum(breadth_vec_cv) / len(breadth_vec_cv)) if breadth_vec_cv else None,
    )

print("\nCHARTER STATS")
for c, s in charter_stats.items():
    print(c, s)

# --- clustering statistic: between/within variance ratio on (depth, breadth=visual CV) ---
# Lineage count is fixed at four in every world and therefore carries no
# information. The report's breadth axis is within-world visual dispersion.
# use world-level points, z-scored, grouped by charter
import statistics as st

pts = []
labels = []
for w in worlds:
    c = w.split("-r")[0]
    pts.append((world_stats[w]["mean_depth"], world_stats[w]["mean_cv"]))
    labels.append(c)

# z-score each dim across all 12 worlds
d_vals = [p[0] for p in pts]
b_vals = [p[1] for p in pts]
def z(vals):
    m = sum(vals) / len(vals)
    sd = st.pstdev(vals) or 1.0
    return [(v - m) / sd for v in vals]
dz = z(d_vals)
bz = z(b_vals)
zpts = list(zip(dz, bz))

grand_mean = (sum(dz) / len(dz), sum(bz) / len(bz))

groups = defaultdict(list)
for p, l in zip(zpts, labels):
    groups[l].append(p)

def dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

# between-group sum of squares
ss_between = 0.0
for l, pts_g in groups.items():
    gm = (sum(p[0] for p in pts_g) / len(pts_g), sum(p[1] for p in pts_g) / len(pts_g))
    ss_between += len(pts_g) * dist2(gm, grand_mean)

ss_within = 0.0
for l, pts_g in groups.items():
    gm = (sum(p[0] for p in pts_g) / len(pts_g), sum(p[1] for p in pts_g) / len(pts_g))
    for p in pts_g:
        ss_within += dist2(p, gm)

ss_total = ss_between + ss_within
ratio = ss_between / ss_within if ss_within > 0 else float("inf")

print("\nCLUSTERING")
print("ss_between", ss_between, "ss_within", ss_within, "ratio(between/within)", ratio)
print("frac variance explained by charter (ss_between/ss_total)", ss_between / ss_total)

# within-charter distance (r1 vs r2) vs between-charter distance (mean pairwise across charters)
within_dists = []
for c in charters:
    reps = [w for w in worlds if w.startswith(c + "-r")]
    if len(reps) == 2:
        i0, i1 = worlds.index(reps[0]), worlds.index(reps[1])
        within_dists.append(math.sqrt(dist2(zpts[i0], zpts[i1])))

between_dists = []
for i in range(len(worlds)):
    for j in range(i + 1, len(worlds)):
        if labels[i] != labels[j]:
            between_dists.append(math.sqrt(dist2(zpts[i], zpts[j])))

print("mean within-charter (r1-r2) distance", sum(within_dists) / len(within_dists))
print("mean between-charter distance", sum(between_dists) / len(between_dists))

# silhouette-like 2-cluster check is overkill/unstable with n=12; report ratio + replicate distances instead.

# save results to json for the writeup
import json as J
with open(BASE / "results" / "_depth_breadth_raw.json", "w") as f:
    J.dump(dict(world_stats=world_stats, charter_stats=charter_stats,
                ss_between=ss_between, ss_within=ss_within, ratio=ratio,
                frac_var=ss_between / ss_total,
                mean_within=sum(within_dists) / len(within_dists),
                mean_between=sum(between_dists) / len(between_dists),
                zpts=zpts, labels=labels, worlds=worlds), f, indent=2)

# Reproducible figure consumed by build_art_assets.py. Connect replicates from
# the same charter so within-charter disagreement is visible rather than hidden.
import matplotlib.pyplot as plt

palette = {
    "botanical": "#5b7f55", "brutalist": "#55585c", "cave": "#a35d35",
    "psychedelic": "#a33b7a", "quilt": "#c17b42", "ukiyo": "#2e6f8e",
}
fig, ax = plt.subplots(figsize=(9, 6))
fig.subplots_adjust(left=.10, right=.98, bottom=.11, top=.82)
for charter in charters:
    idxs = [i for i, label in enumerate(labels) if label == charter]
    xs = [world_stats[worlds[i]]["mean_depth"] for i in idxs]
    ys = [world_stats[worlds[i]]["mean_cv"] for i in idxs]
    ax.plot(xs, ys, color=palette[charter], alpha=.35, linewidth=1.4)
    ax.scatter(xs, ys, s=78, color=palette[charter], edgecolor="white",
               linewidth=.9, label=charter, zorder=3)
    for i, x, y in zip(idxs, xs, ys):
        ax.annotate(worlds[i].rsplit("-", 1)[-1], (x, y), xytext=(6, 4),
                    textcoords="offset points", fontsize=8, color=palette[charter])
ax.set_xlabel("Accepted revision depth (mean canonical versions per lineage)")
ax.set_ylabel("Visual breadth (mean within-world coefficient of variation)")
fig.suptitle("New cultures occupy loose revision regimes", x=.10, y=.97,
             ha="left", weight="bold", fontsize=16)
fig.text(.10, .92,
         "Lines join replicate worlds; extremes separate more cleanly than the middle.",
         fontsize=9, color="#666")
ax.grid(color="#ddd8cc", linewidth=.7, alpha=.7)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, ncol=3, loc="upper left")
fig.savefig(BASE / "results" / "depth_breadth.png", dpi=180,
            facecolor="#faf8f2")
plt.close(fig)
