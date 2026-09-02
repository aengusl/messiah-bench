# Repo map

The directory tour. `CLAUDE.md` has the conventions and how-to-run instructions;
`README.md` is the public description of the project.

## experiments/ — the first port of call

**New experimental code goes in `experiments/`, not at the repo root.** One dated
directory per experiment, `YYYY-MM-DD--aengus--slug`, and each keeps its own code,
prompts, results and status docs. `src/` is only for the shared long-lived engines.

| Directory | What it is |
|---|---|
| `2026-06-21--aengus--data-analysis` | Notebooks, plots and quotes from v1–v6 |
| `2026-06-21--aengus--v7-sim-design` | `PLAN.md` — the v7 design (supersedes `docs/archive/v7-plan.md`) |
| `2026-06-22--aengus--v8-pr-governance` | `DESIGN.md` — the v8 design |
| `2026-07-12-minimal-cultural-selection` | The minimal two-verb (make/choose) engine: own `run.py`, prompts, publisher, `FINAL_RESULTS.md` |
| `2026-07-29--aengus--cultural-selection-blog` | **Currently active** |

## src/ — the shared engines

| File | What it is |
|---|---|
| `sim.py` | Religion & The Machine — the original 12-agent ecology, no win condition |
| `messiah_bench.py` | Messiah Bench v1–v3: civilians + goal-directed messiahs |
| `messiah_bench_v4.py` | v4 (badly rate-limited; ~39% of actions fell back to idle) |
| `messiah_bench_v5.py` | v5: scaling sacrament returns, smaller population |
| `messiah_bench_v6.py` | v6: sacrament fixes. Best art, but agents escalated CSS to unrenderable values |
| `messiah_bench_v7.py` | v7: messiahs locked to their religion, restricted founding → stable pluralism, no winner |
| `messiah_bench_v8.py` | v8: PR-governed art + mortal messiahs. Art governance worked; the war kill-bonus did not |
| `main.py` | Trivial entry stub |

**Run directories.** Each engine sets `BASE_DIR = Path(__file__).resolve().parents[1]`,
i.e. the repo root even though the engine lives in `src/`. `.env` and the default run
directory both hang off that, so runs never write inside `src/`. Passing `--run-dir=` is
cwd-relative and overrides the default — which is why everything runs from the repo root.
Note `messiah_bench_v8.py` defaults to `runs/messiah-v7` (a pre-existing copy-paste bug);
harmless, because `scripts/launch_v8.sh` always passes `--run-dir=runs/messiah-v8`.

## scripts/ — launch, publish, build

Run all of these **from the repo root**. The launchers `cd "$(dirname "$0")/.."` first,
so `bash scripts/launch_v8.sh` works from anywhere and `--run-dir=runs/messiah-vN`
(a cwd-relative path) always lands in the repo-root `runs/`.

- `launch_v5.sh` … `launch_v8.sh` — start the matching engine in a detached tmux session,
  writing to `runs/messiah-vN/` and teeing `sim.log`. Override with `SESSION=` / `RUN_DIR=`.
- `launch_v4_when_ready.sh` — historical: waits for v3 to exit, then launches v4.
- `update_gallery.sh`, `update_gallery_v5.sh`, `update_gallery_v6.sh` — polling loops that copy
  sacrament HTML from `runs/<run>/sacraments/` into the website repo and push.
- `build_galleries.py` — per-version gallery pages from `runs/messiah-vN/world_state.json`.
- `build_blog.py` — builds `religion_and_the_machine.html` from the v7/v8 world states.

Both build scripts derive the repo root from their own location, so they work from
any checkout or worktree.

## Data

- `runs/` — one directory per Messiah Bench / Religion run. **Run data, not regenerable.**
  The bulky parts (`sacraments/`, `logs/`, `world_state.json`, dashboards) are gitignored
  by design; the monitor/watchdog scripts and small summaries are tracked.
  These directories are **historical**: their `STATUS.md` / `README.md` record the commands
  as they were run at the time, when engines lived at the repo root. Don't "fix" those paths —
  they're a record. Use the `scripts/` invocations above for anything new.
- `outputs/` — raw output from the minimal-cultural-selection engine (~600MB). Gitignored.
- `assets/blog/` — plots used by the blog build.
- `gallery.html`, `religion_and_the_machine.html` — generated pages checked in at root.

## docs/

- `MINIMAL_GAME_DESIGN.md` — the minimal make/choose design (linked from the live website)
- `HOW_TO_VIEW.md` — serving dashboards and galleries locally / over SSH
- `260322-religion_and_the_machine_report.md` — the original v1 lab report
- `religion_and_the_machine_2026-03_original.html` — the original site snapshot
- `archive/` — superseded root docs; see `docs/archive/README.md`

## tests/

`uv run pytest tests/ -q`. The suite imports the engines by bare module name via a
`sys.path` insert of `src/` in `tests/conftest.py`.
