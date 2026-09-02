# STATUS — cultural-selection blog experiments

*Operational state. Updated at every phase change. Timestamps UTC.*

## Layout
- `scripts/` — runnable pipelines (judge tournament, fleet launcher, plots)
- `src/` — shared library code (rendering, judging, elo, cost tracking)
- `data/` — sampled/rendered inputs (gitignored; regenerable from runs/)
- `results/` — metrics, plots, ELO tables (small ones committed)
- `tests/` — pytest, grows with every bug
- `SCRATCHPAD.md` — hypotheses + current state (gardened)
- `COSTLOG.md` — every API spend: date, phase, $, tokens, wall time

## Phase: MOVE 1 — blind judge tournament (task #1)
- 2026-08-06 04:05 UTC: PILOT PASSED. 300 sampled (152 v7/118 v8/30 minimal), 299 rendered (1 chromium timeout = degenerate art). 30 pairs × 2 judges, 0 errors, $0.076, 222s. No position bias (Gemini 15/15; Haiku 8/22 B-lean = noise, slots randomized). Inter-judge agreement 70%. Early signal: wins minimal 35 / v8 21 / v7 4.
- ANTHROPIC_API_KEY in repo .env is STALE (401). Working key: just-find-misalignment .env, exported as env var; artlib load_keys now lets env override .env.
- Builder adding --workers concurrency (sequential = 4h for 2000 pairs; target ~30min).
- Known confounds (from builder): artworks embed religion names/doctrine text (not fully blind); degenerate v7 art scores low rather than flagging missing; art-root autoscaling added to avoid size-voting.
- 2026-08-06 03:40 UTC: scaffolding + builder agent launched.
- Data sources (absolute paths, main checkout):
  - v7: runs/messiah-v7/sacrament_snapshots.jsonl (4,445 versions)
  - v8: runs/messiah-v8/sacrament_snapshots.jsonl (1,355 versions)
  - minimal/ExpIX: outputs/2026-07-12-minimal-cultural-selection/ (artworks + jsonl)
- Judges: gemini-2.5-flash + claude-haiku (keys in main checkout .env)
- Renderer: /usr/bin/chromium headless screenshot
- Gate: pilot 30 judgments → report cost math before scaling to ~2000.

## Phase: MOVE 2 — twin worlds (task #2)
- 2026-08-06 04:25 UTC: SMOKE RUNNING. ascetic × 50 turns in tmux 260806-twin-ascetic-r1 → outputs/2026-08-06-twin-smoke-fix-1/ascetic-r1/. Turn 4: 0 errors, $0.057/turn (≈$2.90 total). ETA ~15 min.
- fix-1 because first smoke burned 20 turns on 100% auth errors: worktree had no .env (engines load ROOT/.env; .env is a gitignored secret in the main checkout). Fixed by /bin/cp of .env into worktree + engine fail-fast guard (abort after 3 all-error turns).
- Fleet plan: 6 charters × 3 reps × 300 turns ≈ $400, 2-4h wallclock (Gemini rate limits are the constraint; consider staggering). Per-world cost cap $40.

## Monitors
- bf1ul9jmt: smoke world completion/crash watcher (20s poll, 30min timeout).

## Cumulative spend
- $0.09 (judge pilots incl. failed-key run) + smoke in flight ≈ $3
- See COSTLOG.md for per-call detail.

## 2026-08-06 04:30 UTC — smoke gate PASSED
ascetic-r1 50 turns: $3.41, 1/1200 errors, 24 alive, 13 accepted versions. Charter verified in world_state + agent reasoning ("aligns with the removal principle of the founding charter", 2494 charter mentions, 354 ascetic-vocab lines in decisions.jsonl). Fleet launch queued behind judge tournament (shared Gemini quota).

## 2026-08-06 04:50 UTC — AUDIT: round-1 regime ranking RETRACTED
Renderer fails on v7/v8 SVG/animation/blur art (38%/73%/100% render success, monotonic with ELO headline) + minimal embeds legible doctrine text. Judge r2 killed at $0.31. Gemini slot-A bias 62%. ELO math and 10/10 spot checks clean. Full audit in the team transcript; render fix delegated to builder-move1. Twin-worlds fleet unaffected (minimal-engine HTML renders 100%).

## 2026-08-06 05:00 UTC — Reversal of the reversal: art is GENUINELY blank
Builder ground-truthed our renders against runs/messiah-v7/rendered/ (independent pipeline): same blankness. v7 90.7% truncated mid-tag / 60.7% nothing paintable; v8 78.7%/42.6%; minimal 0%. Cause: generator truncation in sim harness, not renderer. Decision: truncation rate IS the claim-2 finding; cross-regime aesthetic ELO abandoned on this corpus; aesthetics measured only where render=100% (twin worlds). Renderer hardened + render_report gate added (8ddf0e7).

## 2026-08-06 05:20 UTC — Completeness analysis (670c604, 107 tests)
Degradation curves without judges: v7 65%→18% paintable, v8 97%→27%, minimal flat 100%. Gate hypothesis FALSIFIED (rejected proposals as complete as accepted). Mechanism: elaboration correlates with truncation (truncated art larger). Files: results/completeness.csv/.md/.png.

## 2026-08-06 05:40 UTC — futurist-r1 crash + relaunch
Died at init: chromium timeout rendering seed art (launch contention), uncaught. Patched render_art (retry + placeholder fallback), relaunched. 18/18 running. Twin-worlds analysis pipeline built (0662b61, 140 tests); mid-run preview: adherence diagonal 6.4-68x, doctrine within/across cosine 0.268 vs 0.039. H1 looking strong on behavior/text; art-form clustering provisional.

## 2026-08-06 06:55 UTC — FLEET COMPLETE, H1 confirmed
18/18 worlds, $393, 0.2% errors. Final: adherence diagonal 4.7-88x (off-diag max 2.1x); doctrine cosine 0.324 within vs 0.021 across; art F-ratios animated 30.0, colors 10.2, bytes 6.0 (n_drawable 0.74 — element count does not separate). Launched: twin-art judged pass (800 pairs) + threat-dial stage-0 smoke (K=8, 30 turns).

## 2026-08-06 09:25 UTC — Judged pass + dial smoke results
Twin-art aesthetics (1,597 judgments, $2.03): ancestor 70% / ascetic 61% / baroque 59% > control 48% / futurist 47% > nihilist 37% across-charter win rate; judges agree on nihilist-last. Dial smoke (K=8, M=3, $2.12): total monoculture by turn 17 (Ash extinct at first test t9, Open Circuit absorbs all by t17). Pre-reg checkpoint: M=2 smoke launched before main sweep decision.

## 2026-08-06 10:45 UTC — THREAT-DIAL SWEEP COMPLETE ($110, 12/12)
Control: 4/4 religions survive 120 turns, all reps. Any pressure -> total monoculture, dose-dependent speed (median last extinction: K16 t49, K8 t28, K4 t21). Production chilled: proposals 50 -> 44 -> 24 -> 20 by rising pressure despite identical opportunity. H4 (threat sharpens art) heading for reversal: pressure destroys pluralism and chills production. Judged quality pass launched.

## 2026-08-06 11:00 UTC — DIAL JUDGED PASS: pressure sharpens surviving art
1,200 judgments, $1.53, 0 errors: control 40.9% cross-K win rate vs k16 54.0%, k8 55.1%, k4 50.8%; both judges rank control lowest. H4 resolves three-way: quality up, pluralism dead, production chilled. All three moves complete.

## 2026-08-06 18:30 UTC — v1 closed out; scratchpad pruned; v2 (divergent DNA) opened
Aengus: art too samey — all worlds preserved the seed-template circle (baroque-r1 v9 vs ascetic-r2 v9 = same composition, different color). Decision: twin worlds v2 with per-culture founding artworks + no-words rule, all else identical; claims unchanged, H1-visual added. Builder-dna constructing. Prior scratchpad state (04:45 snapshot with all v1 findings/process bugs) is preserved in git history and the entries above.

## 2026-08-06 18:45 UTC — v2 FLEET LAUNCHED (divergent DNA + no-words)
Micro-smoke passed ($1.35): baroque lineage produced genuine wordless ornament (rosettes/guilloche), 11 versions in 10 turns, DNA heritable. Fixed stale min-members test (mine, from M=2 change). Fleet: 18 worlds x 300 turns, out-tag 2026-08-06-twin-worlds-v2, watchdog armed. Prereg: docs/twin_worlds_v2_prereg.md (incl. blind culture-classification outcome, chance=1/6).

## 2026-08-06 21:10 UTC — V2 RESULTS: H1-visual CONFIRMED, perfect classification
Fleet 18/18, $510 (27% over est — dense wordless art = more tokens). Divergence F-ratios exploded vs v1: n_drawable 0.74→449, bytes 212, colors 90, n_svg inf. BLIND CLASSIFICATION: fresh agent sorted 36 anonymized artworks (6/culture, mid+final, shuffled) into cultures 36/36 = 100% vs 17% chance. Vocab diagonal holds (4.7-51x). Judged aesthetics pass running. Total project spend ~$1,043 — above the original $800 ceiling; flagged to Aengus.

## 2026-08-06 21:25 UTC — v2 judged pass ($2.04, 1600 judgments)
Win rates: control 78% > futurist 63% > baroque 62% > ancestor 54% >> ascetic 21% > nihilist 12%. Model judges reward their own home aesthetic (dark glow emblem); 6x cultural range confirms culture moves judged beauty, but ranking = judge-prior-laden. Human curation is the quality signal (per Aengus goal memory). ALL v2 WORK COMPLETE.

## 2026-08-08 01:50 UTC — New-aesthetics fleet launched
Six new culture packs committed (f9cd88f, 293 tests). Ukiyo micro-smoke passed ($0.85): lineage evolves within the woodblock tradition. Fleet: 12 worlds (6 cultures x 2 reps x 200 turns) ~ $220, out-tag 2026-08-08-new-aesthetics, watchdog armed. Results to artifact only per Aengus.

## 2026-09-01 18:57 UTC — Claim audit + public-site redesign
Re-derived the threat-dial headlines from raw world state, events, and decisions. Absorption remains exact (9/9 pressure worlds monoculture; 3/3 controls retain four religions); median final-extinction turns corrected to 49/29/21; proposal endpoint corrected from 20 to 23.0, with K=8/K=4 not separating. Judged win rates remain control 40.9%, K16 54.0%, K8 55.1%, K4 50.8%; K4 uncertainty overlaps control, so the page no longer claims uniform improvement under all pressure.

New-aesthetics depth/breadth analysis is descriptive: charter identity accounts for 85.3% of the two-feature variance across 12 worlds, between/within SS ratio 5.82, replicate vs between-charter distance 0.96 vs 1.91. Cave and psychedelic define the clearest extremes; the middle four overlap. The vocabulary-adherence table is excluded from claims because this fleet has no charter-free control and its uncalibrated word lists show strong column effects.

Redesigned the public page as an editorial research monograph with a sticky contents rail, five audited findings, figure captions, status-tagged nested claim tree, explicit caveats, and unresolved/TODO ledger. Added 12 new-aesthetics art examples and the depth/breadth plot to the evidence bundle. Desktop/mobile Chromium render checks passed; focused suite 293/293 passed.

## 2026-09-01 19:15 UTC — Short-form blog essay added
Expanded the public page from an evidence report into a seven-part concise essay: question and control, cultural inheritance, judged preference, selection pressure, production failure, new-aesthetic regimes, and the bounded implication for churches. Artifacts now lead the narrative in always-visible plates; expandable findings and the claim tree remain as the audit layer. No claim values changed. Desktop and mobile Chromium render checks passed.

## 2026-09-01 20:00 UTC — Reader-state rewrite + paged art plates
Rebuilt the public narrative around the motivating human problem: where art comes from when no individual artist contains the whole explanation. The page now gives a one-minute three-claim answer, then stages the argument as problem → inheritance/selection/institutions → controlled sandbox → three findings → bounded answer and human-study next step. The essay is 930 words; audited evidence cards and the claim tree remain below it. Dense essay galleries now show six works at a time with accessible previous/next controls, while every narrative caption begins with a bold claim. No numerical claim changed. JSON/build checks, desktop/mobile Chromium renders, and the full focused suite (293 tests) passed.

## 2026-09-01 21:00 UTC — Distributed-authorship reframing + matched trace reader
Re-ranked the public claims by intellectual importance. The main argument is now: culture causally changes style; coherent traditions can accumulate without a central designer; the explicit-versus-tacit share is not identified; new-aesthetic extremes suggest conformity/expressivity regimes. Removed the render-truncation implementation failure and model-judge taste ranking from the narrative claim set. Added Joseph Henrich's *The WEIRDest People in the World* as intellectual context without claiming it explains art.

Built an inspectable matched-lineage reader for The Open Circuit inside ascetic-r1, baroque-r1 and charter-free control-r2. Each world exposes six accepted images, turns, makers, doctrines and public revision reasons. The UI explicitly distinguishes stated intent, visible inheritance and the unplanned culture-level trajectory; it does not present private chain-of-thought or infer unconscious influence from missing words. Added a proposed causal program crossing conformity, hierarchy, population mixing and transmission channel while holding aesthetic content fixed.
