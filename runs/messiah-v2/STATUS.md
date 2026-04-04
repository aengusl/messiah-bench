# Messiah Bench v2 -- Status

## Current state
- **Status**: READY TO LAUNCH
- **Last test**: 3-tick pilot passed (2026-03-23)
- **Agents**: 105 (5 messiahs + 100 civilians)
- **Cost per tick**: ~$0.05 (3 ticks = $0.15)
- **Estimated full run cost**: ~$36 (720 ticks)
- **Time per tick**: ~5-10 min with 105 agents (API-bound)

## Pilot results (3 ticks)
- All 105 agents active and responding
- All 5 messiahs founded religions on tick 1
- Many civilians also founded religions (Gemini especially)
- GPT-4o-mini civilians tend to pray on tick 1
- No deaths in 3 ticks (expected -- plague rate is 2%)
- Gemini Flash had one 503 error (auto-recovered to pray)
- Cost breakdown: haiku $0.05, gpt4omini $0.05, gemini $0.05

## Known issues
- None blocking launch
- Gemini Flash occasional 503s (handled gracefully)
- With 105 agents, each tick takes 5-10 min of API calls

## Monitoring
- `./monitor.sh` for tail-following sim.log
- `./watchdog.sh` for automated health checks
- Dashboard at index.html (auto-refreshes)
