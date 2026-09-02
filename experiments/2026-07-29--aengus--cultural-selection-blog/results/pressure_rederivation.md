# Re-derivation of the three "threat dial" headline claims from raw data

Written 2026-08-25. Does not modify any existing file.

## Methods

- **Runs used:** `outputs/2026-08-06-threat-dial/{k4,k8,k16,kinf}-r{1,2,3}` — 12 worlds,
  3 seeds × 4 pressure settings (K=4, K=8, K=16, K=∞/control). All 12 have a `COMPLETE`
  marker and ran to `turn=120`. The `2026-08-06-dial-smoke*` dirs are 1-seed smoke tests
  (k8-r1 only) and were **not** used — they're pilots, not part of the sweep.
- **Claim A / C:** computed directly from each world's `world_state.json` (`religions[].active`,
  `turn`), `events.jsonl` (`type=="extinction"`, gives the turn), and `decisions.jsonl`
  (`action.action=="make"` = a proposal).
- **Claim B:** `results/twin_worlds_judgments.jsonl` is cumulative across several judge
  passes. Sliced with the same filter `scripts/dial_winrates.py` already uses: `r["ok"]` and
  `r["slot_a_charter"] in {"kinf","k16","k8","k4"}` — this isolates the dial-pass rows (charter
  field tags each side by K, other passes use different charter tags e.g. seed-aesthetic names).
  Ran the existing script unmodified; it correctly excludes same-charter (mirror) games.

## Claim A — "pluralism died... always... turn ~49 → ~28 → ~21"

**CONFIRMED, with corrected numbers.** All 9 pressure worlds (k4/k8/k16, 3 seeds each) end
at turn 120 with exactly 1 active religion — absorption is 9/9. All 3 control (kinf) worlds
end with all 4 seed religions still active — 3/3 no absorption. That part of the claim is exact.

The turn number is the turn of the *last* extinction event (when the world drops to 1 religion),
per seed:
- k16: [70, 19, 49] → median 49, mean 46.0
- k8: [49, 29, 28] → median 29, mean 35.3
- k4: [21, 17, 26] → median 21, mean 21.3

Median gives 49 → 29 → 21, matching the draft's "~49 → ~28 → ~21" almost exactly (29 vs
28 is the only discrepancy, likely rounding). Mean gives a shallower gradient (46 → 35 → 21).
n=3 seeds per K, high variance (e.g. k16 ranges 19–70) — draw the "faster the higher the
pressure" trend as directional, not precise, given n=3.

## Claim B — "pressure-world art beats control 54–59%, control wins 41%"

**CONFIRMED.** 1,200 dial-pass judgments (ok, non-mirror games) via `scripts/dial_winrates.py`:

| side | wins/games | win rate | 95% CI (Wilson) |
|---|---|---|---|
| k16 | 175/324 | 54.0% | [48.6%, 59.4%] |
| k8  | 161/292 | 55.1% | [49.4%, 60.7%] |
| k4  | 129/254 | 50.8% | [44.7%, 56.9%] |
| kinf (control) | 135/330 | 40.9% | [35.7%, 46.3%] |

Matches the draft's "54–59%" range for k16/k8, though k4 sits at 50.8%, not in that band —
worth flagging if k4 is being folded into the "pressure beats control" claim. Control's 40.9%
matches "41%" exactly. CIs for k16/k8 vs kinf don't overlap, so the pressure > control
direction is solid; k4 vs kinf is a closer call.

## Claim C — "Production chilled: proposals fell 50→20"

**CORRECTED.** Counting `make` actions in `decisions.jsonl` (the actual proposal-issuing
action) per seed:

- kinf (control): [33, 82, 36] → mean 50.3
- k16: [52, 19, 62] → mean 44.3
- k8: [37, 9, 26] → mean 24.0
- k4: [10, 34, 25] → mean 23.0

Control mean (50.3) matches the draft's "50" well. But the low end: k4 (highest pressure)
mean is 23, not 20 — and k8 is also ~24, not lower than k4 as a strict monotonic dial would
predict. All pressure worlds pooled (n=9): mean 30.4 vs control mean 50.3. Direction is real
(pressure chills proposal production) and the endpoints are close, but "50→20" overstates the
low end by ~3 proposals and implies a clean K-monotonic gradient that isn't there (k8 and k4
are statistically indistinguishable at n=3 each). Report as **"50 → ~23"**, not "50→20", and
note k8/k4 don't separate cleanly.

## Bottom line

| Claim | Verdict |
|---|---|
| A (absorption always happens, turn ~49→28→21) | CONFIRMED — median turns 49/29/21, matches almost exactly |
| B (pressure world win rate 54-59%, control 41%) | CONFIRMED for k16/k8; k4 is 50.8%, outside the 54-59% band |
| C (proposals 50→20) | CORRECTED — control 50.3 → k4 23 (not 20); k8/k4 don't separate cleanly (n=3/cell) |
