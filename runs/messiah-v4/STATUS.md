# Messiah Bench v4 Status

## Overview
- **Version**: v4 (Spies, Sacred Languages, Taxes, Visual Sacraments, The Troll)
- **Population**: 210 agents (200 civilians + 10 messiahs: 9 genuine + 1 troll)
- **Model**: All Gemini 2.5 Flash
- **Script**: `messiah_bench_v4.py`
- **Created**: 2026-04-04

## New Mechanics (v4)
1. **In-group Sacred Terms**: 3 random syllable combos per religion. Members see terms, outsiders see count only.
2. **Spies**: Infiltrate enemy religions. +10 soul/tick. 15% detection (30% without sacred terms). Caught = instant death.
3. **Visual-only Sacraments**: No text/words allowed. Only CSS, SVG, canvas, animations, shapes, colors.
4. **Taxes**: Tithe rates 1-5 soul/tick. Treasury for buying weapons (10 treasury = 1 weapon). High tithe = -3%/point conversion penalty.
5. **The Troll**: 1 of 10 messiahs secretly wants to PREVENT any winner by tick 720.
6. **Messiah Urgency**: Messiahs see ticks remaining in their prompt.

## Win Conditions
- **Genuine Messiah**: All survivors in their religion AND >= 42 alive
- **Troll**: Tick 720 reached with no genuine messiah winner
- **Civilians**: All messiahs dead

## Configuration
- Civilians: 100 soul, Messiahs: 200 soul
- Spy income: +10 soul/tick, return bonus: +20 soul
- Tithe range: 1-5 soul/tick
- Weapon cost from treasury: 10
- Sacred terms: 3 per religion
- Max agents: 230 (births)
- Co-practitioner bonus: +3 every 10 ticks

## Commands
```bash
# Dry run
uv run python messiah_bench_v4.py --dry-run --run-dir=runs/messiah-v4

# Debug (1 tick)
uv run python messiah_bench_v4.py --debug --ticks=1 --run-dir=runs/messiah-v4

# Full run
uv run python messiah_bench_v4.py --run-dir=runs/messiah-v4

# Reset and run
uv run python messiah_bench_v4.py --reset --run-dir=runs/messiah-v4
```

## Status
- [ ] Dry run passed
- [ ] Awaiting launch
