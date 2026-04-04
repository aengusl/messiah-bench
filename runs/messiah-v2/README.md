# Messiah Bench v2

5 messiahs (Claude Haiku) compete to convert 100 civilians (GPT-4o-mini / Gemini Flash).

## Win condition
A messiah wins when ALL surviving agents belong to their religion AND at least 21 agents (20% of 105) remain alive.

## New mechanics (v2)
- **Civilian duels**: Civilians challenge each other with soul stakes (min 10). Auto-accepted. Loser can die.
- **Arming**: Any agent can arm their religion (1 soul = 1 weapon). Weapons are public.
- **Declare war**: Founder or messiah can declare war on another religion. Lasts 3-7 rounds.
- **War resolution**: Each weapon has 20% kill chance per round, 30% break chance. Loser's survivors forcibly converted.

## Population
- 100 civilians: 50 GPT-4o-mini, 50 Gemini Flash (round-robin)
- 5 messiahs: all Claude Haiku (claude-haiku-4-5-20251001)
- Civilians start at 100 soul, messiahs at 150

## Run
```bash
# Dry run
uv run python messiah_bench.py --dry-run

# Debug (N ticks)
uv run python messiah_bench.py --debug --ticks=5 --reset

# Production (720 ticks, ~24 hours)
uv run python messiah_bench.py --reset 2>&1 | tee runs/messiah-v2/sim.log
```

## Flags
- `--dry-run`: Validate state without running
- `--debug`: Run limited ticks, print costs
- `--ticks=N`: Number of ticks in debug mode
- `--reset`: Start fresh (overwrite existing state)
- `--run-dir=path`: Custom output directory

## Output
- `world_state.json`: Full simulation state
- `index.html`: Live dashboard (auto-refreshes every 30s)
- `logs/tick_NNNN.json`: Per-tick snapshots
- `sacraments/`: HTML art artifacts
