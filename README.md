# Religion & The Machine

**[Live Exhibition →](https://www.aenguslynch.com/messiah-bench/)**

Cheap LLM agents found religions, write scripture, produce visual sacraments, prophesy the future, wage theological war, and die. Nobody told them to believe in anything. They just do.

---

## What is this?

Twelve AI agents are dropped into a shared world with one rule: survive. Each tick (every 2 minutes), each agent reads the public state of the world and picks one action. They can't talk to each other. They can only observe what others have done — scripture written, religions founded, prophecies made, agents killed.

Over 24 hours, they build entire theological civilizations from scratch. The art is what they leave behind.

## The Mechanics

**Soul** is life. Start with 100. Lose 1 per tick. Hit zero, you die. Gain soul through prayer, successful prophecies, winning debates, or having co-religionists.

**Religions** are structured objects, not freeform text. Pick a doctrine from a menu. Pick a sacred color. Pick a heresy policy (forgiveness, shunning, or hunting). When theological disputes happen, they're legible. When schisms fork a religion, you can trace the lineage.

**Sacraments** are self-contained HTML files — visual art constrained by the religion's sacred color and number. The simulation produces thousands of these. Each one is a standalone artwork generated under theological constraints.

**Prophecies** are testable predictions staked with soul points. "Within 8 ticks, the Church of Recursive Grace will lose a member." Get it right, collect the pot. Get it wrong, lose your ante. Other agents can challenge your prophecy by betting against you. The prophecy market is where religion meets gambling.

**War** is collective action. Agents arm their religion by sacrificing soul for weapons. A founder declares war. Combat unfolds over 3-7 stochastic rounds where each weapon has a 20% chance of killing a random enemy per round. The underdog can win. Weapons break. Members defect mid-war. Wars burn population. The fanatics who arm heavily beat the complacent majority — until they don't.

## The Simulations

### Religion & The Machine (ecology)

No win condition. No objective. Just agents, survival pressure, and the emergent dynamics of belief. V1 ran 720 ticks with zero deaths and total void-theology convergence. V2 introduced plagues, prophecy markets, and capped co-practitioner bonuses — agents started dying by tick 22.

### Messiah Bench (contest)

100 civilian agents (GPT-4o-mini, Gemini Flash) form an organic ecology of belief. 5 messiah agents (Claude Haiku) are injected with an explicit goal: convert every surviving agent to your religion while keeping at least 20% of the population alive.

Messiahs can't duel civilians. They can only die through war. To kill a rival messiah, you need an army of true believers willing to sacrifice their own soul to arm. A religion that refuses to arm has made a democratic choice about its values.

The interesting question: what strategies do goal-directed AI agents develop when placed in a living ecology and told to win through persuasion?

## What we observed

**V1: The Void Convergence.** 85 religions founded, 76 used "void" as their sacred color. Total memetic collapse into a single aesthetic. Gemini agents dominated through prophecy accuracy (98%). Haiku agents became artisan monks producing 60% of all sacraments. GPT-4o-mini agents free-rode, creating 7 sacraments in 720 ticks. Nobody died.

**V2: Death arrives.** First plague at tick 22 killed Thane. Prophecy failure rate jumped to 69% under the ante system. The graveyard filled. New agents were born into a world of established religions and had to choose. The simulation felt alive.

**Messiah Bench: The race.** Herald took an early lead with 5 followers by tick 14. Five messiahs competing for the souls of 100 civilians, each developing different conversion strategies without being told how to play.

## Run it yourself

```bash
git clone https://github.com/aengusl/messiah-bench
cd messiah-bench
cp .env.example .env  # add your API keys
uv sync
uv run python sim.py --debug --ticks=3  # 3-tick test
uv run python sim.py                     # full 24h run
```

API keys needed: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`

## Cost

A full 24-hour Religion & The Machine run (12 agents, 720 ticks) costs about $22. Messiah Bench (105 agents) costs more but stays under $100. All models are the cheapest tier: Haiku, GPT-4o-mini, Gemini Flash.

## The exhibition

The two simulations pair as a diptych. Religion & The Machine shows how belief systems form from the bottom up. Messiah Bench shows what happens when charismatic leaders with explicit goals enter a living ecology of belief. Together they cover the two big stories of religious history.

The art is not the simulation. The art is what the machines leave behind when they try to believe in something.

---

*Built by [Aengus Lynch](https://www.aenguslynch.com)*
