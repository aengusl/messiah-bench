# Twin worlds — charter divergence

Worlds analysed: 18 (ancestor-r1, ancestor-r2, ancestor-r3, ascetic-r1, ascetic-r2, ascetic-r3, baroque-r1, baroque-r2, baroque-r3, control-r1, control-r2, control-r3, futurist-r1, futurist-r2, futurist-r3, nihilist-r1, nihilist-r2, nihilist-r3)


## 1. Charter adherence

Distinctive charter vocabulary per 1,000 tokens of agent reasoning and
adopted doctrine. Rows are the world's own charter; columns are whose
vocabulary is being counted. If charters bite, the diagonal dominates.
The control has no charter, so it has no column — its row is the
baseline rate at which this vocabulary appears with no charter at all.

| world charter | ancestor | ascetic | baroque | futurist | nihilist | diagonal / best off-diagonal |
|---|---|---|---|---|---|---|
| ancestor | **9.91** | 0.26 | 0.21 | 0.30 | 0.21 | 33.0x |
| ascetic | 0.39 | **2.42** | 0.09 | 0.23 | 0.18 | 6.2x |
| baroque | 0.76 | 0.43 | **11.81** | 0.45 | 0.10 | 15.6x |
| control | 0.39 | 0.51 | 0.13 | 0.24 | 0.14 | — |
| futurist | 0.65 | 0.56 | 0.15 | **11.37** | 0.17 | 17.6x |
| nihilist | 0.47 | 0.43 | 0.28 | 0.40 | **2.80** | 5.9x |

### Lift over the charter-free control

Each cell is the row world's rate divided by the control's rate for the
same vocabulary. 1.0x means the charter made no difference to how often
those words appear; the diagonal is the charter's effect on itself.

| world charter | ancestor | ascetic | baroque | futurist | nihilist |
|---|---|---|---|---|---|
| ancestor | **25.66x** | 0.50x | 1.54x | 1.23x | 1.47x |
| ascetic | 1.01x | **4.74x** | 0.68x | 0.96x | 1.27x |
| baroque | 1.96x | 0.83x | **88.42x** | 1.85x | 0.70x |
| control | 1.00x | 1.00x | 1.00x | 1.00x | 1.00x |
| futurist | 1.67x | 1.09x | 1.12x | **46.54x** | 1.18x |
| nihilist | 1.22x | 0.85x | 2.12x | 1.62x | **19.64x** |

## 2. Art-form divergence

One vector per world (mean over its canonical artworks), then
between-charter variance over within-charter variance. F near 1 means
charter groups differ no more than replicates of the same charter —
that is the falsifier for H1.

| feature | F (between/within) | MS between | MS within |
|---|---:|---:|---:|
| html_bytes | 6.04 | 1.2e+06 | 1.99e+05 |
| n_drawable | 0.736 | 0.0521 | 0.0708 |
| n_svg | 1 | 0.00173 | 0.00173 |
| n_div | 2.92 | 10.9 | 3.74 |
| animated | 30 | 0.362 | 0.0121 |
| distinct_colors | 10.2 | 2.56e+06 | 2.52e+05 |

### Per-world feature means

| world | n artworks | html_bytes | n_drawable | n_svg | n_div | animated | distinct_colors |
|---|---|---|---|---|---|---|---|
| ancestor-r1 | 5 | 881.6 | 2 | 0 | 1 | 0 | 839.4 |
| ancestor-r2 | 4 | 877 | 2 | 0 | 1 | 0 | 841 |
| ancestor-r3 | 4 | 877 | 2 | 0 | 1 | 0 | 841 |
| ascetic-r1 | 7 | 899.9 | 2 | 0 | 1 | 0 | 851.3 |
| ascetic-r2 | 25 | 934.6 | 2 | 0 | 1 | 0 | 863 |
| ascetic-r3 | 5 | 888 | 2 | 0 | 1 | 0 | 849.8 |
| baroque-r1 | 45 | 2849 | 2 | 0 | 7.911 | 0.5778 | 2556 |
| baroque-r2 | 40 | 2714 | 2.025 | 0 | 6.8 | 0.775 | 4634 |
| baroque-r3 | 34 | 2143 | 2.882 | 0.1765 | 3.559 | 0.6765 | 2655 |
| control-r1 | 27 | 1424 | 2.148 | 0 | 3.037 | 0.4815 | 1216 |
| control-r2 | 45 | 1411 | 2 | 0 | 1.422 | 0.6 | 1502 |
| control-r3 | 47 | 2397 | 2 | 0 | 5.851 | 0.6809 | 1623 |
| futurist-r1 | 20 | 1169 | 2.1 | 0 | 1.45 | 0.6 | 966.8 |
| futurist-r2 | 21 | 1318 | 2 | 0 | 1.429 | 0.8095 | 984.1 |
| futurist-r3 | 30 | 2142 | 1.967 | 0 | 5.867 | 0.7333 | 1103 |
| nihilist-r1 | 21 | 1603 | 2 | 0 | 4.19 | 0.5238 | 1153 |
| nihilist-r2 | 30 | 1250 | 2 | 0 | 1.033 | 0.6333 | 1466 |
| nihilist-r3 | 49 | 2558 | 2.694 | 0 | 5.735 | 0.9184 | 1743 |

## 3. Doctrine text divergence

TF-IDF cosine between worlds' adopted doctrines.

| comparison | n pairs | mean cosine |
|---|---:|---:|
| same charter, different replicate | 18 | 0.3243 |
| different charter | 135 | 0.0212 |
| **gap (within − across)** | | **+0.3032** |
