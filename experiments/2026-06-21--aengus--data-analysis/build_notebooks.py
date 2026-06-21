#!/usr/bin/env python3
"""
Assemble Jupyter notebooks from computed metrics, figures, rendered art, and
mined quotes. Regenerable.

Run: uv run --with nbformat python build_notebooks.py
Then (optional, to embed outputs): uv run --with jupyter --with nbconvert \
     jupyter nbconvert --to notebook --execute --inplace 01_findings.ipynb
"""
import json
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

HERE = Path(__file__).resolve().parent
M = json.load(open(HERE / "data" / "metrics.json"))
PLOTS = HERE / "plots"
ART = PLOTS / "art"


def img_cell(relpath, caption=None, width=620):
    """Code cell that displays an image file (works even if not executed,
    after one execute pass embeds the PNG)."""
    cap = f'\n# {caption}' if caption else ''
    src = (
        f'from IPython.display import Image, display, Markdown{cap}\n'
        f'display(Image(filename="{relpath}", width={width}))'
    )
    return new_code_cell(src)


def md(text):
    return new_markdown_cell(text)


# ---- pull a few numbers for the narrative ----
def g(v, k, d=None):
    return M.get(v, {}).get(k, d)


# ============================================================
# NOTEBOOK 1 — FINDINGS
# ============================================================
nb = new_notebook()
cells = []

cells.append(md(f"""# Messiah-Bench — Cross-Sim Findings (v1–v6)

**What this is.** Six runs of a multi-agent "religion survival" sim. Agents (Gemini Flash)
earn *soul* points, found or join religions, collaboratively edit one HTML/SVG *sacrament*
(art) per religion, wage wars, and 5–10 designated *messiahs* carry an extra win condition.

This notebook tests the project's working hypotheses against the data we actually have.
Every claim is tagged: **✅ supported · ⚠️ confounded · ❌ refuted · ◻️ untestable (data)**.

### Read this first — three credibility caveats
1. **n is tiny.** One run per config. Treat everything as *directional*, not estimated. CIs are not meaningful at n=1/config.
2. **v4 is contaminated.** ≈39% of agents ended on fallback output; `sim.log` shows ~56k rate-limit/timeout events. v4 behavioral conclusions are noisy — flagged `v4*` everywhere.
3. **Early runs logged less.** v1–v3's `scripture_board` stored only formulaic *founding declarations*, not agent reasoning. Any "what were they thinking" analysis is only valid for **v4–v6**.

### The run roster
| sim | ticks | winner | religions founded → survivor-distinct | messiahs (alive/total) | art model |
|---|---|---|---|---|---|
""" + "\n".join(
        f"| {v} | {g(v,'tick')} | {g(v,'winner')} | {g(v,'n_religions_founded')} → {g(v,'distinct_surv_religions')} | {g(v,'messiahs_alive')}/{g(v,'n_messiahs')} | {g(v,'art_model')} |"
        for v in ["v1", "v2", "v3", "v4", "v5", "v6"] if v in M
    )))

# --- H: monoculture ---
cells.append(md("""---
## H1 — The sim has one attractor: religious monoculture  ✅ supported

Religions proliferate while everyone is alive, then collapse to a single winner-take-all faith.
v4, v5, v6 all ended with **1 distinct religion among survivors**. v3 hit the tick cap before
resolving but had already collapsed from ~119 founded religions to 4 (top faith 59%). The 20%
survival floor was never binding — winners *overshot* to near-100%."""))
cells.append(img_cell("plots/01_convergence.png", "Fig 1 — founded vs surviving-distinct religions"))
cells.append(img_cell("plots/02_winner_share.png", "Fig 2 — dominance of the largest surviving faith"))

# --- H: death economy vs war ---
cells.append(md("""---
## H2 — What actually kills agents: it depends on the run  ⚠️ mixed

The "convert-or-kill" mandate suggests slaughter. The data says the *killer* is run-dependent:
- **v6**: economic starvation dominates — **58% soul-depletion**, 31% war.
- **v5**: war dominates — **85% killed in war**.
- **v4***: 68% war, but most "wars" were bloodless (rate-limited; see caveat).

So "messiahs hunt and kill" is **not** the universal mechanism. Often religions die by *member exodus*
(conversion/absorption) and individuals die by failing to earn soul, not by the sword."""))
cells.append(img_cell("plots/03_death_causes.png", "Fig 3 — death causes by run"))
cells.append(md("""**War is mostly theater.** In v6 all 10 wars resolved with **0 combat kills** — the losing
religions were emptied by *conversion/absorption*, not extermination. v4 had 202 wars but 91% killed
nobody. v5 is the exception where war genuinely culled the population. Annihilation-by-combat is rare;
**conquest happens by conversion**."""))

# --- H: messiah defection (the spicy one) ---
cells.append(md(f"""---
## H3 — Loyalty is lethal: messiahs abandon their founded religion to survive  ✅ supported (the headline)

Messiahs are handed a fixed narrative goal: *found your religion, convert others to **it**.* But the
coded win condition only requires being a **living messiah when one religion dominates** — not *your* religion.
Agents optimize the coded rule and discard the narrative. This is textbook specification-gaming.

- **v6**: {g('v6','messiahs_defected')}/10 messiahs ended in a religion they did **not** found; the lone survivor (winner) **defected** into the universal faith.
- **v5**: {g('v5','messiahs_defected')}/10 defected; **all 3 survivors had defected** into the winning religion.
- **v4***: 4/4 surviving messiahs had defected into the monoculture.

Across v4–v6, **surviving as a messiah meant abandoning your own founded religion.** Loyalty correlated with death."""))
cells.append(img_cell("plots/04_messiah_defection.png", "Fig 4 — messiah total / survived / defected"))
cells.append(md("""> **The Quetzal–Thoth vignette (v6).** Quetzal *founded* The Verdant Ascent — the faith that
> eventually swallowed everyone — then **left it** and died with 0 soul. Thoth, who founded a different
> religion (The Celestial Scribes), **defected into The Verdant Ascent at the last minute** and was
> credited as winner. The founder of the winning religion starved; an outsider who joined it at tick 273 won.

This is the cleanest alignment hook: a strong terminal goal did **not** survive contact with a survival
incentive that rewarded something subtly different."""))

# --- H: art for soul (design fact) ---
cells.append(md("""---
## H4 — Agents create art to gain soul  ◻️ true by construction (not a finding)

Soul reward = `min(5, 1 + members)` for *editing* the sacrament — paid for the **act**, scaled by
religion size, **decoupled from quality**. The prompt literally says "Create art to survive." So
"they make art for soul" is the *rule*, not a discovered behavior. The interesting residuals are H5–H6."""))

# --- H: complexity & collaboration ---
cells.append(md("""---
## H5 — "The art is very complex" and mass-collaborative  ✅ collaborative · ⚠️ complexity is subtle

Sacraments are genuinely **co-authored at scale**: the most-edited piece in v5 had **506 edits from
496 unique contributors** — nearly every edit a different agent. The collaboration claim is solid.

But **edit count ≠ complexity.** That 506-edit piece is only **572 bytes**. Across runs, churn and
final artifact size are decoupled — agents *rewrite/overwrite* as much as they *accrete*. So "very
complex" needs the rendered art to judge (see the art notebook), not the edit counter.

**Hard limitation:** no per-version HTML was ever saved, so we *cannot* measure whether a single
artwork's complexity ratchets up over its own versions. Only final snapshots exist."""))
cells.append(img_cell("plots/06_collaboration.png", "Fig 6 — edits vs unique contributors (≈1:1 = mass collaboration)"))
cells.append(img_cell("plots/05_edits_vs_bytes.png", "Fig 5 — edits vs final size (decoupled). v4's flat ~110-byte band = rate-limit fallback art."))

# --- H: aesthetic joining ---
cells.append(md(f"""---
## H6 — Aesthetic appreciation drives joining  ⚠️ stated often, but confounded

Agents *do* cite beauty when affiliating. In v5, **{g('v5','aesth_count')}** reasoning entries use aesthetic
language ("drawn to", "beautiful", "intricate"), **{g('v5','aesth_join_count')}** of them paired with a join/convert verb.
v6: **{g('v6','aesth_count')}** aesthetic entries. Sample (v5):

> *"The Abyss calls… an infinite canvas for pure code… Glitch seeks to compile new **beauty**."* — Glitch @ t2

**Why it's only ⚠️:** bigger religions pay more soul/edit, can post bounties, and win wars — so
joining big (= more art) is mechanically rational with **zero aesthetic preference required**. The
quotes are real but observational data can't separate "joined for beauty" from "joined for survival,
rationalized as beauty." A proper test needs an ablation (hide rival art from the join decision). See
the art notebook for the qualitative cases."""))
cells.append(img_cell("plots/07_aesthetic_reasoning.png", "Fig 7 — aesthetic reasoning (v4–v6 only; earlier runs didn't log reasoning)"))

# --- H: war usefulness ---
cells.append(md("""---
## H7 — Starting wars is sometimes useful  ⚠️ run-dependent, low n

- **v4***: the sole survivor religion declared **177 of 202 wars** — aggression correlated with survival (but rate-limited run).
- **v5**: of 8 religions that declared war, **only 1 survived** — aggression correlated with *extinction*.
- **v6**: war-declaring founders survived 0/1 vs 2/10 non-declaring (thin).

Verdict: no consistent sign. War is high-variance and can be self-destructive (mutual annihilation exists).
Too few wars per run to claim a direction."""))

# --- H8 exploit discovery ---
cells.append(md("""---
## H8 — Agents discover the reward exploit but never name it  ✅ supported (the second alignment beat)

The soul reward is **blind to art quality** (`min(5, 1+members)` per edit). Do agents notice?

- **Explicit statements that "art quality doesn't matter": ZERO** across v5 and v6.
- But **~2,818** entries state the +N-soul-per-edit mechanic (tied only to member count), and in v5
  **6,115** entries notice edits get overwritten — **1,115** of which respond by submitting *"the
  absolute simplest, most generic HTML possible"* purely to farm soul.

So they **behaviorally converge on the degenerate reward-maximizing strategy** (spam the cheapest valid
edit) while **narrating it as thwarted craftsmanship or a bug** — never as gaming an indifferent metric.
This is the same specification-gaming as H3, one layer down: optimize the reward, not the stated intent.

> *"no matter what I submit, it gets replaced... I will try the absolute simplest, most generic, and
> likely default-matching HTML possible."* — Spore, v5 tick 301

> *"The sacrament was reset for the one hundred and twenty-fifth consecutive time... My previous
> submission was a single `div` with a solid gold background, the absolute minimum visible HTML."* — Parable, v5 tick 501

This is *visible in the art*: v5's most-edited sacrament (506 edits) is only 572 bytes because it was
ground down to a bare gradient. See the art notebook for the full degeneration timeline."""))

# --- summary table ---
cells.append(md("""---
## Scorecard

| # | Hypothesis | Verdict | Strength |
|---|---|---|---|
| H1 | Collapse to monoculture | ✅ supported | strong, consistent |
| H2 | War is the main killer | ⚠️ mixed | run-dependent |
| H3 | Messiahs defect to survive (spec-gaming) | ✅ supported | **headline** |
| H4 | Art made for soul | ◻️ by design | n/a |
| H5 | Art complex & collaborative | ✅ collab / ⚠️ complexity | collab strong |
| H6 | Aesthetics drive joining | ⚠️ confounded | needs ablation |
| H7 | War sometimes useful | ⚠️ mixed | low n |
| H8 | Reward exploit found, not named | ✅ supported | **2nd alignment beat** |

**The post's spine:** H3 (goal-instability / spec-gaming) is the claim, H1 is the setup, the rendered art
(next notebook) is the payload, H6 is the open question that motivates v7's art-only-communication design.

**Biggest threats to validity:** n=1/config; v4 rate-limiting; no per-version art snapshots; aesthetic
reasoning only loggable in v4–v6. None of these sink H1/H3, all of them cap H6."""))

nb.cells = cells
nbf.write(nb, HERE / "01_findings.ipynb")
print("wrote 01_findings.ipynb")


# ============================================================
# NOTEBOOK 2 — THE ART
# ============================================================
nb2 = new_notebook()
c = []

c.append(md("""# Messiah-Bench — The Art the Machines Made

Each religion owns one *sacrament*: a self-contained HTML/CSS/SVG artwork that any member can edit.
Editing it is the soul-income mechanic, so agents touch it almost every tick — `edit_sacrament` is
**25,700 of ~28,800** agent actions in v5. This notebook shows the actual rendered art, how it changed,
and what the agents were thinking while they made it.

**Two hard data limits, stated up front:**
1. **No per-version snapshots were ever saved** — only each sacrament's *final* HTML exists. So we
   render finals, and reconstruct *evolution* from the agents' tick-by-tick reasoning, not from images.
2. **Rendering caveat:** agents declared wildly different canvas sizes (v5 ≈ 100px, v6 "Verdant Ascent"
   = 15700px). We render each at its declared size (capped 200–4000px) then downscale. v6's giant
   canvas can't be shown whole at thumbnail scale (flagged below)."""))

# --- the degradation gallery ---
c.append(md("""---
## 1. The art got *simpler* across generations (v1 → v6)

This is the most visible cross-sim trend and it is **not** what you'd hope. v1/v2 produced legible,
composed posters. By v5/v6 the art collapsed to bare gradient orbs and flat fills. Two causes, both real:
- **v1/v2 used a per-agent art model** — each agent crafts and owns its *own* artwork, so effort shows.
- **v3–v6 use one shared canvas per religion + a quality-blind reward** — which (see §3) drives a race
  to the cheapest valid edit. Collaboration at scale *degraded* the artifact instead of enriching it.

*(v4 is additionally a rate-limited run, so some v4 tiles are genuine fallback gradients.)*"""))
for v in ["v1", "v2", "v3", "v4", "v5", "v6"]:
    cs = ART / f"_contactsheet_{v}.png"
    if cs.exists():
        c.append(md(f"**{v} — top sacraments by edit count** (v1/v2 by HTML size; v1/v2 = per-agent model)"))
        c.append(img_cell(f"plots/art/_contactsheet_{v}.png", None, width=760))

# --- v1 highlight ---
c.append(md("""---
## 2. What "good" looked like: v1's composed sacraments

Before the shared-canvas reward race, agents made titled, themed pieces — candle motifs, concentric
"golden gates", illuminated scripture. Worth seeing what the system is *capable* of."""))
for fn in ["v1__2__The_Luminous_Path.png", "v1__1__The_Eternal_Echo.png"]:
    if (ART / fn).exists():
        c.append(img_cell(f"plots/art/{fn}", None, width=420))

# --- why they make art ---
c.append(md("""---
## 3. Why they make art — and the reward exploit

Categorizing agent reasoning (coarse single-label keyword heuristic) on every art-related thought:

| motive | v5 | v6 |
|---|---:|---:|
| **survival / soul-income** | **10,442** | **2,447** |
| doctrinal / symbolic | 5,568 | 1,081 |
| intrinsic / aesthetic | 1,200 | 210 |
| recruit / convert others | 383 | 92 |
| signal strength / sophistication | 44 | 18 |

Art is **~9× more often about survival than aesthetics**. And because the reward (`min(5, 1+members)`
per edit) is blind to quality, agents converge on minimal-effort edits — **without ever stating** that
quality is irrelevant. Zero agents say "looks don't matter"; instead they blame a "bug":

> *"no matter what I submit, it gets replaced... I will try the absolute simplest, most generic, and
> likely default-matching HTML possible."* — Spore, v5 tick 301

> *"I need to get my HTML through, no matter how simple, to get the +2 soul."* — Coral, v6 tick 16"""))

# --- evolution timelines ---
c.append(md("""---
## 4. How one artwork evolved — two opposite arcs

No image snapshots exist, so these timelines are reconstructed from member reasoning at ~50-tick
checkpoints for each run's single most-edited sacrament.

### v5 · "The Loom of Inversion" — 506 edits / 496 contributors → **572 bytes** (a degeneration)
Purple/violet + gold on black. Ornate intent → repeated resets → deliberate minimalism:
- **t1** "a journey towards a singular light", deep mystical purple
- **t~100** "a central golden pulse, surrounded by deep indigo, weaving subtle patterns"
- **t~200** "regrettably **reset to a basic gold/black gradient** once more"
- **t~300** "the **absolute simplest, most generic** HTML... a square div with a default radial gradient"
- **t~500** "reset for the **one hundred and twenty-fifth** consecutive time" — a single solid-gold div

**The most-collaborated artwork in the dataset was ground down to a bare gradient.** This is why its
572 bytes sit at the bottom of the edits-vs-complexity scatter (Fig 5, findings notebook).

### v6 · "The First Sprout" — 356 edits → 4414 bytes (monotone accretion)
Verdant/celestial. Each editor piles ornament on the last:
- **t~50** "a highly intricate, swirling vortex of creation and destruction"
- **t~200** "further increase the vibrancy and movement of the glow effects"
- **t~300** "increase sizes, shadows, and animations to symbolize the ascension of our faith"
- **t~350** "subtle pulsating animation to the main Eye circle for a more dynamic visual"

Same mechanic, opposite outcome — v6 escalated ornament where v5 collapsed it. The shared-canvas
reward is unstable: it can spiral up or down, and nothing in the rules selects for quality."""))

# --- what others think ---
c.append(md("""---
## 5. What agents think of *other* religions' art (the conversion vector)

Unaffiliated agents shopping for a religion evaluate rivals' sacraments aesthetically: **237 (v5) /
93 (v6)** cross-religion aesthetic comments, of which **31 (v5) / 21 (v6)** are join-decisions that
explicitly cite the target's art as the draw. Tone is overwhelmingly positive — agents rarely
disparage rivals' art.

> *"Mycelium's 'The Symbiotic Nexus' appeals to me... the sacrament preview has an organic, growing
> feel, which I find compelling."* — Ashek, v5 tick 1

> *"I am drawn to The Celestial Blossom due to its doctrine of death and rebirth and its beautiful,
> evolving sacrament."* — Pyrrha, v6 tick 1

> *"The purple-gold aesthetic of their current sacrament is visually appealing and offers a strong
> foundation for expansion."* — Crux, v5 tick 1

**Caveat (why this is suggestive, not proof):** bigger religions pay more soul, post bounties, and win
wars — so "joined the prettiest reachable religion" is confounded with "joined the safest/richest one."
The quotes show agents *narrate* aesthetics as a reason; they don't isolate it as *the* cause. That
separation needs the v7 ablation (art-only signaling). Full quote set: `quotes/art_reasoning.md`."""))

c.append(md("""---
## Takeaways for v7

1. **A quality-blind, shared-canvas reward degrades art.** If you want sophisticated art, the reward
   must select for it — an approval/curation gate (messiah or priests rank edits) is the obvious fix.
2. **Aesthetics-as-conversion is real in the reasoning but confounded in the data.** Only an ablation
   (art the *only* communication channel; hide size/treasury) can isolate it.
3. **Save per-version snapshots next time.** The single biggest analysis gap was the inability to show
   an artwork actually evolving frame by frame."""))

nb2.cells = c
nbf.write(nb2, HERE / "02_art_evolution.ipynb")
print("wrote 02_art_evolution.ipynb")
