# Twin Worlds v2: divergent DNA — preregistration

Written 2026-08-06, before any v2 world is launched. v1 (`results/twin_worlds_summary.md`)
ran the same six charters from one identical founding artwork.

## Hypothesis

**H1-visual.** Given a genuinely different founding artwork per culture, plus the charter,
the six worlds produce *visibly* divergent art lineages at turn 300 — divergence that a
blind judge can sort by world, not just divergence in a feature vector.

The skeptic's reading of v1 is the reason for v2: *every world made the same circle*. It
is true and it has two possible causes, which v1 cannot separate:

1. Charters do not reach the art. Agents read a creed and keep drawing what the seed drew.
2. The single shared seed artwork was the dominant prior, and the charter never had room
   to act. Every lineage descends from one glowing circle with a name written across it.

v2 removes cause 2. If lineages still converge with six different founding images, the
charter genuinely does not reach the art and the v1 result stands as a real (negative)
finding. If they diverge, v1 was measuring the seed, not the creed.

The no-words rule is the second half of the same argument. Much of v1's "art" carried its
meaning in a title and a doctrine caption — text is the cheap channel, and while it is open
the image never has to do any work. Closing it forces the visual channel to carry the culture.

## Design

Six charters × 3 replicates × 300 turns = 18 worlds. Every parameter identical to v1:

| Parameter | Value |
|---|---|
| `--seed` | 46 |
| `--agents` | 24 |
| `--model` | `gemini-2.5-flash` |
| `--turns` | 300 |
| `--initial-life` | 20 |
| `--proposal-lifetime` | 3 |
| `--workers` | 8 |
| `--cost-cap` | 40 per world (unreachable at ~$22 expected; catches a runaway) |
| `SEED_RELIGIONS` | unchanged — same four names, doctrines, colours, motifs |
| agent→religion | unchanged, `(i % 4) + 1` |
| temperature / thinking | 0.9 / 256 |

Launch:

```bash
bash experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_twin_worlds.sh \
  --charters "ascetic,baroque,nihilist,ancestor,futurist,control" --reps 3 --turns 300 \
  --out-tag 2026-08-07-twin-worlds-v2 \
  --seed-art-root experiments/2026-07-12-minimal-cultural-selection/seed_arts \
  --no-words
```

## What changes vs v1 — exactly two things

1. **Per-charter founding artwork.** `--seed-art-dir DIR` loads `seed-{1..4}.html` from DIR
   as the founding artwork of the four seed religions. The four files within a world are
   variations on one visual DNA, so the religions are distinguishable but obviously kin.
2. **The no-words rule.** `--no-words` appends one sentence to the system prompt ("artworks
   must contain no words, letters, or numerals — the image alone carries meaning") and makes
   `validate_art` reject any artwork whose visible text (tags, `<style>`, `<script>`, `<defs>`
   stripped) contains 3+ consecutive latin letters.

**Both are applied to all six worlds, control included.** Control gets its own seed-art
directory holding the legacy geometric-circle template with the text removed. This is the
whole point: if only the charter worlds got new art, "charter" and "art" would be confounded
and the contrast would be uninterpretable. The control is a world with a distinct founding
image and no creed, so the charter remains the only manipulated variable across worlds.

Nothing else moves. Religion names, doctrines, prompts, seed, model, and the analysis
pipeline are untouched, so `scripts/twin_worlds_report.py` reads v2 output as it reads v1's,
and v1 vs v2 is a legitimate comparison.

Deviations from the original design sketch, both forced by the engine's existing validator:

- **The futurist world is SVG, not canvas.** `validate_art` has always banned `<script>`, so
  a canvas-generated starfield cannot exist in this engine. Same visual target — starfield,
  perspective machine-grid, cyan/steel, hard angles — reached with static SVG.
- **No `xmlns` on any seed SVG.** The validator's `https?://` ban matches the SVG namespace
  URI. Inline SVG in HTML5 does not need the attribute; all 24 files render correctly without it.

## Outcomes

Primary, from the unchanged `twin_worlds_report.py`:

- feature divergence between worlds over time (`twin_worlds_features.csv`, the divergence plot)
- religion count, founding rate, survival, influence concentration
- a blind judged pass over sampled artworks

Added for v2, and the one that answers the skeptic directly:

- **Motif persistence: does any lineage still contain its founding motif at turn 300?**
  Sample the canonical artwork of each surviving religion at turns 0 / 100 / 200 / 300, and
  have a blind judge assign each to one of the six visual worlds. Chance is 1/6. Above chance
  means founding art is heritable; at chance means it washes out and the seed does not matter,
  which would retroactively defend v1.
- **Charter-art agreement**, blind: judge rates each late artwork against the five creeds
  without being told which world it came from.

Pre-committed reading: H1-visual is supported only if world-classification accuracy at turn
300 is above chance *and* the judged charter-art agreement beats control. Divergence in the
feature vector alone is not enough — v1 already had some of that and it did not survive
looking at the images.

## Cost

18 worlds × ~$22 = ~$400, plus ~$8 for the smoke test and the judged passes. Hard cap $40
per world. Rendering and seed-art generation are free (local chromium).

## Verification done before launch

- 24 founding artworks build deterministically from `scripts/build_seed_arts.py`
- all 24 are ≤15000 chars, pass `validate_art(no_words=True)`, and render non-blank
  (>8 distinct colours) in chromium at 800×800
- `tests/test_twin_v2.py`: 66 tests green
- default behaviour unchanged: with no `--seed-art-dir` the founding art is byte-identical
  to the legacy template, and `validate_art` without `no_words` still accepts lettered art
