# New aesthetics: six fresh visual DNAs — preregistration

Written 2026-08-08, before any world is launched. v2 (`docs/twin_worlds_v2_prereg.md`)
showed that a distinct founding artwork plus a charter produces lineages a blind judge
sorts perfectly (36/36) with a 6× spread in judged cultural beauty.

## Question

Two things, one fleet:

1. **Does the v2 result replicate on visual DNA it has never seen?** Six new worlds —
   ukiyo, cave, brutalist, psychedelic, botanical, quilt — none of which shares a palette,
   a construction rule, or a subject with the v2 packs. If blind classification is again
   far above chance at turn 200, the finding is about founding art in general, not about
   the five aesthetics we happened to pick first.
2. **Which visual DNA produces the coolest art?** Judged by humans, not by a model. The
   v2 judged pass showed judges favour their own prior, so the ranking that matters here
   is human curation over the same sampled artworks.

## Design

Six cultures × 2 replicates × 200 turns = 12 worlds. Everything else identical to v2:
seed 46, 24 agents, `gemini-2.5-flash`, initial life 20, proposal lifetime 3, 8 workers,
temperature 0.9, thinking 256, `--no-words`, unchanged `SEED_RELIGIONS` and agent→religion
mapping, `--cost-cap 40` per world.

```bash
bash experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_twin_worlds.sh \
  --charters "ukiyo,cave,brutalist,psychedelic,botanical,quilt" --reps 2 --turns 200 \
  --out-tag 2026-08-08-new-aesthetics \
  --seed-art-root experiments/2026-07-12-minimal-cultural-selection/seed_arts \
  --no-words
```

**This round ships no control world.** v2's control (creed-free, legacy geometry, same
engine, same seed) already anchors the comparison, and a second identical control would
buy nothing at ~$18/world. The cost is that a within-fleet charter-vs-no-charter contrast
is unavailable here; every comparison in this round is either between the six new worlds
or against the v2 control on record.

## The six worlds

| World | Founding image |
|---|---|
| ukiyo | flat woodblock planes: indigo/salmon wave bands, snow-capped mountain, bold ink outline |
| cave | ochre herd and stencilled handprints, charcoal tallies, speckled stone ground |
| brutalist | grey concrete slabs over a heavy grid, one hard diagonal, one warning-orange bar |
| psychedelic | concentric warped rings in vibrating complements, moiré fans, melting mirror blobs |
| botanical | art-nouveau cartouche, mirrored vines and tendrils, sage/ivory blossoms with gold eyes |
| quilt | pieced calico blocks (pinwheel, square-in-square, nine-patch, flying geese), stitch dashes |

Four seeds per world, variations on one construction rule, generated deterministically by
`scripts/build_seed_arts.py` and committed under
`experiments/2026-07-12-minimal-cultural-selection/seed_arts/<world>/seed-{1..4}.html`.

## Outcomes

- **Blind world classification** of sampled canonical artworks at turns 0/50/100/200.
  Six worlds, so chance is 1/6 (16.7%). Pre-committed reading: replication if turn-200
  accuracy is above chance with a CI excluding 1/6; strong replication if it approaches
  v2's ceiling.
- **Judged pass** on the same sampled artworks (`scripts/judge_tournament.py`), reported
  with the judge's own-prior bias in view — a judge's ranking of its own aesthetic is
  read as a bias estimate, not as a quality estimate.
- **Human curation.** Aengus ranks a blind grid of late artworks across the six worlds.
  This is the primary outcome for "which DNA is coolest"; the model judge is secondary.
- Standard divergence/feature series from the unchanged `twin_worlds_report.py`.

## Cost

12 worlds × ~$18 (200 turns, scaled from v2's ~$22 at 300) ≈ $215, plus ~$5 for the smoke
test and judged pass. Call it **~$220**, hard cap $40/world. Seed-art generation and
rendering are local and free.

## Verification done before launch

- 24 founding artworks build deterministically from `scripts/build_seed_arts.py`
- all 24 are ≤15000 chars, pass `validate_art(no_words=True)`, and render non-blank in
  chromium at 800×800 (>8 distinct colours); every seed inspected by eye
- six charters, one ~80-word creed paragraph each, no game-mechanic vocabulary
- `tests/test_new_aesthetics.py` 64 green; experiment suite 293 green; repo suite 71 green
- the v2 packs are byte-identical after the builder change (asserted by a test)
