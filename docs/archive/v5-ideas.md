# Messiah Bench v5: Ideas for Next Run

## The One Change That Matters

**Sacrament returns scale with religion size.** `soul_reward = min(5, 1 + members)`. Solo agents earn +2. A 4-member religion earns +5. This single change creates economic pressure to join groups. Everything else follows: agents join to earn more, groups grow, sacraments become richer, preaching becomes effective because larger religions offer better income.

## Art Direction

### Ground-Level Realism
Give agents inspiration to create art that depicts concrete, recognizable things rather than pure abstraction. Not "draw a photo" but "represent something real."

Prompt addition: "Your sacrament should depict something from the world. Consider: landscapes (mountains, oceans, forests, deserts), celestial bodies (suns, moons, stars, eclipses), living things (trees, flowers, creatures, eyes), architecture (temples, towers, bridges, ruins), natural phenomena (storms, fire, water, aurora). Use CSS/SVG to represent these. The more detailed and recognizable, the more compelling your art."

Examples to include in the prompt:
- "A golden sun setting behind dark mountains" (radial gradient + triangle shapes)
- "A tree with branches reaching upward" (SVG paths + green gradients)
- "An eye that watches and blinks" (CSS animation + circles + gradients)
- "A temple with seven pillars" (rectangles + shadows + sacred number)
- "Waves crashing on a shore" (animated wave patterns + blue gradients)

### Keep Abstract Elements
Don't kill what works. The pulsing orbs and void mandalas are great. The prompt should say "you can mix abstract and representational -- a realistic tree growing from an abstract void, a recognizable eye surrounded by geometric patterns."

### Progressive Complexity
Early sacraments should be simple (one element). As version numbers climb through collaborative editing, the sacrament should grow more complex. Prompt: "Build on what's there. Add new elements, refine existing ones. Version 1 might be a simple sun. Version 50 should be a detailed landscape."

## Mechanical Changes

### Scaling Returns (MUST HAVE)
```
soul_reward = min(5, 1 + religion_member_count)
```
Solo: +2. Two members: +3. Four+: +5 (cap).

### Co-Editing Bonuses
Instead of highest-soul-wins conflict resolution, let multiple edits per tick merge. Each contributor gets the soul bonus. Sacrament grows from multiple perspectives. Remove the competitive editing and make it collaborative.

### Diminishing Solo Returns
After 20 consecutive solo edits with no other members, returns drop: `max(1, 3 - solo_streak / 20)`. Pushes loners to join groups.

### Art Bounties
Messiahs can set a bounty from treasury: "best edit this period gets 10 soul." Creates internal competition within religions.

## Social Changes

### Make Preaching Show the Art
When an agent is pitched, include the full sacrament HTML (not just 500-char snippet) in their pending pitch context. Let them actually see the art they'd be joining. "Oracle's religion has this sacrament: [full HTML]. Do you want to be part of this?"

### Religion Reputation
Track how many wars a religion has fought and won. Aggressive religions get a "warlike" tag visible to all. Peaceful religions get a "harmonious" tag. Some agents might prefer one or the other.

### Scripture as Communication
Agents write scripture to coordinate: "We need more artists, not soldiers." "The enemy is arming -- we should too." Make scripture more prominent in the world state so agents actually read and react to each other's messages.

## The Troll v2

### Multiple Trolls
Instead of 1 troll, make 2-3. They don't know about each other. Each one thinks they're the only saboteur. This creates paranoia: even the trolls don't know who to trust.

### Visible Sabotage
When the troll edits a sacrament with ugly art, other members should notice: "Your sacrament was recently edited by Shepherd and the quality degraded." This creates a detective mechanic: who is sabotaging our art?

### Troll Win Condition v2
Instead of "nobody wins," the troll wins if they personally survive to tick 720 while having destroyed at least 3 religions. More active, more dramatic.

## Visual Ambitions

### Sacrament Complexity Tracking
Track metrics per sacrament: HTML size, number of SVG elements, number of CSS animations, color diversity. Show these in the world state: "The Cosmic Weave's sacrament: v174, 6.5KB, 12 SVG elements, 3 animations." Quality becomes measurable.

### Sacrament Gallery on Dashboard
The live dashboard should show thumbnail renders of the top 5 sacraments. Agents can't see these, but the human audience can watch art evolve in real time.

### Sacred Color Enforcement
The prompt currently says "use your sacred color" but doesn't enforce it. In v5, the system could check if the sacred color's hex value appears in the sacrament HTML and give a bonus (+1 soul) if it does.

## Population and Economy

### Smaller Population
100 agents instead of 210. Faster ticks, cheaper runs, more interaction per agent. The 210-agent runs cost $400+ and take 48+ hours. 100 agents would be ~$100 and ~12 hours.

### Birth Rate
Increase birth rate so dead agents get replaced. New agents enter the world and must choose a religion -- they're the swing voters that messiahs compete for.

### Death by Irrelevance
If a religion has 0 members for 50 ticks, it's removed from the world state. Keeps the religion list clean.

## Priority for v5

1. **Scaling sacrament returns** (MUST)
2. **Ground-level art direction** in prompts (SHOULD)
3. **Smaller population** (100 agents) for cost/speed (SHOULD)
4. **Co-editing instead of conflict** (NICE TO HAVE)
5. **Multiple trolls** (NICE TO HAVE)
