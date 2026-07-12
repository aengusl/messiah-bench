# Minimal Cultural Selection — Live Scratchpad

Last updated: 2026-07-12 UTC

## Current state

- Phase: live pilot
- Status: pilot healthy at turn 44; separate live exhibition pushed and awaiting GitHub Pages deployment
- Canonical output: `outputs/2026-07-12-minimal-cultural-selection/`
- Tmux session: `260712-minimal-pilot`
- Monitor session: `260712-minimal-watch`
- Website publisher session: `260712-minimal-publish`
- Latest completed checkpoint: 6-agent, 10-turn scripted dry-run

## Budget and cost

- Hard stop: **$100**
- Actual API cost so far: **$3.424** ($0.155 preflight + $3.269 pilot)
- Pilot calls so far: **1,056**, all valid
- Current projection: **about $6.57 pilot cost at the current rate**, with a conservative **$10–$20** allowance as proposals add images
- Stop conditions: cost reaches $100, authentication fails, more than 5% of actions are invalid, or the same phase fails twice

## ETA

- Tests and deterministic validation: approximately 15–30 minutes
- Corrected paid smoke test: complete
- Design deck draft and first fix-and-verify QA cycle: complete
- Pilot launched: **2026-07-12 23:02 UTC**
- Expected completion: approximately **23:18–23:30 UTC** based on the first nine turns; proposal growth may slow later turns

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

## Next actions

1. Confirm the queued GitHub Pages deployment and public URL.
2. Update and push this scratchpad at meaningful checkpoints.
3. Diagnose immediately if invalid actions exceed 5% or logs stop changing.
4. Update the deck with final trajectories after completion.
