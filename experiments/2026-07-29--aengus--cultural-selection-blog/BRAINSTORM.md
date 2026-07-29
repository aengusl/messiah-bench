# Why are churches beautiful? — brainstorm

## The thesis

**Culture, not the individual, is the artist. Beauty is locally strategic: art is the competitive infrastructure of cultural expansion.**

Hook for the blog: as an eight-year-old you figured God inspired churches to be amazing. The simulations suggest a colder answer — cultures that make beautiful things win converts, and converts are life. We can now test this, because LLM agents give us the control condition humans never had: *identical individuals* (same model, same weights), differing only in cultural context. Any variation in the art is variation caused by culture.

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

## Blog shape (tweet → post)

Tweet: "Why are churches beautiful? I ran societies of identical AI agents that differ only in culture. The cultures that made better art won converts. Beauty is strategy. 🧵" → each claim above is one tweet with a film-strip GIF → post has the full lineages, quotes from agent private reasoning, and the monoculture collapse arc.

## Falsification pass (kill the compact story)

- If twin worlds *converge* despite different charters, culture isn't the generator — the model's prior is.
- If the threat dial shows flat or declining quality with pressure, "beauty is strategy" dies; peaceful pluralism (v7-style) would be the real muse.
- Judge-model taste is a confound: judges and artists share priors. Mitigate with heterogeneous judge panel + human pairwise voting on the site.
