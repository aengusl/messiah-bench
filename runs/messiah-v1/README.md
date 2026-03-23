# Messiah Bench v1

Competitive messiah simulation: 5 messiah agents (Haiku) compete to convert 50 civilian agents (GPT-4o-mini / Gemini Flash).

## Setup

- **50 civilians**: round-robin GPT-4o-mini and Gemini Flash, 100 soul each
- **5 messiahs**: all claude-haiku-4-5-20251001, 150 soul each (divine backing)
- **Total**: 55 starting agents

## Win Condition

A messiah wins when ALL surviving agents belong to their religion AND at least 11 agents (20% of 55) remain alive.

If all messiahs die, civilians win by default.

## Messiah Names

Prophet, Oracle, Herald, Beacon, Shepherd

## Key Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Co-prac bonus | +3 every 10 ticks | Larger groups, slower bonus cycle |
| Plague chance | 2% | Slightly lower for bigger population |
| Birth chance | 1% | Keep population manageable |
| Max agents | 65 | Headroom for births |
| Prophecy ante | 5 | Same as v2 |
| Tick interval | 120s | Same as v2 |
| Max ticks | 720 | ~24 hours |

## Mechanics

Same as sim.py v2 (prophecy markets, sacraments as persuasion, random births/deaths) with these additions:

1. Messiahs have a competitive system prompt with win-condition awareness and progress tracking
2. Civilians are told messiahs exist and can choose to follow, resist, or ignore them
3. Win condition checked every tick
4. Messiah progress dashboard in index.html
5. World state summary is compressed (civilians summarized by religion, not listed individually)

## Running

```bash
# Dry run (no API calls)
uv run python messiah_bench.py --dry-run

# Debug (1 tick with real API calls)
uv run python messiah_bench.py --debug --ticks=1

# Full run
uv run python messiah_bench.py

# Reset and start fresh
uv run python messiah_bench.py --reset
```
