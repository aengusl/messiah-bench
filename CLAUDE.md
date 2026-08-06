# CLAUDE.md

Instructions and conventions for working in this repo. For the directory tour, read
[MAP.md](MAP.md). For the public description of the project, read [README.md](README.md).

## What this project is

LLM agent societies that compete through culture. Cheap agents found religions, produce
visual artwork as sacraments, persuade each other, and die. The artwork is the instrument
of persuasion, not decoration — agents demonstrably choose religions because the art is better.

Two lines of work:
- **Messiah Bench v1–v8** (`src/`): 100 agents, one rule changed per version. v7 (messiahs
  locked to their founded religion) produced stable pluralism; v8 (PR-governed art + mortal
  messiahs) kept the art composed but the war kill-bonus failed and messiahs went extinct.
- **The minimal engine** (`experiments/2026-07-12-minimal-cultural-selection/`): the current
  line. Two verbs, *make* and *choose*. Its own `run.py`, not shared with `src/`.

Prior findings are in memory: `messiah-bench-key-findings`, `messiah-v7-run-result`,
`messiah-v8-run-result`, `cultural-selection-thesis`. Read them before designing a new run.

## Where code goes

**`experiments/` is the first port of call for experimental code.** New work gets a dated
directory, `YYYY-MM-DD--aengus--slug`, and keeps its own code, prompts and results inside it.
Only promote something to `src/` once it is a shared, long-lived engine.

Each experiment dir keeps a gardened `STATUS.md` (current state, cost so far, next action)
and a `SCRATCHPAD.md` (running log). Update them as you go; archive them when the run ends.
Log costs — every run has a hard cap and it must be checkable at a glance.

`runs/` and `outputs/` are raw run data. Never commit them wholesale (`outputs/` alone is
~600MB and is gitignored). Commit scripts, configs and docs, not regenerable artifacts.

## Running a simulation

```bash
bash scripts/launch_v8.sh          # detached tmux session, from the repo root
tmux attach -t 2026-06-22-messiah-v8
tail -f runs/messiah-v8/sim.log
```

**Always run from the repo root.** Launchers `cd` there themselves and take `SESSION=` /
`RUN_DIR=` overrides; `--run-dir=` is cwd-relative. The engines resolve `BASE_DIR` to the
repo root (not to `src/`), so `.env` loads and default run dirs land in `runs/` — don't
change that to `Path(__file__).parent` or runs will start writing inside `src/`.

Always smoke-test before a full launch: `--dry-run`, then `--debug --ticks=1`, then check
cost and invalid-action rate before scaling. `uv run pytest tests/ -q` should be **71 passed**.
If you see failures about `haiku` or `CIVILIAN_MODEL_ROTATION`, you're running stale
bytecode — `/bin/rm -rf tests/__pycache__ src/__pycache__ .pytest_cache` and rerun.

## Publishing to the website

The site repo is `/home/aenguslynch/projects/aengusl.github.io`.

- Messiah Bench galleries: `scripts/build_galleries.py`, `scripts/update_gallery_v6.sh`.
- The cultural-selection page: `experiments/2026-07-12-minimal-cultural-selection/publish_website.py`.
  **Edit `website_template.html`, never the published `index.html`** — the publisher
  regenerates it and your edits are lost.

## Conventions

- Python via `uv`. Never `pip install` outside a venv.
- API keys in `.env`: `GOOGLE_API_KEY` (Gemini, every agent from v5 on), `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY` (only the mixed-model v1–v4 runs).
- `PYTHONUNBUFFERED=1` when piping to a log file.
- Always `/bin/rm`, `/bin/cp`, `/bin/mv` — the bare commands are aliased to `-i` and hang.
- Never `git add -A`. Stage named paths. Never symlink; copy.
- Colors in terminal output, `--dry-run` flags on anything that spends money or writes data.
- Naming is `YYYY-MM-DD-descriptive-name` everywhere: experiments, outputs, tmux, branches.
- Write to new files; never overwrite source data. Temp name, rename on success.
