# Twin worlds — charter divergence

Worlds analysed: 12 (botanical-r1, botanical-r2, brutalist-r1, brutalist-r2, cave-r1, cave-r2, psychedelic-r1, psychedelic-r2, quilt-r1, quilt-r2, ukiyo-r1, ukiyo-r2)


## 1. Charter adherence

Distinctive charter vocabulary per 1,000 tokens of agent reasoning and
adopted doctrine. Rows are the world's own charter; columns are whose
vocabulary is being counted. If charters bite, the diagonal dominates.
The control has no charter, so it has no column — its row is the
baseline rate at which this vocabulary appears with no charter at all.

| world charter | ancestor | ascetic | baroque | botanical | brutalist | cave | futurist | nihilist | psychedelic | quilt | ukiyo | diagonal / best off-diagonal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| botanical | 1.71 | 1.27 | 27.05 | **17.48** | 16.13 | 0.29 | 38.18 | 0.14 | 2.89 | 2.11 | 3.16 | 0.5x |
| brutalist | 1.72 | 1.24 | 23.32 | 13.84 | **24.82** | 0.43 | 36.99 | 0.15 | 2.51 | 1.83 | 2.85 | 0.7x |
| cave | 1.58 | 1.66 | 31.35 | 13.76 | 20.74 | **1.11** | 22.30 | 0.20 | 2.68 | 1.09 | 2.88 | 0.0x |
| psychedelic | 1.25 | 1.90 | 26.28 | 11.39 | 18.93 | 0.37 | 30.99 | 0.19 | **8.82** | 2.13 | 3.23 | 0.3x |
| quilt | 2.30 | 1.18 | 28.66 | 15.82 | 17.93 | 0.21 | 24.01 | 0.17 | 2.25 | **2.81** | 2.15 | 0.1x |
| ukiyo | 1.46 | 1.41 | 23.85 | 12.43 | 16.44 | 0.35 | 41.67 | 0.19 | 2.27 | 2.27 | **3.81** | 0.1x |

### Lift over the charter-free control

Each cell is the row world's rate divided by the control's rate for the
same vocabulary. 1.0x means the charter made no difference to how often
those words appear; the diagonal is the charter's effect on itself.

| world charter | ancestor | ascetic | baroque | botanical | brutalist | cave | futurist | nihilist | psychedelic | quilt | ukiyo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| botanical | — | — | — | **—** | — | — | — | — | — | — | — |
| brutalist | — | — | — | — | **—** | — | — | — | — | — | — |
| cave | — | — | — | — | — | **—** | — | — | — | — | — |
| psychedelic | — | — | — | — | — | — | — | — | **—** | — | — |
| quilt | — | — | — | — | — | — | — | — | — | **—** | — |
| ukiyo | — | — | — | — | — | — | — | — | — | — | **—** |

## 2. Art-form divergence

One vector per world (mean over its canonical artworks), then
between-charter variance over within-charter variance. F near 1 means
charter groups differ no more than replicates of the same charter —
that is the falsifier for H1.

| feature | F (between/within) | MS between | MS within |
|---|---:|---:|---:|
| html_bytes | 175 | 2.94e+07 | 1.68e+05 |
| n_drawable | 133 | 2.82e+03 | 21.3 |
| n_svg | inf | 0 | 0 |
| n_div | inf | 0 | 0 |
| animated | 0.925 | 0.00473 | 0.00512 |
| distinct_colors | 499 | 2.29e+06 | 4.59e+03 |

### Per-world feature means

| world | n artworks | html_bytes | n_drawable | n_svg | n_div | animated | distinct_colors |
|---|---|---|---|---|---|---|---|
| botanical-r1 | 37 | 8322 | 62.35 | 1 | 0 | 0.2432 | 3325 |
| botanical-r2 | 41 | 7980 | 62.22 | 1 | 0 | 0 | 3310 |
| brutalist-r1 | 33 | 2577 | 24.21 | 1 | 0 | 0 | 190.1 |
| brutalist-r2 | 45 | 3273 | 33.24 | 1 | 0 | 0 | 255.4 |
| cave-r1 | 5 | 1.156e+04 | 94 | 1 | 0 | 0 | 1844 |
| cave-r2 | 19 | 1.103e+04 | 89.05 | 1 | 0 | 0 | 1732 |
| psychedelic-r1 | 42 | 4184 | 19.48 | 1 | 0 | 0.04762 | 850.1 |
| psychedelic-r2 | 22 | 4279 | 23.05 | 1 | 0 | 0 | 679.2 |
| quilt-r1 | 10 | 9558 | 102.4 | 1 | 0 | 0 | 1510 |
| quilt-r2 | 23 | 1.06e+04 | 113.6 | 1 | 0 | 0 | 1603 |
| ukiyo-r1 | 30 | 2444 | 24.63 | 1 | 0 | 0 | 1070 |
| ukiyo-r2 | 26 | 2288 | 21.38 | 1 | 0 | 0 | 1083 |

## 3. Doctrine text divergence

TF-IDF cosine between worlds' adopted doctrines.

| comparison | n pairs | mean cosine |
|---|---:|---:|
| same charter, different replicate | 6 | 0.3087 |
| different charter | 60 | 0.0505 |
| **gap (within − across)** | | **+0.2583** |
