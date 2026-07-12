# Minimal Cultural Selection — Status

Updated: 2026-07-12 UTC (engine validation)

## Hypothesis

Agents will voluntarily spend scarce turns making cultural artifacts when those artifacts can influence other agents' religious choices, even though making has no direct reward.

## Phase

Pilot running.

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

- Tmux session: `260712-minimal-pilot`
- PID: `1771020` (tmux pane shell)
- Command: `UV_CACHE_DIR=/tmp/uv-cache uv run python experiments/2026-07-12-minimal-cultural-selection/run.py --agents=24 --turns=100 --workers=8 --run-dir=outputs/2026-07-12-minimal-cultural-selection`
- Log: `experiments/2026-07-12-minimal-cultural-selection/run.log`
- Monitor: `experiments/2026-07-12-minimal-cultural-selection/monitor.log`
- Monitor tmux: `260712-minimal-watch`

## Progress log

- 2026-07-12: Created experiment directory and confirmed Gemini SDK, Chromium, Node, and pdftoppm are available.
- 2026-07-12: Defined support as a per-turn choice. `choose` contributes support; `make` does not. This prevents automatic equilibrium and makes cultural production genuinely costly.
- 2026-07-12: Completed first 6-agent/10-turn scripted run: 60 decisions, 4 proposals, 2 accepted versions, all agents alive, $0 spend.
- 2026-07-12: Six of seven focused tests passed. The remaining failure was a test expecting resolution before the full three-turn proposal window; corrected the test boundary.
- 2026-07-12: First live Gemini action passed; $0.0011, 0 errors, private reasoning correctly weighed making against survival.
- 2026-07-12: Eight-agent/5-turn smoke passed technically (40/40 valid, $0.0709) but failed behaviorally: 40 `choose`, 0 `make`. Stable support was a dominant equilibrium.
- 2026-07-12: Added cultural influence: an agent earns influence only when another agent chooses a proposal or canonical version it authored. Making remains unpaid.
- 2026-07-12: Corrected 8-agent/5-turn smoke passed: 40/40 valid, 1 voluntary make, 2 other-agent responses, top influence 2, $0.0834.
- 2026-07-12: Inspected Ember's rendered proposal and reasoning. The agent knowingly spent survival time to make a modest visual/doctrinal revision it expected Axiom to support; Axiom did so on turns 4 and 5.
- 2026-07-12: Generated an eight-slide editable deck. First visual QA found blank images on slide 5; corrected its render path and verified the repair.
- 2026-07-12 23:02 UTC: Launched 24-agent/100-turn pilot in tmux. Monitor PID `1771025`; expected completion 23:27–23:42 UTC based on smoke latency.
- 2026-07-12 23:04 UTC: Turn 9 checkpoint healthy: 24 alive, 6 make actions, 5 open proposals, 1 accepted version, Cairn influence 13, 216/216 valid calls, pilot cost $0.5909.
- 2026-07-12 23:04 UTC: Replaced cleaned-up nohup watcher with persistent exact-name tmux session `260712-minimal-watch`; verified it recorded turn 9.

## Next step

Inspect artwork and proposal competition at turns 15–20; continue monitoring cost and invalid rate.
