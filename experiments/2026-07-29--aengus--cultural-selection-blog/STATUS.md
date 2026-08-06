# STATUS — cultural-selection blog experiments

*Operational state. Updated at every phase change. Timestamps UTC.*

## Layout
- `scripts/` — runnable pipelines (judge tournament, fleet launcher, plots)
- `src/` — shared library code (rendering, judging, elo, cost tracking)
- `data/` — sampled/rendered inputs (gitignored; regenerable from runs/)
- `results/` — metrics, plots, ELO tables (small ones committed)
- `tests/` — pytest, grows with every bug
- `SCRATCHPAD.md` — hypotheses + current state (gardened)
- `COSTLOG.md` — every API spend: date, phase, $, tokens, wall time

## Phase: MOVE 1 — blind judge tournament (task #1)
- 2026-08-06 03:40 UTC: scaffolding + builder agent launched.
- Data sources (absolute paths, main checkout):
  - v7: runs/messiah-v7/sacrament_snapshots.jsonl (4,445 versions)
  - v8: runs/messiah-v8/sacrament_snapshots.jsonl (1,355 versions)
  - minimal/ExpIX: outputs/2026-07-12-minimal-cultural-selection/ (artworks + jsonl)
- Judges: gemini-2.5-flash + claude-haiku (keys in main checkout .env)
- Renderer: /usr/bin/chromium headless screenshot
- Gate: pilot 30 judgments → report cost math before scaling to ~2000.

## Monitors
- (none running)

## Cumulative spend
- $0.00
