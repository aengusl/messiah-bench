# Cultural selection → blog post: scratchpad

*Gardened. Prune aggressively. Bayesian: hypotheses with credences, updated on evidence.*

## The big question (candidate thesis)
**How does cultural context inspire art?** — cultures, not individuals, create art. You don't need humans to make art; you need cultures.

Candidate thesis: *Beautiful art (churches!) emerges for locally strategic reasons — cultures compete, and art is a weapon of cultural expansion.*

## Key hypotheses (credences = priors, to update)
- H1 (0.7): Variation in cultural context → measurable variation in art quality/novelty (culture is the generator, agent is the pen).
- H2 (0.6): Competitive pressure (expansion, conversion, violence) increases art quality vs. peaceful pluralism.
- H3 (0.5): Art degrades under monoculture (v1-v6 collapse data supports); pluralism sustains novelty.
- H4 (0.4): Different initializations (seeded aesthetics/values) produce persistently divergent art lineages, not convergence.

## Current state of the world (scans complete)
- Best build platform: minimal make/choose engine (`experiments/2026-07-12-minimal-cultural-selection/run.py`), ~$7/1000-turn run, 24 agents, influence economy. Experiment IX ended in monoculture ("art became currency").
- v7 = stable pluralism (locked messiahs); v8 = PR curation composed art but war failed. Per-version art snapshots exist only for v7/v8/minimal.
- Website: `/cultural-selection/` built by `publish_website.py` + `website_template.html`; narrative phases/quotes hardcoded in publisher.
- BRAINSTORM.md written: thesis, 6 claims, sub-agent fleet, E1-E3 experiment designs.

## Goal
Complete the experiments required for a Twitter post (Aengus /goal, 2026-08-06).

## Progress
- DONE: six culture charters + integration notes (results/charters/, run.py:76 injection via --charter-file). Key design note: temp 0.9 → n=1 per charter is anecdote; need ≥3 replicates.
- IN FLIGHT: Move 1 judge harness (builder agent); repo-wide restructure + CLAUDE.md (gardener agent).

## Next actions (priority order)
1. Audit builder's harness → run 30-pair judge pilot → cost math → scale to ~2000 pairs (Move 1; tests claims 2+3).
2. Twin worlds: smoke test 1 charter ~50 turns → 18-run fleet (6 conditions × 3 reps, 300 turns) (Move 2; claim 1).
3. Threat-dial mechanic + sweep (Move 3; claim 4).

## To prune next pass
- Threat-dial mechanic details (design when Move 2 launches).
