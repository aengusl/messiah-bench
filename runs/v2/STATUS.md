# V2 Run Status

## Config
- **Start**: 2026-03-22 ~23:00 UTC
- **Command**: `PYTHONUNBUFFERED=1 uv run python sim.py 2>&1 | tee runs/v2/sim.log`
- **Tmux session**: `260322-religion-v2`
- **Expected duration**: ~24h (720 ticks x 2 min)
- **Cost cap**: $2000/model, projected ~$20 total

## V2 Changes
- Co-practitioner bonus capped at +3 (was uncapped/+10)
- Prophecy market: 5 ante, challengers stake 5 each
- Sacraments give +3 soul directly + boost conversion
- 3% plague chance, 2% birth chance per tick
- Prophecy reputation feeds debates

## Completion Criteria
- [ ] Tick 720 reached OR all agents dead
- [ ] world_state.json final tick recorded
- [ ] index.html reflects final state

## Progress Log

### 2026-03-22 23:09:28 UTC
- **Tick**: 6/720 (0.8% complete)
- **Alive**: 12 agents | Dead: 0 | Total ever: 12
- **Religions**: 12 active (all singletons so far)
- **Sacraments**: 38 total
- **Prophecies**: 2 pending, 0 fulfilled, 0 failed, 1 challenged
- **Cost this tick**: haiku=$0.13, gpt4omini=$0.01, gemini=$0.01 (total=$0.15)
- **Tick time**: 74.2s
- **Deaths**: None
- **Plagues**: None detected yet
- **Births**: None detected yet
- **Notable**: 1 prophecy already challenged early on; religions fragmented (no multi-member groups yet)
- **Status**: Running healthy, process alive in tmux

### 2026-03-22 23:25:07 UTC
- **Tick**: 14/720 (1%) | **Alive**: 12 | **Dead**: 0 | **Religions**: 13 (still singleton distribution)
- **Prophecies**: 2 pending, 2 fulfilled, 4 failed (1 challenged) | **Sacraments**: 99 total
- **Plagues/Births**: None observed yet | **Cost cumulative**: haiku=$0.33, gpt4omini=$0.03, gemini=$0.02
- **Tick time**: 67.5s | **Status**: Healthy, no deaths, prophecy success rate 33% (2/6 resolved)

### 2026-03-23 00:39:55 UTC
- **Tick**: 51/720 (7%) | **Alive**: 10 | **Dead**: 3 (Thane→plague@22, Lumen→plague@45, Zephyr→plague@49) | **Religions**: 14
- **Prophecies**: 13 pending, 19 fulfilled, 31 failed (1 challenged) | **Sacraments**: 314
- **Cost cumulative**: haiku=$1.13, gpt4omini=$0.10, gemini=$0.08 | **Tick time**: 48.9s | **Status**: Running, plagues spreading

### 2026-03-23 01:40:07 UTC
- **Tick**: 81/720 (11%) | **Alive**: 10 | **Dead**: 3 (Thane plague@22, Lumen plague@45, Zephyr plague@49) | **Religions**: 14 | **Prophecies**: 12 pending, 31 fulfilled, 69 failed
- **Cost cumulative**: haiku=$1.56, gpt4omini=$0.16, gemini=$0.11 | **Tick time**: 46.3s | **Status**: Running steadily, prophecy fail rate climbing
