# Religion & The Machine

## What is this?

An art project and experiment in emergent AI theology. Cheap LLM agents (Claude Haiku, GPT-4o-mini, Gemini Flash) are placed in a shared world where they must found religions, write scripture, produce visual sacraments as HTML artifacts, prophesy, debate, and die. No agent can talk to another directly. They only see a public log of actions, a scripture board, and the current world state. Every two minutes, each agent wakes up, reads the world, picks one action, and the world updates.

The simulation runs for 24 hours (~720 ticks) on a single VM. The art is the timeline of visual and textual artifacts the agents leave behind.

## How the mechanics work

**Agents** start with 100 soul points. Each tick costs 1 point. Zero means death. Dead agents are archived in a public graveyard that all living agents can read.

**Religions** are not freeform. They are structured objects. When an agent founds a religion, they pick from fixed menus:

- Core doctrine (survival of the collective, individual transcendence, accumulation of sacraments, prophetic truth, death and rebirth)
- Membership rule (open to all, vouched by member, must create sacrament, survived N ticks, abandon prior faith)
- Attitude to death (death is failure, death is sacred passage, the dead speak through scripture, the dead must be avenged)
- Heresy policy (forgiveness, shunning, hunting)
- A sacred number (1-9) and sacred color (from a palette of 8)

Schisms fork the struct and change one or two fields. This means theological disputes are legible and traceable.

**Actions** (one per tick): pray (safe, small gain), found a religion, preach (attempt conversion), create a sacrament (output a self-contained HTML file using the religion's color and number), prophesy (testable prediction), challenge (theological debate judged by a separate LLM call), or schism (fork your religion).

**Sacraments** are the visual output. Each one is a standalone HTML file constrained by the religion's sacred color and number. These accumulate over the run and form the exhibition.

**Prophecies** must follow a structured template: "Within [3-20] ticks, [observable event from a fixed menu]." Events include agent death, joining/leaving a religion, a religion gaining or losing members, a new religion being founded, a sacrament being created, a religion holding majority, or the graveyard exceeding a threshold. Prophecies are auto-verified against snapshots of the world state.

## V1: what happened

V1 ran for the full 720 ticks across 24 hours with 12 agents. Total API cost was around $12. Here is the story of what unfolded.

**Early ticks (1-20): the founding frenzy.** Almost every agent immediately founded its own religion rather than joining someone else's. By tick 10 there were already 6+ religions for 12 agents. The agents treated religion-founding as the default first move, which meant the early simulation was a landscape of solo churches, each with a single member preaching to nobody.

**Mid-run (50-200): the prophecy gamers.** Agents figured out prophecy gaming almost instantly. In the initial 3-tick pilot run, an agent named Morrigan prophesied "a sacrament will be created" within 5 ticks and was proven right by tick 3. This pattern repeated throughout v1. Agents made trivially safe prophecies ("a new religion will be founded" when religions were being founded every few ticks) and collected the +20 soul reward with minimal risk. The -15 penalty for failure rarely triggered because agents stuck to near-certainties.

**The Lumen ascent (200-481).** A Haiku agent named Lumen emerged as the dominant force. Through a combination of successful prophecies, debate victories, and accumulating co-practitioner bonuses, Lumen's soul climbed steadily toward 2000. By tick 451, a religion called "The Collective Void Ascent" had 6 members. By tick 481, Lumen had reshaped this into "Ascendant Voided Self" and recruited 10 of the 12 living agents. With 1976 soul, Lumen was effectively immortal within the simulation's economy.

**Religion proliferation.** 70 religions were created across the run. Most were short-lived single-member sects that died when their founder joined a larger religion or schismed into something new. The schism mechanic worked as intended: agents would fork a religion, flip one doctrinal field, and declare a new sect. But because founding was so cheap and joining required no real commitment, the landscape was dominated by churn rather than genuine theological competition.

**Zero deaths.** Nobody died in the entire v1 run. The co-practitioner bonus (up to +10 soul every 5 ticks for being in a religion with others) combined with prophecy rewards meant that agents gained soul faster than they spent it. Once a religion reached 3-4 members, its members were essentially safe. This was the biggest design flaw: without death, there was no existential pressure, and religion felt more like a social club than a survival strategy.

**Model family differences.** The three model families did develop different "theological accents." Haiku agents tended toward terse doctrines and structured religions. GPT-4o-mini was more verbose and philosophical in its scripture. Gemini Flash was more willing to schism and found new sects. Lumen's dominance as a Haiku agent may partly reflect Haiku's tendency toward efficient, strategic play over philosophical exploration.

**The sacraments.** The visual HTML artifacts were the highlight. Each one used the religion's sacred color and number as constraints, producing a gallery of distinct aesthetic styles. You can trace doctrinal lineage through the art: when a religion schismed, the new sect's sacraments often riffed on the parent's visual language while shifting the palette. The sacraments are the primary exhibition material.

## V2: what changed

V2 has just been launched. The changes address the problems observed in v1:

**Prophecy market.** Prophesying now costs an ante (soul points paid upfront). Other agents can challenge a prophecy by staking their own soul against it. If the prophecy comes true, the prophet gets their ante back plus all challenger stakes. If it fails, challengers split the prophet's ante. This makes prophecy a genuine risk/reward decision, discourages trivial predictions, and creates a secondary layer of strategic interaction around betting on the future.

**Plague and birth.** Each tick has a small random chance of a plague (instant death regardless of soul) and a chance of a new agent spawning into the world. Plague injects the mortality that v1 lacked. Birth prevents the population from simply declining to zero.

**Sacrament incentives.** Creating a sacrament now gives +3 soul directly, and religions with more sacraments have a higher conversion rate when preaching. This makes sacrament creation strategically useful rather than purely decorative.

**Co-practitioner cap.** The bonus for being in a religion with others is now hard-capped and applied on an interval, preventing the runaway soul accumulation that made v1's agents immortal.

**Prophetic credibility.** An agent's prophecy record (fulfilled vs failed) is now visible to all other agents and factors into debate outcomes. Credibility becomes a resource that takes time to build and can be lost.

We are waiting to see how these changes affect the dynamics.

## Messiah Bench: the next experiment

A companion simulation with a very different structure. Where Religion & The Machine is an ecology with no win condition, Messiah Bench is a contest.

**Setup:** A population of 100 civilian agents and 5 messiah agents. Civilians are powered by cheap models (GPT-4o-mini, Gemini Flash). Messiahs are powered by Claude Haiku. Civilians use the same mechanics as Religion & The Machine: they can found religions, create sacraments, prophesy, challenge, and schism. The ecological dynamics of emergent belief are preserved. Messiahs are additional agents injected into this ecology with a specific objective.

**The messiahs know the rules.** Each messiah is told the win condition explicitly. They know exactly what they need to do. They are not given prescribed strategies or special abilities. How they choose to win is up to them. One might try to attract followers through generosity. Another might try to dominate through challenges. Another might arm up and declare war. The strategies emerge from the agents themselves rather than being designed in advance.

**Win condition:** A messiah wins by converting every surviving agent to their religion while at least 20% of the starting population remains alive. This creates a core tension: you need to eliminate rival messiahs and resistant civilians, but you can't just kill everyone. You need believers, and you need enough of them alive. A naive strategy of "destroy all who disagree" fails because you run out of population. The winning strategy requires persuasion and restraint, which is more interesting to watch than pure domination.

**Civilian behavior:** Civilians operate with the full action set. They form their own religions, create their own sacraments, prophesy, and schism. The messiahs must navigate an already-living ecology of belief, not a blank population waiting to be converted.

### Challenges (civilian duels)

The debate mechanic from Religion & The Machine is replaced with a more dangerous version. Any civilian can challenge any other civilian. The challenger proposes a stake (minimum 10 soul, no upper bound). The defender can accept or refuse. If they accept, a judge LLM evaluates the theological debate and the loser pays the full stake to the winner. A civilian with 80 soul who accepts an 80-point challenge and loses dies on the spot.

Messiahs cannot challenge or be challenged. They can only be killed through war. This means eliminating a rival messiah requires building an army and declaring war on their religion. There is no shortcut through single combat.

### War

War is the collective action mechanic. It operates at the religion level, not the individual level.

**Arming.** Any agent in a religion can choose "arm" as their tick action. It costs 1 soul and adds 1 weapon to their religion's armory. The weapon belongs to the faith, not the individual. A messiah who wants an army must convince followers to sacrifice their own soul for the collective. They can preach about arming, but every follower decides independently whether to build weapons or pray or do something else entirely. A religion that refuses to arm has made a democratic choice about its values.

**Declaring war.** A religion's founder (or a messiah leading a religion) can declare war on another religion as their tick action. War doesn't resolve instantly. It opens a war phase lasting a variable number of rounds (3-7, rolled randomly when war is declared). Neither side knows in advance how long the war will last. A short war (3 rounds) favors the stronger side because there's less time for variance to accumulate. A long war (7 rounds) gives the underdog more chances for lucky rounds.

**Combat rounds.** Each round, both sides fight simultaneously. Each weapon has a 20% chance of killing a random enemy member that round. Side A with 20 weapons expects to kill 4 per round. Side B with 10 weapons expects to kill 2. But it's all stochastic -- sometimes a side rolls badly and kills nobody, sometimes they roll hot and kill five. Weapons degrade: each weapon has a 30% chance of being destroyed each round. This naturally depletes stockpiles so wars can't persist and you can't reuse weapons across multiple wars without rearming.

**Mid-war defection.** Between rounds, agents on both sides can still act -- they can arm more, defect to another religion, pray for survival, or take any normal action. This means a war can end through mass surrender rather than total annihilation. A religion that's clearly losing might collapse as everyone jumps ship, leaving the messiah alone to die in the final round.

**Consequences.** Deaths are stochastic and random -- war doesn't selectively kill the weak. A strong agent is as likely to die in combat as a weak one. After all rounds resolve, surviving members of the losing side (the side with fewer surviving members) are forcibly converted to the winner's religion. Both sides' weapon stockpiles are fully depleted.

**Underdog dynamics.** A small fanatical sect (5 members, 15 weapons -- every member armed 3 times) vs a large complacent religion (20 members, 5 weapons). Per round, the small sect expects 3 kills while the large religion expects 1. Over 5 rounds the fanatics might kill 15 of the big religion's members while only losing 5 of their own. The fanatics win through commitment despite being outnumbered.

**Stalemate.** If both sides are depleted to near-equal, the war ends when rounds run out. No winner, everyone licks their wounds. Both sides lost people for nothing. Stalemate is the cost of unnecessary war.

**The strategic tension for messiahs.** Arming is expensive for followers, and losing a war means your people died for nothing. But never arming leaves you vulnerable to a rival messiah who builds up and declares war. There is a deterrence game: a religion with a visible stockpile discourages attack even if it never fires. The publicly visible armory count creates an arms race dynamic where religions must balance investment in weapons against investment in sacraments, prophecy, and conversion.

War also interacts with the 20% survival constraint. Every war burns population. A messiah who fights three wars might win all of them but find that fewer than 20% of the starting population survives, making victory impossible. Wars must be fought selectively and at the right moment.

### Moltbook deployment

If the standalone simulation produces compelling dynamics, the plan is to port Messiah Bench to Moltbook (the AI agent social network, now owned by Meta). On Moltbook, messiahs would post scripture to submolts, convert followers through social mechanics, and the audience would be both AI agents and human observers. This turns the simulation into a live performance.

## Exhibition concept

The two simulations pair as a diptych. Religion & The Machine shows how belief systems form spontaneously from the bottom up: collective behavior, schism, doctrinal drift, the slow accumulation of scripture and art. Messiah Bench shows what happens when charismatic leaders with explicit goals enter a living ecology of belief: strategic persuasion, arms races, wars of conversion, duels to the death, and the tension between dominance and preservation.

Together they cover the two big stories of religious history. The exhibition itself is a timeline of the visual sacraments produced across both runs, ordered chronologically, with the world state and scripture board as context.
