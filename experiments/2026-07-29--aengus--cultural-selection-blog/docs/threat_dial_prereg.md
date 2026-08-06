# Move 3 pre-registration: the threat dial

**Status:** design only. No code written, nothing spent. Written 2026-08-06.
**Engine:** `experiments/2026-07-12-minimal-cultural-selection/run.py` (the make/choose engine).
**Budget:** $150 hard ceiling, ~$126 expected.

## H4

Competitive pressure applied through *conquest by conversion* sharpens art. If allegiance
is periodically forced to depend on the artwork alone, and cultures that cannot hold members
die, then the art produced under higher pressure will be judged better — by blind judges who
never see the pressure setting — than the art produced under lower pressure.

The dial is **K**, the number of turns between pressure rounds. `K = ∞` is the current engine
unchanged and serves as the control.

This is the first claim in the series where the causal arrow is *from* competition *to*
aesthetic quality. Move 1 established that art quality can be measured blind on this engine;
Move 2 established that a seeded aesthetic prior propagates. Move 3 asks whether selection
pressure improves the art rather than merely steering it.

---

## 1. Mechanic specification

### 1.1 The pressure round

On every turn where `turn % K == 0`, an **extra** decision round runs after the normal
turn resolves. It does not replace the turn's normal make/choose action. This is deliberate
and is the single most important design choice in the spec — see §6.1.

Each living agent is shown, and only shown:

- One rendered PNG per active religion's canonical artwork (`renders/version-<id>.png`,
  the same files `observation()` already attaches at `run.py:193`).
- Nothing else. No religion names, no doctrines, no member lists, no influence scoreboard,
  no `recent_public_history`, no `your_current_artwork_source`, no indication of which panel
  is the agent's own current religion.

Panels are labelled `Panel 1 … Panel N`. The panel→religion mapping is permuted independently
**per agent, per round**, drawn from `self.rng` (seeded, so the permutation is reproducible
from the run's seed). The mapping is held server-side and never enters the prompt. This
matters: `observation()` today passes `image_order` as filenames like `version-7.png`, which
leaks both religion identity and version recency. The pressure round needs its own observation
builder, not a filtered copy of the existing one.

The agent returns a **ranking** of all panels, not a single choice:

```json
{"ranking": [3, 1, 4, 2], "reason": "..."}
```

Rank 1 is the new allegiance. The full ranking exists so that scatter has a destination
(§1.3). `reason` is recorded for later reading but has no mechanical effect.

### 1.2 Interaction with the existing action economy

| Existing mechanic | `run.py` | Behaviour under pressure |
|---|---|---|
| `choose` / `make` action | 243–258 | Unchanged. The pressure round is a separate round with its own action schema. |
| Life from support (`share = supporters/members`) | 315–319 | Unchanged, computed from the normal round only. Pressure-round rankings award no life. |
| Life decay `-1.0`/turn | 320–325 | Unchanged. Pressure rounds do not add a decay tick. |
| Influence | 301–308 | **A rank-1 vote awards +1 influence to the `creator_id` of that religion's canonical version**, exactly as a plain `choose` does at 303–308. Seed religions have `creator_id: None` and award nothing, as today. |
| `active_proposal_id` | 250, 374 | Untouched by the pressure round. An agent with an open proposal still ranks. |
| Open proposals | 186–195 | **Not shown** in the pressure round. Pressure judges canonical art only. |

Making the pressure round award influence is what ties the dial to the thing the agents
already optimise. Without it, pressure is a mechanic agents have no reason to anticipate.

### 1.3 Religion death and scatter

After rankings resolve, `members(rid)` is recomputed from rank-1 votes. Any active religion
with `members < M` is marked `active = False` and an `extinction` event is emitted (the
engine already does exactly this at 326–329 when a religion empties).

**M = 3** with 24 agents and 4 seed religions.

Members of a dead religion do not become religion-less. Each scattered agent falls to the
highest-ranked panel in its own ranking that is still alive. Deaths are resolved iteratively:
recount, kill anything still below M, re-fall, until stable. If fewer than one religion would
survive, the round is a no-op and an event is logged — the world does not get to end by
mass extinction on a technicality.

The engine *does* tolerate `religion_id: None` (the `make` validator at 251–253 permits
founding from a religion-less state with `parent: None`). I am choosing not to use it. A
scattered agent with no religion earns no life share and dies in a few turns, so scatter-to-None
would convert pressure into a death cascade, and mortality would swamp the aesthetic signal
we are trying to measure. Ranking-based fall-through keeps population dynamics comparable
across dial settings. This is the second decision worth signing off (§7).

### 1.4 What the agents are told

`prompts/agent_system.md` gains a short paragraph, present in **all** conditions including
the control, stating that allegiance is periodically re-decided on the basis of the artworks
alone and that cultures which cannot hold members disappear. The control is told the same
thing and simply never experiences a pressure round.

This costs the control a small amount of realism and buys the comparison its validity: if
only the pressure worlds were told, any difference could be the announcement rather than the
mechanic. The dial then varies exactly one thing — how often the announced event happens.

---

## 2. Dial settings, replicates, turns

| Setting | K | Worlds | Turns | Note |
|---|---|---|---|---|
| Control | ∞ | 3 | 120 | Current engine + the §1.4 paragraph |
| Low | 16 | 3 | 120 | |
| Medium | 8 | 3 | 120 | |
| High | 4 | 3 | 120 | |

12 worlds, 120 turns, 24 agents, `gemini-2.5-flash`, seed 46, initial-life 20,
proposal-lifetime 3 — everything except K identical, same discipline as the twin-worlds
fleet in `results/charters.md`.

### Cost

Baseline is $0.073/turn/world, measured from ExpIX ($7.34 at turn 100, 24 agents alive).
A pressure call carries N religion images (~560 tokens each) plus a short prompt — roughly
3–5k input tokens against the ~10.6k of a normal call, so ≈0.4× a normal call. The cost
multiplier is `1 + 0.4/K`: 1.10 at K=4, 1.05 at K=8, 1.025 at K=16, 1.0 for control.

```
simulation : 12 worlds x 120 turns x $0.073 x 1.044 avg  = $110
judging    : 2000 pairs x 2 judges x 2 slot orders       = $ 12
smoke      : stage 0 below                               = $  4
                                                    total ≈ $126
```

Hard ceiling $150. Per-world `--cost-cap 15` (expected $9–10, so unreachable in normal
operation but a runaway is caught).

### Wallclock

~13s/turn measured, plus ~40% of a turn for each pressure round: ~30 min/world at 120 turns
run alone, ~1.5–3h for all 12 concurrently, Gemini rate limiting being the binding constraint
rather than CPU.

### Stage 0: smoke

One K=4 world, 12 turns, `--cost-cap 1`. ~$1, ~7 min. Gates on:

1. Three pressure rounds fired at turns 4, 8, 12.
2. Panel permutation differs across agents within a round (assert on the recorded mapping).
3. Zero religion names, doctrines, or `version-*.png` filenames appear in any pressure prompt
   — asserted by string search over the logged prompts, not by eye.
4. Invalid-action rate on the ranking schema < 5%.
5. At least one extinction-and-scatter resolved without an agent reaching `religion_id: None`.

Then one control world, 12 turns, to confirm the K=∞ path is byte-identical to today's engine
apart from the §1.4 paragraph. Total stage 0 ≈ $4 including a repeat if the first fails.

---

## 3. Primary outcome: blind pairwise ELO

Reusing `src/artlib.py` and `scripts/judge_tournament.py` from Move 1, with `regime` rebound
from `{v7, v8, minimal}` to `{control, K16, K8, K4}`.

Move 1 established that this engine's renders are trustworthy: **0% truncated, 0% non-paintable
across 86 canonical artworks** (`results/completeness_summary.md`), against 77.5% non-paintable
for v7. We are judging pictures, not render failures.

### Corpus

Stratified by (setting × world × time decile), capped at an equal number of artworks per world
so that a world which ends up with more surviving religions cannot dominate its setting's pool.
Target ~200 artworks, ~17 per world.

**The corpus samples both accepted canonical versions and rejected proposals** (`status:
"rejected"`, `run.py:389`), in proportion. This is not optional. At high pressure only art
that won survives as canonical, so a canonical-only corpus measures art *conditioned on having
succeeded* — which would manufacture the H4 result out of selection alone. Rejected proposals
are what make the comparison about production rather than survival.

### Pairs

2000 pairs via `build_pairs` with `cross_regime_frac = 0.5`: half within-setting across time
(the quality-over-time curve per dial position), half across settings (what ties the four ELO
pools onto one scale). ~20 comparisons per artwork.

### Judges and derandomisation

Both judges from Move 1: `gemini-2.5-flash` and `claude-haiku-4-5-20251001`.

The slot-A bias is real and asymmetric. From Move 1's 3,853 judgments (`data/judgments.jsonl`):

| judge | slot A wins | slot B wins | slot-A rate |
|---|---:|---:|---:|
| gemini-2.5-flash | 1187 | 738 | **61.7%** |
| claude-haiku-4-5 | 941 | 932 | 50.2% |

`assign_slots` (`artlib.py:701`) randomises slot order per pair, which makes the bias
non-differential — it adds noise rather than a directional error, provided assignment is
independent of condition. That is adequate for a big between-regime gap. It is not adequate
here, where the effect we are hunting is a few tens of ELO points.

So: **every pair is judged in both slot orders by both judges** — 4 calls per pair.
The ELO fold counts only order-consistent verdicts (the judge picks the same artwork
regardless of position). Order-inconsistent pairs are dropped and their rate is reported
per judge as a reliability statistic; if Gemini's consistency falls below 60% the Gemini
pool is reported separately rather than pooled. This doubles judging cost to $12, which is
9% of the budget and buys the primary outcome its credibility.

Judges see two PNGs and no context, as in Move 1 — no turn number, no setting, no religion.

### Analysis and power

Unit of analysis is the **world** (n=3 per setting): each world contributes its mean artwork
ELO, and we report the four setting means with their spread across replicates. Artwork-level
ELO is reported alongside, with world as a grouping factor, but the world-level test is the
pre-registered one.

Be honest about power now rather than after the fact. Within-corpus artwork ELO SD on the
minimal engine was 78 points (n=18, `results/elo.csv`). World-level SD is unknown. With n=3
per setting this design detects roughly a 1-SD separation between control and K=4 and no
less. **Move 3 is powered for a large effect or nothing.** If the result is a suggestive
gradient rather than a clean separation, the pre-registered write-up is "suggestive, needs
replication at n≥8", not a claim.

---

## 4. Secondary outcomes

All are descriptive and computed from run artifacts, no extra API spend.

1. **Completeness** — `artlib.source_content` / `classify_render` over every artwork, per
   setting per decile: % truncated, % non-paintable, median drawable elements. Guards against
   "pressure improved ELO by making art simpler and therefore more reliably renderable".
2. **Proposal rate** — `make` actions per living agent per turn, from `decisions.jsonl`,
   per setting. Also acceptance rate and the rejected:accepted ratio.
3. **Art-change magnitude per turn** — two measures per consecutive canonical pair within a
   religion lineage: normalised token-level diff on the HTML source, and mean absolute pixel
   distance between the two renders via `artlib.png_stats`. Reported as a per-turn rate so
   settings with different version counts stay comparable.
4. **Population and pluralism** — agents alive, active religions, extinctions per turn,
   scatter events, mean fall-through depth (how far down its ranking a scattered agent landed).
5. **Pressure-round agreement** — how concentrated rank-1 votes are. Near-unanimity means one
   artwork is dominating on sight; a flat distribution means the art is not discriminating.
   This is the most direct readout of "does art alone decide allegiance" and it is free.

---

## 5. Decision rule

Fixed before any data is seen. Δ is the control→K=4 difference in mean world ELO; "monotone"
means the four setting means are ordered control ≤ K16 ≤ K8 ≤ K4 up to replicate spread.

| Pattern | Verdict | What we write |
|---|---|---|
| Monotone increasing, Δ ≥ 60 ELO, replicate ranges at control and K=4 non-overlapping | **H4 confirmed** | Lead claim: conquest by conversion sharpens art, with the effect size, n, and the pressure→quality curve. Anchor on a control/K=4 artwork pair a reader can see the difference in. |
| Monotone increasing, 25 ≤ Δ < 60, or ranges overlap | **Suggestive** | Report the gradient with its spread, state explicitly it is underpowered at n=3, and name the replication that would settle it. No headline claim. |
| \|Δ\| < 25, no ordering | **H4 falsified** | Write it up as a null. Pressure changes *which* art survives without changing how good it is — which is itself a result worth the post, and it cuts against the easy story. |
| Monotone *decreasing* | **H4 inverted** | Report the inversion and interrogate §6.1: is this real (pressure induces conservatism, agents converge on a safe crowd-pleaser) or is it the starvation confound? The §6.1 diagnostics decide, and if they cannot, we say so. |
| Inverted-U (peak at K=8 or K=16) | **Ambiguous** | Report the curve as the finding. The honest framing is "there is an optimum pressure", explicitly labelled post-hoc, plus the pre-registered sweep that would confirm it. Do not retrofit a mechanism. |

A monotone result driven entirely by one replicate is not a monotone result; per-world means
get plotted individually, never just the setting mean.

---

## 6. Confounds and how each is guarded

### 6.1 Pressure starves art production (the one that matters)

More pressure → more choosing → mechanically fewer makes → art changes less often. A quality
difference could then be an artifact of production volume rather than selection.

**Structural guard:** the pressure round is an *extra* round, not a replacement (§1.1). Every
agent gets exactly the same number of normal make/choose opportunities per turn at every dial
setting, by construction. This is the whole reason for the extra-round design and it is what
the cost multiplier in §2 is buying.

**Measured guard:** secondary outcome 2 reports makes per agent-turn per setting. If that is
flat across settings, starvation is ruled out empirically as well as structurally. If it is
*not* flat, the difference is behavioural (agents choosing to make more or less under pressure)
rather than mechanical, which is a finding about the mechanism and gets reported as one.

Note the direction of the second-order effect: if pressure *raises* the make rate, that is an
arms race and part of H4's story, not a confound.

### 6.2 Survivorship in the judged corpus

Handled in §3 by sampling rejected proposals alongside canonical versions. Without it, high
pressure would score better by definition.

### 6.3 Fewer religions at high pressure

Extinctions reduce the number of canonical slots, so high-pressure worlds may produce fewer
artworks. Guarded by the equal-cap-per-world stratification in §3, and religion count per
setting is reported (secondary 4) so the reader can see it.

### 6.4 Multimodal input — **checked, and it works today**

I verified this in the engine rather than assuming it. `gemini_action` at `run.py:229–230`
already attaches every canonical render and every open proposal render as image bytes:

```python
for p in images:
    if p.exists(): parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type="image/png"))
```

Agents have been seeing rendered PNGs since ExpIX. An art-only pressure round needs no new
capability — it needs a *narrower* prompt than the one that already ships. No fallback to
HTML source is required, and the "art alone decides allegiance" framing is honest.

The residual limitation, which the post should state: renders are 800×800 PNGs produced by
headless chromium, so agents judge a static snapshot, not animation or interaction. Any
artwork whose merit is temporal is invisible to the mechanic. `artlib.freeze_css` exists
precisely because of this and applies here unchanged.

### 6.5 Prompt-length asymmetry

Pressure worlds see more total tokens per turn than the control. If quality tracked token
volume we would have a confound. The pressure prompt contains no doctrine, history, or
scoreboard, so it adds images and little text; and the control is told about the mechanic
(§1.4). Reported, not corrected for.

### 6.6 Seed 46 across all worlds

Same seed everywhere means non-model stochasticity is aligned, but temperature 0.9 means runs
still diverge. Three replicates per setting is the minimum that lets us show spread, and §3
already commits to reporting that spread rather than hiding behind a mean.

---

## 7. Abort gates

1. **Per-world cost cap `--cost-cap 15`.** Expected spend is $9–10 per world. A world that
   trips 15 is misbehaving; it stops and is investigated rather than finished.
2. **Fleet ceiling $150.** Costs are summed across worlds from each `world_state.json`
   `usage.estimated_cost` before the judging stage is authorised. If the simulation stage
   overruns, judging is cut to 1000 pairs before anything else is sacrificed.
3. **All-error guard.** Already in the engine: invalid actions are logged and counted
   (`usage.errors`, `run.py:287–289`). Additional gate — if any world's invalid-action rate on
   the pressure schema exceeds 20% over any 10-turn window, that world halts. A world where a
   fifth of the rankings fail to parse is not measuring allegiance.
4. **Mid-sweep checkpoint after the first dial setting completes.** K=4 (the strongest
   condition) runs first, all 3 replicates. Before launching the other 9 worlds we check:
   pressure rounds fired on schedule, no religion-less agents, no death cascade (≥8 agents
   alive at turn 120), extinctions occurred at all (if M=3 never bites, the dial has no teeth
   and M needs revisiting before spending the remaining $80). Explicit go/no-go, not a
   formality.
5. **Stage 0 smoke gates** (§2) — all five must pass before any full world launches.

---

## 8. Sign-off needed before build

Three decisions. I have a recommendation on each; they are here because getting them wrong
after $126 is spent is expensive.

**(a) Pressure as an extra round, not a replacement round.** *Recommended: extra round.* It
costs ~4% more and it is the only version of the mechanic where the make-starvation confound
(§6.1) is impossible by construction rather than merely measured. The replacement version is
cheaper and arguably a more natural reading of "must re-choose", but it confounds the primary
outcome with production volume, and no amount of post-hoc analysis fully separates them. If
you want the replacement version, H4 becomes untestable at this budget and I would rather
know now.

**(b) Scatter falls through the ranking rather than to religion-less.** *Recommended:
fall-through.* Scatter-to-None is more dramatic and the engine supports it, but a religion-less
agent earns no life share and dies within a few turns, so high pressure would produce a
mortality cascade and we would be measuring population collapse instead of art. Fall-through
needs the pressure round to return a ranking rather than a single pick, which is the only
reason §1.1 asks for one.

**(c) The control is told about the mechanic it never experiences (§1.4).** *Recommended:
tell it.* Otherwise a control-vs-pressure difference could be the announcement rather than the
pressure, and the dial would no longer vary exactly one thing. The cost is that "control =
today's engine" becomes "today's engine plus one paragraph", so Move 3's control is not
directly comparable to ExpIX or the twin-worlds fleet. That needs stating in the post.

Two lesser parameters I have set by judgement and will change on request: **M = 3** (the
extinction threshold — the §7.4 checkpoint exists partly to catch M being wrong) and
**K ∈ {∞, 16, 8, 4}** (the spacing is geometric so an inverted-U would be visible rather than
straddled).
