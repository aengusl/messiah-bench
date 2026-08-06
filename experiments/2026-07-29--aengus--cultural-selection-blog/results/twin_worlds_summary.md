# Twin worlds — charter divergence

> **PREVIEW — the fleet is still running.** These numbers will move.

Worlds analysed: 18 (ancestor-r1, ancestor-r2, ancestor-r3, ascetic-r1, ascetic-r2, ascetic-r3, baroque-r1, baroque-r2, baroque-r3, control-r1, control-r2, control-r3, futurist-r1, futurist-r2, futurist-r3, nihilist-r1, nihilist-r2, nihilist-r3)

Still running: ancestor-r1, ancestor-r2, ancestor-r3, ascetic-r1, ascetic-r2, ascetic-r3, baroque-r1, baroque-r2, baroque-r3, control-r1, control-r2, control-r3, futurist-r1, futurist-r2, futurist-r3, nihilist-r1, nihilist-r2, nihilist-r3


## 1. Charter adherence

Distinctive charter vocabulary per 1,000 tokens of agent reasoning and
adopted doctrine. Rows are the world's own charter; columns are whose
vocabulary is being counted. If charters bite, the diagonal dominates.
The control has no charter, so it has no column — its row is the
baseline rate at which this vocabulary appears with no charter at all.

| world charter | ancestor | ascetic | baroque | futurist | nihilist | diagonal / best off-diagonal |
|---|---|---|---|---|---|---|
| ancestor | **9.89** | 0.21 | 0.37 | 0.27 | 0.25 | 26.5x |
| ascetic | 0.37 | **2.49** | 0.21 | 0.25 | 0.21 | 6.7x |
| baroque | 0.26 | 0.36 | **16.76** | 0.58 | 0.15 | 29.1x |
| control | 0.28 | 0.40 | 0.24 | 0.33 | 0.22 | — |
| futurist | 0.79 | 0.65 | 0.23 | **13.98** | 0.24 | 17.8x |
| nihilist | 0.28 | 0.28 | 0.40 | 0.45 | **3.48** | 7.8x |

### Lift over the charter-free control

Each cell is the row world's rate divided by the control's rate for the
same vocabulary. 1.0x means the charter made no difference to how often
those words appear; the diagonal is the charter's effect on itself.

| world charter | ancestor | ascetic | baroque | futurist | nihilist |
|---|---|---|---|---|---|
| ancestor | **35.38x** | 0.52x | 1.53x | 0.84x | 1.16x |
| ascetic | 1.34x | **6.25x** | 0.87x | 0.76x | 0.99x |
| baroque | 0.93x | 0.91x | **68.60x** | 1.77x | 0.71x |
| control | 1.00x | 1.00x | 1.00x | 1.00x | 1.00x |
| futurist | 2.81x | 1.64x | 0.96x | **42.92x** | 1.12x |
| nihilist | 0.99x | 0.71x | 1.63x | 1.38x | **16.14x** |

## 2. Art-form divergence

One vector per world (mean over its canonical artworks), then
between-charter variance over within-charter variance. F near 1 means
charter groups differ no more than replicates of the same charter —
that is the falsifier for H1.

| feature | F (between/within) | MS between | MS within |
|---|---:|---:|---:|
| html_bytes | 5.9 | 1.16e+06 | 1.96e+05 |
| n_drawable | 0.795 | 0.0414 | 0.0521 |
| n_svg | 1 | 0.00128 | 0.00128 |
| n_div | 3.43 | 10.7 | 3.12 |
| animated | 5.99 | 0.278 | 0.0465 |
| distinct_colors | 9.62 | 2.55e+06 | 2.65e+05 |

### Per-world feature means

| world | n artworks | html_bytes | n_drawable | n_svg | n_div | animated | distinct_colors |
|---|---|---|---|---|---|---|---|
| ancestor-r1 | 5 | 881.6 | 2 | 0 | 1 | 0 | 839.4 |
| ancestor-r2 | 4 | 877 | 2 | 0 | 1 | 0 | 841 |
| ancestor-r3 | 4 | 877 | 2 | 0 | 1 | 0 | 841 |
| ascetic-r1 | 7 | 899.9 | 2 | 0 | 1 | 0 | 851.3 |
| ascetic-r2 | 24 | 937.6 | 2 | 0 | 1 | 0 | 867.2 |
| ascetic-r3 | 4 | 877 | 2 | 0 | 1 | 0 | 841 |
| baroque-r1 | 43 | 2793 | 2 | 0 | 7.721 | 0.5581 | 2570 |
| baroque-r2 | 40 | 2714 | 2.025 | 0 | 6.8 | 0.775 | 4634 |
| baroque-r3 | 33 | 2087 | 2.697 | 0.1515 | 3.606 | 0.6667 | 2549 |
| control-r1 | 27 | 1424 | 2.148 | 0 | 3.037 | 0.4815 | 1216 |
| control-r2 | 42 | 1346 | 2 | 0 | 1.357 | 0.5714 | 1417 |
| control-r3 | 46 | 2370 | 2 | 0 | 5.717 | 0.6739 | 1632 |
| futurist-r1 | 3 | 877.3 | 2 | 0 | 1 | 0 | 846.3 |
| futurist-r2 | 20 | 1260 | 2 | 0 | 1.2 | 0.8 | 978 |
| futurist-r3 | 20 | 1739 | 1.95 | 0 | 4.65 | 0.65 | 1048 |
| nihilist-r1 | 17 | 1445 | 2 | 0 | 3.471 | 0.4118 | 1077 |
| nihilist-r2 | 20 | 1123 | 2 | 0 | 1 | 0.45 | 1050 |
| nihilist-r3 | 45 | 2495 | 2.667 | 0 | 5.467 | 0.9111 | 1616 |

## 3. Doctrine text divergence

TF-IDF cosine between worlds' adopted doctrines.

| comparison | n pairs | mean cosine |
|---|---:|---:|
| same charter, different replicate | 18 | 0.2680 |
| different charter | 135 | 0.0385 |
| **gap (within − across)** | | **+0.2295** |
