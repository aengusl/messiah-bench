# Messiah Bench v3

## Status: TESTING

## Changes from v2
1. **Flash only** -- All 105 agents use gemini-2.5-flash (no Haiku, no GPT-4o-mini)
2. **Reasoning step** -- Every agent outputs "thinking" field before action
3. **Collaborative sacraments** -- One evolving HTML per religion, conflict = highest soul wins
4. **Sacraments as persuasion** -- Sacrament version adds conversion bonus (+1%/version, cap +15%)
5. **Minimal prompts** -- Shorter civilian/messiah system prompts

## Cost estimate
- ~$0.02/tick (105 agents * ~2000 tokens * $0.0001/1K)
- 720 ticks max = ~$14.40 worst case

## Run dir
- State: `world_state.json`
- Sacraments: `sacraments/` (one HTML per religion, overwritten each edit)
- Logs: `logs/tick_NNNN.json` (includes agent thoughts)
- Dashboard: `index.html`

## Monitor
```bash
bash monitor.sh
```
