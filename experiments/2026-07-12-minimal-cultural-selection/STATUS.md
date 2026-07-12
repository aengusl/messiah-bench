# Minimal Cultural Selection — Status

Updated: 2026-07-12 UTC (engine validation)

## Hypothesis

Agents will voluntarily spend scarce turns making cultural artifacts when those artifacts can influence other agents' religious choices, even though making has no direct reward.

## Phase

Deterministic engine validation.

## Plan

1. Build a fresh choose/make engine.
2. Pass deterministic dry-run, tests, schema, render, replay, and resume checks.
3. Run an 8-agent paid Gemini smoke test and inspect its first decisions.
4. Create and QA an editable design deck.
5. Launch 24 Gemini 2.5 Flash agents for 100 turns in tmux.
6. Monitor the run and update the deck/site from actual evidence.

## Run configuration

- Model: `gemini-2.5-flash`
- Pilot: 24 agents, 4 seed religions, 100 turns
- Proposal lifetime: 3 turns
- Initial life: 20
- Workers: 8 initially; tune only after smoke test
- Hard cost cap: $100

## Persistence

CANONICAL OUTPUT: outputs/2026-07-12-minimal-cultural-selection/

Expected files include `world_state.json`, `events.jsonl`, `decisions.jsonl`, `observations.jsonl`, `versions.jsonl`, `artworks/`, `renders/`, and `site/`.

## Launch

- Tmux session: not launched
- PID: not launched
- Command: pending validation
- Log: `experiments/2026-07-12-minimal-cultural-selection/run.log`
- Monitor: `experiments/2026-07-12-minimal-cultural-selection/monitor.log`

## Progress log

- 2026-07-12: Created experiment directory and confirmed Gemini SDK, Chromium, Node, and pdftoppm are available.
- 2026-07-12: Defined support as a per-turn choice. `choose` contributes support; `make` does not. This prevents automatic equilibrium and makes cultural production genuinely costly.
- 2026-07-12: Completed first 6-agent/10-turn scripted run: 60 decisions, 4 proposals, 2 accepted versions, all agents alive, $0 spend.
- 2026-07-12: Six of seven focused tests passed. The remaining failure was a test expecting resolution before the full three-turn proposal window; corrected the test boundary.

## Next step

Rerun tests and schema checks, then commit/push the engine milestone.
