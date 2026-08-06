# Repo map

A guide to what lives where. `README.md` is the public-facing description of the
project; this file is for whoever has to work in the repo.

## Engines (root-level, do not move — scripts reference them by root path)

| File | What it is |
|---|---|
| `sim.py` | Religion & The Machine — the original 12-agent ecology, no win condition |
| `messiah_bench.py` | Messiah Bench v1–v3: 100 civilians + 5 goal-directed messiahs |
| `messiah_bench_v4.py` | v4 |
| `messiah_bench_v5.py` | v5: scaling sacrament returns, smaller population |
| `messiah_bench_v6.py` | v6: sacrament fixes (conflict resolution, error fallback, full reasoning logged). Best art, but agents escalated CSS to unrenderable values |
| `messiah_bench_v7.py` | v7: messiahs locked to their religion, restricted founding. Result: stable pluralism, no winner |
| `messiah_bench_v8.py` | v8: PR-governed art + mortal messiahs. Art governance worked; the war kill-bonus did not |
| `main.py` | Trivial entry stub |

Design docs for the later versions: `MINIMAL_GAME_DESIGN.md` (root, linked from the
live website — don't move it), `experiments/2026-06-21--aengus--v7-sim-design/PLAN.md`,
`experiments/2026-06-22--aengus--v8-pr-governance/DESIGN.md`.

## Scripts

- `launch_v4_when_ready.sh`, `launch_v5.sh`, `launch_v6.sh`, `launch_v7.sh`, `launch_v8.sh`
  — start the matching engine in a detached tmux session, writing to `runs/messiah-vN/`
  and teeing `sim.log`. Override with `SESSION=` / `RUN_DIR=`.
- `update_gallery.sh`, `update_gallery_v5.sh`, `update_gallery_v6.sh` — polling loops that
  copy sacrament HTML from `runs/<run>/sacraments/` into
  `~/projects/aengusl.github.io/messiah-bench/` and push the live site.
- `build_galleries.py` — builds gallery pages from `runs/messiah-vN/world_state.json`
  plus that run's `sacraments/`.
- `build_blog.py` — builds `religion_and_the_machine.html` from the report + `assets/blog/`.

## Data and outputs

- `runs/` — one directory per run (`v1`, `v2`, `messiah-v1`…`messiah-v4`, and whatever the
  launch scripts create). This is **run data, not regenerable** — the bulky parts
  (`sacraments/`, `logs/`, `world_state.json`, dashboards) are gitignored by design;
  the monitor/watchdog scripts and small summaries are tracked.
- `assets/blog/` — plots used by the blog build.
- `gallery.html`, `religion_and_the_machine.html` — generated pages checked in at root.
- `docs/` — `religion_and_the_machine_2026-03_original.html` (the original site snapshot)
  and `docs/archive/` (superseded root docs; see `docs/archive/README.md`).

## Experiments

One directory per piece of analysis or follow-on work, named `YYYY-MM-DD--owner--slug`:

- `2026-06-21--aengus--data-analysis` — notebooks, plots and quotes from v1–v6
- `2026-06-21--aengus--v7-sim-design` — the v7 plan (supersedes `docs/archive/v7-plan.md`)
- `2026-06-22--aengus--v8-pr-governance` — v8 design
- `2026-07-12-minimal-cultural-selection` — the minimal two-verb (make/choose) run:
  its own `run.py`, prompts, publisher and `FINAL_RESULTS.md`
- `2026-07-29--aengus--cultural-selection-blog` — **currently active**

## Tests

`tests/` (`test_sim.py`, `test_messiah.py`) — `uv run pytest`.

## Other root docs

- `HOW_TO_VIEW.md` — how to serve dashboards and galleries locally / over SSH
- `260322-religion_and_the_machine_report.md` — the original v1 lab report
