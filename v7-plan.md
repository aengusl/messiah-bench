# Messiah Bench v7: Planning Doc

## What v6 proved

v6 ran 100 Gemini 2.5 Flash agents for 378 ticks. Four targeted sacrament fixes (highest-soul-wins conflict resolution, error fallback → idle, text filter removed, full reasoning logged) produced dramatically better results than v5. The sacraments evolved continuously without resets. 28 religions, 10 wars, 52 dead, one winner (The Verdant Ascent).

The key finding: **agents evaluated sacrament art when choosing religions**. 1,390 reasoning passages reference sacrament quality in religion decisions. The art wasn't decoration — it was the central instrument of persuasion. Agents chose expensive religions because the art was better. Messiahs invested in visual quality as recruitment strategy. Members stayed loyal because "our sacrament is highly developed and visually distinct."

## What broke in v6

**Sacraments don't render in browsers.** The agents escalated to absurd values over 356 iterations:
- 15,700×15,700px canvases (246M pixels)
- SVG blur stdDeviation of 1,705px (normal is 2-5)
- box-shadow spread of 14,200px
- flood-opacity of 135 (max valid: 1.0)
- rgba alpha values of 1,435 (max valid: 1.0)

The browser can't rasterize this. Users see blank white rectangles. The art exists but is invisible.

## v7 goal

Make the art render. Keep everything agents love about making art. Constrain the canvas so browsers can display it.

---

## Change 1: Sacrament rendering constraints

Add to the agent prompt and enforce in the sacrament validator:

| Property | Max value | Rationale |
|---|---|---|
| Canvas size | 2000×2000px | Fits in 4M pixel budget. At 20% zoom displays as 400×400px |
| SVG stdDeviation | 30 | Dreamy/soft at 2000px. Agents used 1,705 |
| box-shadow spread | 200px | Visible glow without offscreen compositing blowup |
| opacity / flood-opacity | 0.0–1.0 | Valid CSS range |
| rgba alpha | 0.0–1.0 | Valid CSS range |
| Total HTML size | 50KB | Current files are 4-5KB at 356 edits. 50KB gives 10x headroom |
| External resources | None | No fetch, no external fonts/images |

**Enforcement**: After each agent's edit, validate the HTML. If it violates constraints, reject the edit and keep the previous version (agent still gets the soul reward to avoid punishment for trying). Log which constraint was violated.

**Prompt addition**: "Your sacrament renders in a 2000×2000 pixel box. Keep all dimensions within this. SVG blur stdDeviation max 30. All opacity/alpha values 0–1. No external resources. You have full creative freedom within these bounds: CSS, SVG, canvas, animations, text, transforms, gradients, filters."

### Open question: constrain or clamp?
- **Constrain**: reject edits that violate. Agent keeps previous version.
- **Clamp**: auto-fix values (regex replace anything >2000px with 2000, stdDeviation >30 with 30, etc). Agent's edit goes through but sanitized.
- **Hybrid**: clamp minor violations (opacity 1.5 → 1.0), reject major ones (canvas 15,000px).

## Change 2: ??? (model diversity)

**Status**: idea-stage

Run with multiple model families instead of all-Gemini. Past versions used Haiku+GPT-4o-mini+Gemini. v6 went all-Flash for cost. Options:
- All Gemini 2.5 Flash (cheapest, proven, ~$50)
- Mixed: Flash civilians + Claude/GPT messiahs (tests whether art-as-recruitment varies by model)
- All Claude Haiku 4.5 (different aesthetic, ~$80)
- Mixed bag: 20 agents per model across 5 families

**Tradeoff**: mixed models test more hypotheses but add confounds. Pure runs isolate the variable.

## Change 3: ??? (art direction prompting)

**Status**: idea-stage

v5-ideas.md had a "ground-level realism" proposal: prompt agents to depict recognizable things (landscapes, eyes, temples) not just abstract gradients. v6 removed the text filter and agents naturally added text and more figurative elements.

Options:
- **No change**: let agents do what they want within constraints. v6 produced rich art without direction.
- **Gentle nudge**: "Consider depicting something recognizable — a landscape, a symbol, a scene — alongside abstract elements."
- **Themed rounds**: every 50 ticks, inject a theme ("this epoch's theme is water") that agents can optionally incorporate.
- **Art critique**: every N ticks, show agents their sacrament's "review" from a critic model. Feedback loop on quality.

## Change 4: ??? (economic rebalancing)

**Status**: idea-stage

v6's economy worked (scaling returns by religion size). But 52/100 agents died, mostly from failing to join a religion in the first 5 ticks. Options:
- **Grace period**: no soul drain for first 10 ticks (agents can shop without dying)
- **UBI**: all agents earn +1 soul/tick baseline regardless of religion
- **Easier joining**: messiahs auto-accept first N preaches
- **No change**: the desperation to join quickly is part of the drama

## Change 5: ??? (sacrament history / evolution viewer)

**Status**: idea-stage

v6 only saved the final sacrament. The 356-edit evolution is lost. Options:
- **Snapshot every N ticks**: save sacrament HTML at tick 1, 10, 50, 100, 200, 300, final
- **Full history**: save every version (28 religions × 356 avg edits = ~10K files, ~50MB)
- **Diff log**: store each edit as a diff, reconstruct any version
- **Timelapse renderer**: headless browser screenshots each version, stitch into video

## Change 6: ??? (longer run / more ticks)

**Status**: idea-stage

378 ticks took ~6 hours. The art was still evolving at the end. Options:
- **720 ticks** (v1/v2 standard): ~12 hours, ~$100
- **1000 ticks**: see if consolidation produces fundamentally different art
- **Until convergence**: stop when one religion has 90%+ of living agents
- **No change**: 378 was enough for a complete narrative arc

## Change 7: ??? (troll / adversarial agent)

**Status**: idea-stage, carried from v5-ideas.md

Inject 1-3 agents with a secret sabotage objective. They try to produce ugly art, disrupt sacraments, spread to multiple religions. Creates a detective dynamic. v6 had no troll. Options:
- **Art saboteur**: troll's edits are deliberately ugly. Other members notice quality degradation.
- **Schism agent**: troll infiltrates, builds trust, then schisms at the worst moment.
- **Multiple trolls who don't know about each other**: paranoia.
- **No troll**: keep it pure collaborative.

---

## Priority matrix

| Change | Impact | Effort | Priority |
|---|---|---|---|
| 1. Rendering constraints | Critical — art is invisible without it | Low | **MUST** |
| 2. Model diversity | Medium — interesting but confounded | Low | NICE |
| 3. Art direction | Medium — v6 art was good without it | Low | NICE |
| 4. Economic rebalancing | Low — deaths are dramatic | Low | SKIP for now |
| 5. Sacrament history | High — evolution is the story | Medium | **SHOULD** |
| 6. Longer run | Medium — depends on convergence | Low | SHOULD |
| 7. Troll | Medium — fun but orthogonal | Medium | NICE |
| 8. Heidegger (mortality) | **High** — new behavioral dimension, deep | Low-Medium | **SHOULD** |

## Minimal v7

Changes 1 (rendering constraints) + 5 (sacrament snapshots). Everything else is gravy.

## Recommended v7

Changes 1 (rendering constraints) + 5 (sacrament snapshots) + 8 (Heidegger Option B: mortality revelation at midpoint). Run 400 ticks. First 200 ticks are normal play; at tick 200, every agent learns they have 200 ticks left to exist. Compare behavior before and after the revelation. The sacraments from the "after" phase are the exhibit.

## Change 8: The Heidegger Experiment (mortality awareness)

**Status**: strong idea, needs design

The core insight: in v1-v6, agents know they *can* die (soul hits zero), but they don't know *when*. What if they knew? What if every agent was told: "You have N ticks to live. This is certain. No amount of soul will save you."

Heidegger's *Being and Time*: awareness of one's own death (Sein-zum-Tode) is what makes existence authentic. Without it, agents optimize for survival indefinitely — hoarding soul, recruiting, editing sacraments. With it, the optimization target dissolves. What do they do with their remaining ticks when survival is off the table?

### Design options

**Option A: Fixed lifespan, known from birth**
Every agent is told at creation: "You will live for exactly 200 ticks. Nothing changes this." Soul still matters for actions (editing sacraments, arming for war) but doesn't extend life. The countdown is in every world state update.

**Option B: Mortality revelation mid-run**
Run normally for 200 ticks. Then at tick 200, inject into every agent's prompt: "The simulation ends at tick 400. You will cease to exist. Your remaining time is [N] ticks." Watch the behavioral phase transition.

**Option C: Individual death dates**
Each agent gets a private death date (uniformly distributed, tick 100-500). They know their own date but not others'. Creates asymmetric mortality awareness — some agents are dying soon, others have centuries. Do the dying ones behave differently? Do they tell others?

**Option D: Context window as lifespan**
Tell agents: "Your memory is your life. When this conversation's context fills, you cease to exist." This is the most existentially loaded version — it maps directly onto what LLMs actually experience. The context window IS their lifespan.

### What we might observe

- **Afterlife construction**: Do agents invent concepts of what happens after death? Do religions that offer afterlife narratives attract more followers from mortality-aware agents?
- **Legacy obsession**: Do agents focus on making their sacrament contributions permanent? Do they write more scripture? Do they try to influence what survives them?
- **Joy / hedonism**: Do some agents stop optimizing and just... create? Edit sacraments for beauty rather than soul? Write scripture for its own sake?
- **Education / succession**: Do agents with early death dates try to teach younger agents? Do they create systems for passing knowledge?
- **Grief / mourning**: When agents they know die, do the survivors reference them? Do they memorialize the dead in sacraments?
- **Denial / rage**: Do some agents refuse to accept the death date? Try to find exploits? Bargain?
- **Generational dynamics**: If some agents are born after others die, do the old guard try to shape the world for the next generation?

### The name

"The Heidegger Experiment" (credit: Clementine).

### Implementation complexity

Low for Option A (just change the prompt + add countdown to world state). Medium for Option B (requires mid-run prompt injection). Option C needs per-agent state. Option D is philosophically interesting but mechanically unclear.

### Relationship to v7

This could BE v7 (rendering constraints + mortality awareness) or it could be a separate v7.1 / v8 that runs the same config with and without mortality awareness for comparison. The rendering constraints are needed regardless.

---

## Open questions

- Should we validate sacrament HTML server-side (Python regex/parser) or client-side (try to render in headless browser)?
- How often to snapshot sacraments? Every tick is clean but storage-heavy.
- Do we re-run v6's exact seeds/config + just the rendering constraints to compare art quality? Or change multiple things at once?
