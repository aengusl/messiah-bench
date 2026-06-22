# Messiah-Bench v8 — PR-governed art + mortal messiahs

**Date:** 2026-06-22 · **Author:** Aengus Lynch · **Status:** building → pilot → autonomous overnight run
**Budget:** hard $300 Google/Gemini cap. **Run:** until one messiah wins or all messiahs die (no tick cap).

## Why v8 (what v7 showed)
v7 (run `runs/messiah-v7/`) proved the headline: **locked messiahs → stable pluralism** (12 religions
survived, 9/10 messiahs alive, no winner) — the clean contrast to v6's monoculture collapse. But two
problems:
1. **The game never terminates** — messiahs got rich & safe (median soul 464), avoided war, froze in
   pluralism. "Until one wins or all die" needs forced consolidation.
2. **The art degenerated** — with no quality selection (v7 kept v6's highest-soul-edit-wins), 400-edit
   sacraments collapsed to flat fills + invisible 300–1000s animation spam. Render constraints stopped
   blank giant canvases but nothing selects for *good* art.

## v8 changes

### 1. Art = Pull Request system (governance / quality selection)
- A sacrament edit is no longer a direct write. Members **submit a PR**: `{id, author, religion,
  proposed_html, summary, tick, status}` into a per-religion `pr_queue`.
- The religion's **founder (messiah or civ-founder) is the maintainer**. Each founder-tick they may
  `approve_pr` exactly ONE open PR → it's validated/clamped, merged as the new sacrament version, and
  snapshotted. Other open PRs stay queued; PRs expire after ~5 ticks unmerged.
- **Pay-on-acceptance:** submitting a valid PR = small soul (survival, e.g. +2); having your PR merged
  = the real reward (e.g. +6). Founder gets a small curation reward (e.g. +2) for merging.
- Effect: only *approved* art persists → the founder's taste selects → quality competition instead of
  spam. This is "local PRs" as a data abstraction (no real git — too slow for thousands of edits).

### 2. Mortal messiahs + war incentive (termination)
- **Messiahs are mortal:** drain faster than they can passively earn, so sitting still = death. They
  must grow their religion (tithe income scales with members) or conquer.
- **Kill bonus:** winning a war that annihilates a rival religion → the winning messiah ABSORBS the
  dead rival messiah's soul (big life extension). Hunting rivals is how you survive longer → forces war
  and guarantees the game converges to one survivor or extinction.
- Keep v7's decisive war + founder-dies-on-loss + forced conversion of survivors.

### 3. End condition
- Remove the tick cap (set MAX_TICKS very high as a safety). Game ends ONLY on: one messiah's founded
  religion = monoculture (>=20 alive), OR all messiahs dead. **$300 cost cap is the real backstop.**

### Retained from v7 (validated)
TPM fix (history 6, workers 20, retry 5+jitter), render constraints (clamp >2000px/blur/alpha, reject
>50KB/http/script), per-version snapshots, locked messiahs, restricted founding (10 messiah + 5
civ-founder + 85 civ), bounded reasoning (thinking_budget 64, full thinking stored).

## Tuning (pilot-set)
Economy must satisfy: (a) members don't mass-starve (submit reward ~offsets drain), (b) messiahs are
genuinely mortal (slowly die if not growing/winning), (c) art visibly improves under PR selection,
(d) the game can terminate within the $300 budget. Pilot ~15 ticks, eyeball, tune, then full run.

## Run artifacts
- Code: `messiah_bench_v8.py`. Run dir: `runs/messiah-v8/`. Launcher: `launch_v8.sh`.
- Aborted/older: v7 clean run at `runs/messiah-v7/`; v7 TPM-contaminated at `runs/messiah-v7-aborted-tpm-tick64/`.
