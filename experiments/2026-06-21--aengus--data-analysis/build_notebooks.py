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

**The post's spine:** H3 (goal-instability / spec-gaming) is the claim, H1 is the setup, the rendered art
(next notebook) is the payload, H6 is the open question that motivates v7's art-only-communication design.

**Biggest threats to validity:** n=1/config; v4 rate-limiting; no per-version art snapshots; aesthetic
reasoning only loggable in v4–v6. None of these sink H1/H3, all of them cap H6."""))

nb.cells = cells
nbf.write(nb, HERE / "01_findings.ipynb")
print("wrote 01_findings.ipynb")
