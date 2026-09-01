# Depth / breadth: clusters or continuum?

## Definitions used

- **World / charter**: 12 worlds = 6 charters (botanical, brutalist, cave, psychedelic, quilt, ukiyo) x 2 replicates (r1, r2).
- **Depth**: from `versions.jsonl`, versions are grouped by `religion_id` (each world seeds 4 religions at turn 0; every subsequent proposal either revises one of these lineages via `parent_version_id` or is rejected). All logged versions in these files have `status: "canonical"` (no rejected/superseded versions are persisted in this dump), so depth per lineage = count of canonical versions ever recorded under that `religion_id`. **Depth per world** = mean and max of that count across the world's 4 lineages.
- **Breadth, lineage count**: number of distinct `religion_id` lineages that reached canonical status. **This turned out to be exactly 4 in all 12 worlds** (every world was seeded with 4 religions and none died out or split before producing a canonical version) — it carries zero variance and cannot separate anything. Reported per world for completeness but excluded from the clustering statistic.
- **Breadth, dispersion**: coefficient of variation (CV = sd/mean) of `html_bytes`, `n_drawable`, and `distinct_colors` across all canonical artworks in a world, averaged over the three features → "mean_cv" per world. This is the breadth measure actually used for clustering, since lineage-count breadth is degenerate.

## Per-world table

| world | n canonical artworks | mean depth | max depth | n lineages | mean CV (breadth) |
|---|---|---|---|---|---|
| botanical-r1 | 37 | 9.25 | 10 | 4 | 0.162 |
| botanical-r2 | 41 | 10.25 | 11 | 4 | 0.162 |
| brutalist-r1 | 33 | 8.25 | 10 | 4 | 0.160 |
| brutalist-r2 | 45 | 11.25 | 12 | 4 | 0.225 |
| cave-r1 | 5 | 1.25 | 2 | 4 | 0.140 |
| cave-r2 | 19 | 4.75 | 14 | 4 | 0.096 |
| psychedelic-r1 | 42 | 10.50 | 14 | 4 | 0.647 |
| psychedelic-r2 | 22 | 5.50 | 10 | 4 | 0.541 |
| quilt-r1 | 10 | 2.50 | 3 | 4 | 0.191 |
| quilt-r2 | 23 | 5.75 | 6 | 4 | 0.180 |
| ukiyo-r1 | 30 | 7.50 | 9 | 4 | 0.132 |
| ukiyo-r2 | 26 | 6.50 | 7 | 4 | 0.128 |

Charter means (pooling r1+r2): botanical depth 9.75/breadth 0.162; brutalist depth 9.75/breadth 0.192; cave depth 3.00/breadth 0.118; psychedelic depth 8.00/breadth 0.594; quilt depth 4.125/breadth 0.186; ukiyo depth 7.00/breadth 0.130.

## Clustering statistic

z-scored each world's (mean depth, mean CV breadth) across all 12 worlds, then computed between-charter vs within-charter sum-of-squares (6 groups of 2):

- **ss_between = 20.48, ss_within = 3.52, ratio = 5.82** (fraction of total variance explained by charter identity = **0.853**).
- Cave is the clear low-depth outlier (z ≈ -1.9 to -0.7 on depth); psychedelic is the clear high-breadth outlier (z ≈ +1.9 to +2.5 on breadth CV, driven almost entirely by wide swings in `html_bytes` and color count). Botanical/brutalist sit together at high depth, low-to-moderate breadth; ukiyo/quilt sit at moderate depth, low breadth.

**n lineages breadth is degenerate (=4 everywhere)** — it was dropped from the clustering statistic; only depth and CV-dispersion breadth are used above.

## Replicate agreement

Mean within-charter (r1 vs r2) distance in z-space = **0.96**; mean between-charter distance = **1.91**. Replicates land roughly twice as close to each other as to a random other charter, consistent with charter being a real factor, though not by a huge margin — cave-r1 and cave-r2 disagree substantially in depth (1.25 vs 4.75, and n=5 canonical artworks for cave-r1 is a thin sample), and brutalist-r1/r2 diverge more in breadth (0.16 vs 0.23) than either does from botanical.

## Caveats

- Sample sizes per world range from 5 (cave-r1) to 45 (brutalist-r2) canonical artworks — cave-r1's depth/breadth estimate is on a thin base and should be read with wide uncertainty.
- Only canonical versions are logged in `versions.jsonl`; there's no record of rejected proposals, so "depth" here is depth of *accepted* revision, not total revision attempts.
- Lineage-count breadth is uninformative by construction (fixed 4 seed religions/world) — this is a genuine null result about the data, not a bug in the analysis.
- 6 charters x 2 reps is a small n for any clustering test; the between/within ratio (5.82) and 85% variance-explained are descriptive, not p-value-backed.

## Verdict

Charters separate into loose regimes rather than a smooth continuum: charter identity explains ~85% of the variance in (depth, breadth) and within-charter replicates sit about half as far apart as between-charter pairs (between/within SS ratio 5.82). Psychedelic is a clean outlier on breadth (CV ~0.6 vs ~0.1-0.2 elsewhere) and cave is a clean outlier on depth (mean depth 1.25-4.75 vs 5.5-11.25 elsewhere), while botanical/brutalist/ukiyo/quilt overlap more with each other, so "distinct regimes" is true at the extremes (cave, psychedelic) but the middle four charters smear together.

## Files

- `scripts/depth_breadth.py` — computation
- `results/depth_breadth.png` — scatter plot
- `results/_depth_breadth_raw.json` — raw per-world/charter numbers backing this table
