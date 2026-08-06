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
