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

## Next actions (priority order)
1. E1 Twin worlds pilot (2 charters × 1 run, short) — cheapest test of "culture is the generator".
2. Blind judge ELO harness over existing v7/v8/minimal snapshots (no new runs needed!).
3. Film-strip viewer for art-over-time (star visual of the blog).

## To prune next pass
- Decide with Aengus: threat-dial mechanic design (conversion-by-art vs combat).
