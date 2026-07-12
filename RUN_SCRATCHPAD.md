# Minimal Cultural Selection — Live Scratchpad

Last updated: 2026-07-12 UTC

## Current state

- Phase: launch readiness
- Status: corrected 8-agent smoke passed technically and behaviorally; deck generated and visually QA'd
- Canonical output: `outputs/2026-07-12-minimal-cultural-selection/`
- Tmux session: not launched yet
- Latest completed checkpoint: 6-agent, 10-turn scripted dry-run

## Budget and cost

- Hard stop: **$100**
- Actual API cost so far: **$0.155** (one-agent check plus two 8-agent smoke runs)
- Paid model calls so far: **81**
- Current projection: **about $5–$8 measured / $10–$20 conservative** for 2,400 pilot actions
- Stop conditions: cost reaches $100, authentication fails, more than 5% of actions are invalid, or the same phase fails twice

## ETA

- Tests and deterministic validation: approximately 15–30 minutes
- Corrected paid smoke test: complete
- Design deck draft and first fix-and-verify QA cycle: complete
- Pilot launch: next
- Full 100-turn pilot duration: approximately **25–40 minutes** from measured smoke latency, with additional time possible as proposal images accumulate

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

## Next actions

1. Commit and push the corrected design, scratchpad, and deck.
2. Launch the 24-agent/100-turn pilot in tmux.
3. Start a persistent monitor and record exact process/session details.
4. Inspect early turns for make rate, invalid rate, cost, and artwork quality.
