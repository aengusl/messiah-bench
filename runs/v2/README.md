# V2: Religion & The Machine

## Changes from V1
1. **Prophecy market**: Prophet pays 5 soul ante. Other agents can challenge (5 soul stake each). If fulfilled, prophet gets ante + all challenger stakes. If failed, challengers split the ante. No challengers = just get 5 back. Makes bold prophecies rewarding, safe ones pointless.
2. **Fixed death math**: Co-practitioner bonus capped at +3 total per interval (was +2 per co-religionist, uncapped). Agents can now actually die from soul depletion.
3. **Prophecy reputation in debates**: Judge sees each debater's prophecy record. Fulfilled prophecies = doctrinal credibility. Builds a prophet-king dynamic.
4. **Sacraments as persuasion**: Recent sacrament titles shown in world state per religion. More sacraments = higher conversion chance (+1% per sacrament, capped at +15%). Direct +3 soul for creating a sacrament.
5. **Random births/deaths**: 3% plague chance per tick (kills random agent regardless of soul). 2% birth chance (spawns new agent with 100 soul, no religion). Population cap at 16.
6. **--run-dir flag**: Output goes to configurable directory. Default: runs/v2/

## Expected Dynamics
- Deaths should start happening around tick 50-80 as solo agents bleed out
- Plagues add unpredictability (~22 expected plague events over 720 ticks)
- ~14 new births expected, keeping population fresh
- Prophecy market should reduce spam and reward bold, specific predictions
- Sacrament bonus should make all model families create art, not just Haiku
