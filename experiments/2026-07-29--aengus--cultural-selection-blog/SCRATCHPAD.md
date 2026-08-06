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
- **RETRACTED: round-1 regime ranking (minimal 1799 > v8 1433 > v7 1312).** Audit found renderer blanks v7/v8 art (render-success 38%/73%/100%, exactly monotonic with ELO) — v7/v8 use SVG+animation+blur our screenshot doesn't paint; minimal also embeds legible doctrine text judges cite. Judged on renderer compatibility, not art. Round 2 killed at $0.31. Auditor also found: Gemini 62% slot-A bias (discounts half of votes); ELO math + spot checks clean (10/10); elo.csv silently drops 36 low-game artworks. → retractions ledger.
- **BLOCKED (render fix)**: builder-move1 diagnosing blank IDs, forcing animations to end-state, adding distinct-colour render gate to separate render failure from genuinely degenerate art. Rejudge only after per-regime render table looks sane.
- H2 prior unchanged at 0.5 (evidence invalidated, not reversed). Process bugs logged: dry-run must not write files; pair_index not a unique key across runs.
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
