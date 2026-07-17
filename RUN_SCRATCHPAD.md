# Minimal Cultural Selection — Live Scratchpad

Last updated: 2026-07-12 UTC

## Current state

- Phase: turn-1,000 extension running
- Status: canonical society resumed successfully; new proposals appeared immediately
- Canonical output: `outputs/2026-07-12-minimal-cultural-selection/`
- Tmux session: `260712-minimal-pilot`
- Monitor session: `260712-minimal-watch`
- Website publisher session: `260712-minimal-publish`
- Latest completed checkpoint: 6-agent, 10-turn scripted dry-run

## Budget and cost

- Hard stop: **$100**
- Cost through turn 100: **$7.3383**
- Preflight smoke cost: **$0.1554**
- Extension projection: **approximately $71–$78 additional; $78–$85 cumulative**
- Hard cost cap: **$100 cumulative pilot spend**
- Calls through turn 100: **2,400 / 2,400 valid**
- Stop conditions: cost reaches $100, authentication fails, more than 5% of actions are invalid, or the same phase fails twice

## ETA

- Tests and deterministic validation: approximately 15–30 minutes
- Corrected paid smoke test: complete
- Design deck draft and first fix-and-verify QA cycle: complete
- Pilot launched: **2026-07-12 23:02 UTC**
- Extension target: **turn 1,000** (900 additional turns)
- Extension launched: **2026-07-17 04:16 UTC**
- Measured ETA: approximately **08:00–08:45 UTC** (3.5–4.5 hours total)

ETAs are estimates and will be replaced with measured rates as soon as live calls begin.

## Latest evidence

- Chromium successfully rendered seed and proposal artwork.
- The scripted run produced 60 decisions, 60 observations, 4 proposals, and 2 accepted cultural versions.
- The first live action was valid and cost $0.0011.
- The 8-agent smoke produced 40/40 valid actions for $0.0709, but every action was `choose`; stable self-support gave agents no reason to make.
- Cultural-influence correction worked: the second smoke produced 1 voluntary `make`, followed by 2 other-agent choices of that proposal. Ember explicitly made because no one had influence and expected Axiom to choose the work.
- Corrected smoke: 40/40 valid actions, 8 alive, 1 proposal, top influence 2, $0.0834.
- Artwork render inspected successfully; doctrine and geometry were visibly revised.
- Eight-slide editable deck generated. Visual QA found missing artwork on slide 5, fixed the source path, and verified the repaired slide plus slides 1, 6, and 8.
- Pilot turn 9: 24 alive, 4 religions, 6 make actions, 5 open proposals, 1 accepted version, 0 invalid actions.
- Cairn's first proposal attracted 13 other-agent choices by turn 9. Top influence is 13.
- Persistent monitoring moved to exact tmux session `260712-minimal-watch` after the initial detached watcher was cleaned up by its launch shell.
- New website page: `https://www.aenguslynch.com/cultural-selection/`. Initial turn-37 snapshot pushed at website commit `c666ffc`; GitHub Pages deployment is queued.
- Live publisher updates the separate page every ten turns without modifying the existing Messiah Bench page.
- Final: 24/24 alive, 26 makes, 2,374 choices, 21 accepted works, 5 rejected, 4 religions, $7.3383 pilot cost.
- Brine won with influence 318. Tide reached 304, Ash 278, Echo 189.
- Making ended after turn 54. Turns 55–100 were a consolidation phase in which canonical authors accumulated influence.
- Final website includes a scrollable seven-version evolution of The Verdant Archive.
- Editable deck updated in place to ten slides with final metrics and the convergence finding.

## Next actions

1. Monitor progress, cost, and invalid rate at durable checkpoints.
2. Stop if cumulative cost reaches $100 or invalid actions exceed 5%.
3. Completion watcher publishes the website only after the extension sentinel appears.
