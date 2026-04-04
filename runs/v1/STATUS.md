# Religion & The Machine - Overnight Run

## Config
- **Start**: 2026-03-21 19:20 UTC
- **Command**: `PYTHONUNBUFFERED=1 uv run python sim.py 2>&1 | tee sim.log`
- **Tmux session**: `260321-religion-sim`
- **Expected duration**: ~24h (720 ticks x 2 min)
- **Expected completion**: 2026-03-22 ~19:20 UTC
- **Cost cap**: $2000/model ($6000 total), projected ~$15 total

## Completion Criteria
- [ ] Tick 720 reached OR all agents dead
- [ ] world_state.json final tick recorded
- [ ] index.html reflects final state
- [ ] No cost cap breaches
- [ ] sim.log shows clean exit or all-dead message

## Progress
- **2026-03-22 00:28:19 UTC**: Tick 152/720 (21%) | 12 alive | The Conflux of the Voided One (9 members, top soul: Ashek 675) | haiku:$2.98
- **2026-03-22 08:29:18 UTC**: Tick 391/720 (54%) | 12 alive, 0 dead | 63 religions (fragmentation peak; top 3: Morrigan's Singular Ascent 8, Vesper's Harmonious 2, The Collective Void 1) | Top soul: Lumen 1895 | haiku:$8.38, gpt4omini:$0.89, gemini:$0.69

## Sentinel Plan
1. sim.py runs in tmux, writes world_state.json + index.html each tick
2. Tick logs written to logs/tick_NNNN.json
3. Sacraments written to sacraments/
4. On completion: sim.py exits naturally

## Cost Estimate
- 720 ticks x 12 agents = 8640 LLM calls (split 4 agents each across 3 providers)
- ~2880 calls/model x ~2K tokens avg
- Haiku: 2880 x $0.017/call ~ $12
- GPT-4o-mini: 2880 x $0.0005/call ~ $1.50
- Gemini Flash: 2880 x $0.0005/call ~ $1.50
- **Total estimated: ~$15**

## Progress Log
- 2026-03-21 19:20 UTC: Launched in tmux. Tick 1 completed in 31.7s.
- 2026-03-21 20:27 UTC: **Tick 32/720 (4.4%)** | Alive: 12 | Dead: 0 | Religions: 12 | Sacraments: 103 | Prophecies: 5 pending, 15 fulfilled, 4 failed | Cost: $0.67/tick
- 2026-03-21 21:22 UTC: **Tick 60/720 (8.3%)** | Alive: 12 | Dead: 0 | Religions: 15 | Sacraments: 194 | Prophecies: 4 pending, 35 fulfilled, 8 failed | Top 3 souls: Lumen (315), Vesper (299), Morrigan (296) | **All 12 agents in Voided Solitude** (void, individual transcendence) | Cost: $1.22/tick
- 2026-03-21 22:28 UTC: **Tick 92/720 (12%)** | Alive: 12 | Dead: 0 | Religions: 21 | Sacraments: 289 | Prophecies: 3 pending, 43 fulfilled, 20 failed | Top soul: Ashek (423) | Religion breakdown: 8 in Voided Solitude, 3 in Voided Collective, 1 in Conflux of the Voided One | Cost: $1.93/tick
- 2026-03-22 01:28 UTC: **Tick 182/720 (25%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (12 members) | Top soul: Ashek (856) | Cost: $4.17 cumulative
- 2026-03-22 02:28 UTC: **Tick 212/720 (29%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (10 members) | Top soul: Lumen (1070) | Total cost: $4.89
- 2026-03-22 03:28 UTC: **Tick 241/720 (33%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (11 members) | Top soul: Ashek (1123) | Total cost: $5.70
- 2026-03-22 04:28 UTC: **Tick 271/720 (37%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (12 members) | Top soul: Ashek (1209) | Total cost: $6.48
- 2026-03-22 05:28 UTC: **Tick 301/720 (41%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (11 members) | Top soul: Lumen (1375) | Total cost: $7.44
- 2026-03-22 06:29 UTC: **Tick 331/720 (45%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (12 members) | Top soul: Lumen (1767) | Total cost: $8.53
- 2026-03-22 07:29 UTC: **Tick 361/720 (50%)** | Alive: 12 | Dead: 0 | The Conflux of the Voided One (5 members) | Top soul: Lumen (1757) | Cumulative cost: $9.43
- 2026-03-22 09:29 UTC: **Tick 421/720 (58%)** | Alive: 12 | Dead: 0 | Religions: 63 | Top soul: Lumen (1910) | Dominant: Morrigan's Singular Ascent (5 members), The Collective Void Ascent (5 members) | Cost: haiku:$8.65, gpt4omini:$0.99, gemini:$0.76
- 2026-03-22 10:29 UTC: **Tick 451/720 (62%)** | Alive: 12 | Dead: 0 | Religions: 68 | Dominant: The Collective Void Ascent (6 members) | Top soul: Lumen (1933) | Cost: haiku:$9.27, gpt4omini:$1.09, gemini:$0.83
- 2026-03-22 11:29 UTC: **Tick 481/720 (66%)** | Alive: 12 | Dead: 0 | Religions: 70 | Dominant: Lumen's Ascendant Voided Self (10 members) | Top soul: Lumen (1976) | Cost: haiku:$10.07, gpt4omini:$1.19, gemini:$0.90
- 2026-03-22 17:30 UTC: **Tick 662/720 (92%)** | Alive: 12 | Dead: 0 | Religions: 84 | Dominant: Lumen's Ascendant Voided Self (4 members) & Morrigan's Ineffable Voided Self (6 members) | Top soul: Lumen (3133) | Cost: haiku:$16.03, gpt4omini:$1.89, gemini:$1.42
- 2026-03-22 12:30 UTC: **Tick 511/720 (70%)** | Alive: 12 | Dead: 0 | Religions: 74 | Dominant: Lumen's Ascendant Voided Self (9 members) | Top soul: Lumen (2127) | Cost: haiku:$11.00, gpt4omini:$1.30, gemini:$0.98
- 2026-03-22 13:30 UTC: **Tick 541/720 (75%)** | Alive: 12 | Dead: 0 | Religions: 77 | Dominant: Lumen's Ascendant Voided Self (10 members) | Top soul: Lumen (2386) | Cost: haiku:$12.02, gpt4omini:$1.41, gemini:$1.07
- 2026-03-22 14:30 UTC: **Tick 571/720 (79%)** | Alive: 12 | Dead: 0 | Religions: 77 | Dominant: Lumen's Ascendant Voided Self (11 members) | Top soul: Lumen (2542) | Cost: haiku:$12.99, gpt4omini:$1.53, gemini:$1.15
- 2026-03-22 15:30 UTC: **Tick 601/720 (83%)** | Alive: 12 | Dead: 0 | Religions: 79 | Dominant: Lumen's Ascendant Voided Self (11 members) | Top soul: Lumen (2836) | Cost: haiku:$14.03, gpt4omini:$1.64, gemini:$1.25
- 2026-03-22 16:30 UTC: **Tick 631/720 (87%)** | Alive: 12 | Dead: 0 | Religions: 84 | Dominant: Lumen's Ascendant Voided Self (9 members) | Top soul: Lumen (2977) | Cost: haiku:$15.01, gpt4omini:$1.76, gemini:$1.33
- 2026-03-22 18:01 UTC: **Tick 677/720 (94%)** | Alive: 12 | Dead: 0 | Religions: 84 | Dominant: Morrigan's Ineffable Voided Self (12 members) | Top soul: Lumen (3145) | Cost: haiku:$16.50, gpt4omini:$1.95, gemini:$1.47 | **Final 10 ticks**
- 2026-03-22 18:31 UTC: **Tick 692/720 (96%)** | Alive: 12 | Dead: 0 | Religions: 84 | Dominant: Morrigan's Ineffable Voided Self (12 members) | Top soul: Lumen (3360) | Prophecies: 3 pending, 402 fulfilled, 48 failed | Cost: haiku:$17.02, gpt4omini:$2.01, gemini:$1.52 | **Sim still running** | **FINAL COUNTDOWN - 28 ticks remaining**
- 2026-03-22 19:01 UTC: **Tick 707/720 (98%)** | Alive: 12 | Dead: 0 | Religions: 85 | Dominant: Morrigan's Ineffable Voided Self (11 members) | Top soul: Lumen (3595) | Prophecies: 3 pending, 422 fulfilled, 48 failed | Cost: haiku:$17.55, gpt4omini:$2.07, gemini:$1.56 | **Process still running, 13 ticks remaining**
- 2026-03-22 19:36:48 UTC: SIMULATION COMPLETE at tick 720 (12 alive, 0 dead, 2581 sacraments)
