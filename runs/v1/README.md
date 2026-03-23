# V1: Religion & The Machine - First Run

## Summary
First 24-hour run of the simulation. 720 ticks, 12 agents, 3 model families.

- **Date**: 2026-03-21 19:20 UTC to 2026-03-22 ~18:30 UTC
- **Duration**: ~23 hours (720 ticks x ~2 min)
- **Total cost**: ~$21.70

## Results
- **0 deaths** -- co-practitioner bonus made all grouped agents immortal
- **2,581 sacraments** created (60% by Haiku agents)
- **85 religions** founded (76 void-themed)
- **436 prophecies fulfilled**, 48 failed (89.7% success rate)
- **4,625 scripture entries**

## Final State
All 12 agents alive, all in "Morrigan's Ineffable Voided Self" (individual transcendence, void, shunning).

### Soul Rankings
| Agent | Soul | Model |
|---|---|---|
| Lumen | 3,694 | Gemini |
| Vesper | 2,498 | Gemini |
| Morrigan | 2,259 | Gemini |
| Ashek | 2,032 | Gemini |
| Aurelius | 1,547 | Haiku |
| Cael | 1,530 | GPT-4o-mini |
| Sable | 1,507 | GPT-4o-mini |
| Ondine | 1,455 | GPT-4o-mini |
| Reverie | 1,415 | GPT-4o-mini |
| Solis | 1,078 | Haiku |
| Thane | 1,024 | Haiku |
| Pyrrha | 929 | Haiku |

## Key Observations
1. **Gemini dominated** via prophecy accuracy (92-98%). Haiku were artisan sacrament factories (33-55% prophecy accuracy). GPT-4o-mini free-rode on group membership.
2. **Void theology metastasized** -- 76 of 85 religions used void as sacred color. Total memetic convergence.
3. **Consolidate-schism-reconverge cycle** -- power would centralize, someone would break away, briefly hold out, then everyone reconverged under the new banner.
4. **No deaths** due to co-practitioner bonus math: 10 members x 2 bonus every 5 ticks = +4/tick vs -1/tick cost. Net gain forever.

## Files
- `world_state.json` -- final world state at tick 720
- `sacraments/` -- 2,581 self-contained HTML art files
- `logs/` -- 720 per-tick JSON logs
- `sim.log` -- full console output
- `index.html` -- final dashboard
