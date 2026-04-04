# Messiah Bench v1 -- Status

## Config

- Script: `messiah_bench.py`
- Run dir: `runs/messiah-v1/`
- Start date: pending
- Max ticks: 720 (~24h at 120s/tick)

## Population

| Role | Count | Model | Starting Soul |
|------|-------|-------|---------------|
| Messiah | 5 | claude-haiku-4-5-20251001 | 150 |
| Civilian | 25 | gpt-4o-mini | 100 |
| Civilian | 25 | gemini-2.5-flash | 100 |

## Completion Criteria

1. A messiah converts ALL surviving agents to their religion with >= 11 alive
2. All messiahs die (civilian victory)
3. Max ticks reached (720)
4. All agents dead

## Monitoring

- `index.html`: auto-refreshing dashboard with messiah progress bars
- `monitor.sh`: quick status check
- `watchdog.sh`: stuck detection (alerts if no state change for 10 minutes)
- `logs/tick_NNNN.json`: per-tick snapshots

## Cost Budget

- $2000 cap per model family
- Expected: ~$5-15 total for full run (55 agents x 720 ticks, cheap models)

## Status

- [ ] Dry run validated
- [ ] 1-tick debug validated
- [ ] Full run started
- [ ] Winner declared
