# Twin worlds — charter divergence

Worlds analysed: 12 (k16-r1, k16-r2, k16-r3, k4-r1, k4-r2, k4-r3, k8-r1, k8-r2, k8-r3, kinf-r1, kinf-r2, kinf-r3)


## 1. Charter adherence

Distinctive charter vocabulary per 1,000 tokens of agent reasoning and
adopted doctrine. Rows are the world's own charter; columns are whose
vocabulary is being counted. If charters bite, the diagonal dominates.
The control has no charter, so it has no column — its row is the
baseline rate at which this vocabulary appears with no charter at all.

| world charter | ancestor | ascetic | baroque | futurist | nihilist | diagonal / best off-diagonal |
|---|---|---|---|---|---|---|
| k16 | 2.62 | 19.12 | 19.54 | 28.83 | 1.99 | — |
| k4 | 2.48 | 20.79 | 17.67 | 28.25 | 2.43 | — |
| k8 | 2.35 | 22.56 | 20.29 | 23.25 | 2.97 | — |
| kinf | 2.20 | 20.13 | 21.31 | 27.80 | 1.98 | — |

### Lift over the charter-free control

Each cell is the row world's rate divided by the control's rate for the
same vocabulary. 1.0x means the charter made no difference to how often
those words appear; the diagonal is the charter's effect on itself.

| world charter | ancestor | ascetic | baroque | futurist | nihilist |
|---|---|---|---|---|---|
| k16 | — | — | — | — | — |
| k4 | — | — | — | — | — |
| k8 | — | — | — | — | — |
| kinf | — | — | — | — | — |

## 2. Art-form divergence

One vector per world (mean over its canonical artworks), then
between-charter variance over within-charter variance. F near 1 means
charter groups differ no more than replicates of the same charter —
that is the falsifier for H1.

| feature | F (between/within) | MS between | MS within |
|---|---:|---:|---:|
| html_bytes | 0.418 | 6.83e+04 | 1.63e+05 |
| n_drawable | 0.76 | 0.887 | 1.17 |
| n_svg | 0.956 | 0.0168 | 0.0176 |
| n_div | 0.233 | 0.68 | 2.92 |
| animated | 2.4 | 0.1 | 0.0419 |
| distinct_colors | 1.85 | 1.57e+05 | 8.45e+04 |

### Per-world feature means

| world | n artworks | html_bytes | n_drawable | n_svg | n_div | animated | distinct_colors |
|---|---|---|---|---|---|---|---|
| k16-r1 | 34 | 1724 | 2.706 | 0 | 2.294 | 0.7647 | 1359 |
| k16-r2 | 17 | 1889 | 2 | 0 | 4.235 | 0.7647 | 1285 |
| k16-r3 | 33 | 1778 | 2.121 | 0.0303 | 2.818 | 0.7576 | 1109 |
| k4-r1 | 14 | 1389 | 2 | 0 | 2.857 | 0.4286 | 1620 |
| k4-r2 | 26 | 1793 | 2.308 | 0 | 2.462 | 0.7308 | 1753 |
| k4-r3 | 21 | 2851 | 2 | 0 | 5.524 | 0.7143 | 1308 |
| k8-r1 | 29 | 1782 | 2 | 0 | 4.793 | 0.6552 | 1242 |
| k8-r2 | 12 | 1556 | 2 | 0 | 5.5 | 0 | 939.4 |
| k8-r3 | 24 | 1703 | 5.667 | 0.4583 | 1.917 | 0.5 | 1060 |
| kinf-r1 | 32 | 2131 | 2 | 0 | 5.125 | 0.7812 | 1214 |
| kinf-r2 | 57 | 1669 | 2 | 0 | 1.772 | 0.9298 | 2096 |
| kinf-r3 | 33 | 2069 | 2.212 | 0 | 5.545 | 0.6364 | 1260 |

## 3. Doctrine text divergence

TF-IDF cosine between worlds' adopted doctrines.

| comparison | n pairs | mean cosine |
|---|---:|---:|
| same charter, different replicate | 12 | 0.1117 |
| different charter | 54 | 0.0864 |
| **gap (within − across)** | | **+0.0253** |
