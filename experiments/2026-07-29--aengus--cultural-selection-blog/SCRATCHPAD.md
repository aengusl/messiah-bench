# Scratchpad — cultural selection blog experiments

> **Usage:** This file holds ONLY the present: state of the world, hypothesis board, open uncertainties, next steps, budget. Closed rounds and narratives move to LOG.md the moment they stop being actionable. Overwrite stale content, never stack. Budget numbers are measured (COSTLOG.md), never estimated from memory. Point to evidence files; never inline evidence.

## Goal
Experiments sufficient for a Twitter thread → blog post. Thesis: **culture, not the individual, is the artist; beauty is locally strategic.** (Claims list: BRAINSTORM.md. Motivation memory: cultural-selection-thesis.)

**What I want to be true (guard against):** that culture charters cause big art divergence and competition improves art. Falsification attempts get priority.

## Hypothesis board (ordered by value-of-falsification)
- **H1 Culture is the generator** — P ≈ 0.7. Charters cause persistent art-lineage divergence. Falsifier: twin worlds converge to indistinguishable art by blind-judge + embedding distance (charter effect ≤ replicate noise). If false: model prior is the artist → blog thesis rewritten around "the model is the culture."
- **H3 Monoculture kills art** — P ≈ 0.6. Art quality (blind ELO) declines after ExpIX consolidation (~turn 272+). Falsifier: flat/rising ELO across collapse. If false: collapse tweet dies; pluralism framing weakens.
- **H2 Competition breeds beauty** — P ≈ 0.5. Regime ranking: competitive regimes > locked pluralism. Early pilot signal (n=30 pairs): minimal 35 > v8 21 > v7 4 wins — but confounded (v7 art embeds text, render era differs). Falsifier: ranking driven by confounds or judge taste.
- **H4 Threat sharpens art** — P ≈ 0.4. Untested until Move 3.

## State of the world (2026-08-06 04:45 UTC)
- **RUNNING** fleet: 18 twin worlds × 300 turns in tmux (`260806-twin-*`), ETA 2-4h, per-world cap $40. Monitor bucr75ps2 (5-min watchdog: completion/crash/error-storm).
- **RESOLVED (2 reversals, both logged in retractions):** (a) round-1 ELO ranking retracted — measured emptiness, not aesthetics; (b) auditor's "renderer artifact" cause overturned by builder's ground-truth check vs the v7 engine's own renders: **the art is genuinely blank.** v7: 90.7% truncated mid-tag, 60.7% nothing paintable; v8: 78.7%/42.6%; minimal: 0%. Cause = generator truncation (sim token limits), not renderer. Renderer hardened anyway (definite-size frame, truncation repair, animation pinning, per-render profile; render_report.jsonl gate) — 89 tests, commit 8ddf0e7. 2/300 unexplained render failures (flagged, not hidden).
- **DECISION:** no cross-regime aesthetic ELO on this corpus (completeness confound, self-selected paintable subsample). Instead: **truncation/completeness rate is the claim-2 finding** — pay-per-edit regimes produced mostly unrenderable fragments; adoption-gated regime (make/choose) produced 100% paintable canon. Measurable from files, no judges needed. Aesthetic comparisons → twin-worlds corpora only (render 100%).
- **FINDING (judge-free degradation curves, results/completeness_*):** paintable-art rate over each run's life: v7 65%→18%, v8 97%→27%, minimal flat 100%. v7 median drawable elements = 0.
- **FALSIFIED: adoption-gate mechanism.** Rejected proposals as complete as accepted (0%/0% truncated) — the gate filtered nothing; minimal's advantage is upstream in generation. Surviving mechanism: **elaboration correlates with truncation** (truncated art is LARGER: v7 4314 vs 2844 median bytes) — works die spending their output budget on defs/keyframes preambles. State as correlation, not "token cap did it" (no hard byte ceiling in data).
- Caveats pinned: minimal n=86 vs v7 4,445; different engine; completeness ≠ beauty (2 rectangles pass). Gemini judge slot-A bias (62%) noted for future judging.
- Process bugs logged: dry-run must not write files; pair_index not unique across runs; chromium profile dirs must be per-render.
- Built + committed: judge harness (68 tests), twin-worlds injection + launcher (79 tests), repo restructure, CLAUDE.md/MAP.md.
- Known confounds for H2: artworks embed religion names/doctrine (not fully blind); v7 degenerate art renders blank (scores low, arguably correctly).
- ANTHROPIC key: repo .env stale; working key = just-find-misalignment .env via env override.

## Next steps (re-rank at each milestone)
1. Judge tournament done → `--results` → ELO curves → update H2/H3 priors → independent spot-check agent on 10 random judgments.
2. Smoke world done → validate charter reached prompts (world_state charter field, agent reasoning mentions asceticism) → launch 18-world fleet (~$400, staggered if 429s).
3. Design Move 3 threat-dial pre-registration in docs/ before building.
4. Progress artifact page (single URL, data-driven, retractions ledger).

## Budget ledger (measured)
- Judging: $0.086 (pilots incl. failed-key run) — COSTLOG.md
- Smoke worlds: $0 (failed run) + ~$3 in flight (read final from run.log usage line)
- Committed spend ceiling agreed with Aengus: lean pass ~$300, max ~$800.
