# Why are churches beautiful? — brainstorm

## The thesis

**Art has makers, but a tradition has no single designer. Culture shapes the visual inheritance, the legitimate next move, and which experiments survive.**

Hook for the blog: a church is visibly authored, yet no one person designed the tradition that makes it intelligible. The simulations provide a control human history cannot: *identical individuals* (same model and weights), placed inside different cultural inheritances. The deepest question is not merely whether culture changes art, but how much guidance is explicit doctrine, inherited example, tacit convention, or selection across many local choices.

## The one big question

**How does cultural context inspire art?**

### Sub-questions / claims to test

1. **Culture is the generator.** Same model, different culture → different art. (Twin-worlds test: parallel runs identical except the seeded culture charter; measure divergence of art lineages.)
2. **Competition breeds beauty.** Regimes we already ran are the natural comparison: soul-economy free-for-all (v5/v6), locked pluralism (v7), PR curation (v8), make/choose influence (Experiment IX). Which regime's art wins a blind tournament?
3. **Monoculture kills art.** v1–v6 collapse + Experiment IX's own headline ("Art became currency. Currency became monoculture."). Claim: novelty needs living rivals.
4. **Existential threat sharpens art** — or crushes it. v8's war mechanic failed (0 wars, messiah extinction); replace violence-as-combat with *conquest-by-conversion*: agents defect to the culture whose art moves them. War fought entirely in aesthetics.
5. **Sacredness matters (or doesn't).** Secular control: same engine, religion framing stripped, "just cultures, secular art." Does removing the sacred flatten the art?
6. **Patronage vs free expression.** A central body commissions works (the church model) vs open submission. Which produces the cathedral?

## Sub-agent fleet (the "really cool" machinery)

- **Blind judge tournament** — panel of diverse models scores artworks with all context stripped; ELO across regimes/cultures/turns. This is the measurement backbone for every claim above.
- **Art historian agent** — reads a lineage's snapshots + private reasoning, writes the history of a style: motifs, borrowings, ruptures. Output goes straight on the website.
- **Anthropologist agent** — reads decisions.jsonl, characterizes each culture's values from behavior, not charter. Do stated values predict the art?
- **Novelty scorer** — embedding distance (render → CLIP or code-embedding) between versions and across cultures; detects convergence/theft quantitatively.
- **Ablation runner** — orchestrates fleets of cheap minimal-engine runs ($7 each!) varying one knob per fleet.
- **Curator agent** — picks the film-strip frames for the "watch one culture's art evolve" viewer.

## Concrete next experiments (build on the minimal make/choose engine, not v8)

- **E1 Twin worlds** (n≈6): identical init except culture charters (ascetic / baroque / nihilist / ancestor-cult / futurist / control-blank). Cheapest, cleanest test of H1/H4.
- **E2 Threat dial**: add a conversion-pressure knob (agents periodically re-choose allegiance based on art alone; shrinking cultures die). Sweep the dial, plot art quality (blind ELO) vs pressure. Tests H2.
- **E3 Secular control**: strip religious vocabulary from prompts, keep mechanics. Tests claim 5.
- Deliverable per run: film-strip of the canonical artwork over time + judge scores over time. The evolution-over-time visual is the star of the blog.

## Next causal program: what kind of culture produces what kind of art?

Hold the founding image, written creed, model, seed and opportunity to make fixed. Cross social structure independently so institutional effects are identifiable:

- **Conformity:** reward similarity to the inherited canon ↔ reward legible deviation ↔ neutral adoption.
- **Hierarchy:** one central patron/curator commissions and selects ↔ distributed proposal and adoption ↔ prestige-weighted intermediates.
- **Population:** isolated native populations ↔ periodic migration ↔ continuous mixing, with ancestry labels hidden from judges.
- **Transmission channel:** charter only ↔ visual ancestor only ↔ lineage history only ↔ combinations. This separates explicit instruction from visual and historical inheritance.

Primary outcomes are inspectable cultural histories, not only scores: matched early/mid/late art, accepted revision notes, motif persistence and rupture, lineage depth, visual dispersion, borrowing after migration, and blinded human descriptions of what changed. A novelty metric may support the read, but cannot substitute for it.

## Blog shape (tweet → post)

Tweet: "Why are churches beautiful? I ran societies of identical AI agents that differ only in culture. The cultures that made better art won converts. Beauty is strategy. 🧵" → each claim above is one tweet with a film-strip GIF → post has the full lineages, quotes from agent private reasoning, and the monoculture collapse arc.

## Falsification pass (kill the compact story)

- If twin worlds *converge* despite different charters, culture isn't the generator — the model's prior is.
- If the threat dial shows flat or declining quality with pressure, "beauty is strategy" dies; peaceful pluralism (v7-style) would be the real muse.
- Judge-model taste is a confound: judges and artists share priors. Mitigate with heterogeneous judge panel + human pairwise voting on the site.
