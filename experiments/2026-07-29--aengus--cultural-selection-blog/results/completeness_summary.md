# Completeness of generated artwork — all corpora

Source-level analysis: was the HTML cut off mid-tag, and does it contain
any element that would actually paint? No rendering involved.

`n_drawable` counts complete foreground elements, excluding `<defs>`,
`<style>`, half-written tags, and full-bleed background rects.

## Per regime (canonical artworks)

| regime | n | % truncated | % nothing paintable | median drawable elements | median bytes |
|---|---:|---:|---:|---:|---:|
| v7 | 4445 | 90.7% | 77.5% | 0 | 4266 |
| v8 | 1355 | 78.7% | 44.0% | 3 | 4611 |
| minimal | 86 | 0.0% | 0.0% | 2 | 2788 |

## Trend over each run's lifetime

Paintable fraction per time decile (Wilson 95% CI).

| regime | decile | mean turn | n | % paintable | 95% CI |
|---|---:|---:|---:|---:|---|
| v7 | 0 | 23 | 431 | 64.7% | 60.1–69.1% |
| v7 | 1 | 62 | 452 | 25.7% | 21.9–29.9% |
| v7 | 2 | 102 | 470 | 24.3% | 20.6–28.3% |
| v7 | 3 | 141 | 458 | 18.1% | 14.9–21.9% |
| v7 | 4 | 181 | 475 | 15.8% | 12.8–19.3% |
| v7 | 5 | 220 | 465 | 18.1% | 14.8–21.8% |
| v7 | 6 | 260 | 423 | 16.8% | 13.5–20.6% |
| v7 | 7 | 299 | 433 | 10.6% | 8.1–13.9% |
| v7 | 8 | 339 | 407 | 13.0% | 10.1–16.6% |
| v7 | 9 | 380 | 431 | 17.9% | 14.5–21.8% |
| v8 | 0 | 15 | 68 | 97.1% | 89.9–99.2% |
| v8 | 1 | 32 | 104 | 100.0% | 96.4–100.0% |
| v8 | 2 | 51 | 122 | 99.2% | 95.5–99.9% |
| v8 | 3 | 69 | 147 | 73.5% | 65.8–79.9% |
| v8 | 4 | 87 | 146 | 43.2% | 35.4–51.3% |
| v8 | 5 | 105 | 179 | 50.8% | 43.6–58.1% |
| v8 | 6 | 122 | 191 | 43.5% | 36.6–50.5% |
| v8 | 7 | 141 | 184 | 38.0% | 31.3–45.2% |
| v8 | 8 | 158 | 151 | 23.8% | 17.7–31.2% |
| v8 | 9 | 174 | 63 | 27.0% | 17.6–39.0% |
| minimal | 0 | 20 | 25 | 100.0% | 86.7–100.0% |
| minimal | 1 | 110 | 6 | 100.0% | 61.0–100.0% |
| minimal | 2 | 195 | 39 | 100.0% | 91.0–100.0% |
| minimal | 3 | 244 | 13 | 100.0% | 77.2–100.0% |
| minimal | 4 | 339 | 1 | 100.0% | 20.7–100.0% |
| minimal | 5 | 394 | 1 | 100.0% | 20.7–100.0% |
| minimal | 6 | 762 | 1 | 100.0% | 20.7–100.0% |

## Does the adoption gate filter on completeness?

The minimal run is the only one with an explicit accept/reject step,
so it is the only place this mechanism can be tested directly.

| group | n | % truncated | % nothing paintable | median drawable |
|---|---:|---:|---:|---:|
| proposal_accepted | 82 | 0.0% | 0.0% | 2 |
| proposal_rejected | 255 | 0.0% | 0.0% | 2 |
| proposal_unresolved | 2 | 0.0% | 0.0% | 2 |
| canon | 86 | 0.0% | 0.0% | 2 |
