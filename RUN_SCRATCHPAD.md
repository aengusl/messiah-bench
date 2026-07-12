# Minimal Cultural Selection — Live Scratchpad

Last updated: 2026-07-12 UTC

## Current state

- Phase: engine validation
- Status: implementation complete enough for deterministic dry-run; correcting one test boundary before the paid smoke test
- Canonical output: `outputs/2026-07-12-minimal-cultural-selection/`
- Tmux session: not launched yet
- Latest completed checkpoint: 6-agent, 10-turn scripted dry-run

## Budget and cost

- Hard stop: **$100**
- Actual API cost so far: **$0.00**
- Paid model calls so far: **0**
- Current projection: pending the 8-agent smoke test; projection will use its measured tokens per action
- Stop conditions: cost reaches $100, authentication fails, more than 5% of actions are invalid, or the same phase fails twice

## ETA

- Tests and deterministic validation: approximately 15–30 minutes
- Paid smoke test and inspection: approximately 15–30 minutes after tests pass
- Design deck draft and QA: approximately 30–60 minutes
- Pilot launch: after smoke output is valid and projected cost remains below budget
- Full 100-turn pilot duration: to be estimated from measured smoke-test turn latency

ETAs are estimates and will be replaced with measured rates as soon as live calls begin.

## Latest evidence

- Chromium successfully rendered seed and proposal artwork.
- The scripted run produced 60 decisions, 60 observations, 4 proposals, and 2 accepted cultural versions.
- Resume and static-site generation checks passed.
- One test expected a three-turn proposal to resolve one turn too early; the engine behavior matched the written rule and the test boundary is being corrected.

## Next actions

1. Rerun the complete experiment test suite.
2. Verify JSON schemas and replay-relevant logs.
3. Commit and push the engine milestone.
4. Run one small paid Gemini smoke test.
5. Recalculate budget and ETA from actual usage.
