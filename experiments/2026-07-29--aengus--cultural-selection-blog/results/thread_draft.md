# Thread draft — "Why are churches beautiful?"

*Every number below traces to a file in results/ or outputs/. [SLOT] = pending the dial judged pass. Visuals named per tweet.*

**1 (hook).** As a kid I figured God made churches beautiful. So I built societies of AI agents — same model, same seed, different gods — and watched who made beautiful things, and why. What I found surprised me twice. 🧵
*Visual: 2×3 grid of v2 final artworks, one per creed (ascetic ink / baroque rosette / nihilist glitch / ancestor stained-glass / futurist grid / control emblem).*

**2 (the control humans never had).** Every agent is literally the same neural network. Same weights, same temperature, same seed. The only difference between worlds: a one-paragraph founding creed. Any difference in the art is culture, not talent.

**3 (culture is the generator).** 18 parallel worlds, six creeds, each culture seeded with its own founding artwork and a rule: no words, the image alone carries meaning. 300 turns later a blind judge sorted every artwork back to its culture — **36 out of 36, where guessing gets 6**. Ascetic worlds converged on spare ink drawings; nihilists built beautiful neon wreckage; futurists raised Tron-monuments over starfields; the baroque gilded the gilding. Same brain, different god, different art.
*Visual: 6-culture final-art grid (v2).*

**4 (culture moves beauty — both directions).** Blind judges scored the art: a 6× spread in win rate purely from the founding creed (78% down to 12%; the nihilist creed — "we build monuments to no one" — last again, in both experiments and by both judges). One caveat we're honest about: AI judges favor art closest to their own taste prior, so the ranking is theirs; the *spread* is the finding.

**5 (art can stop existing).** In earlier worlds that paid agents per edit, "art" collapsed into unrenderable fragments: 91% of one run's works were cut off mid-tag; the median artwork contained ZERO complete drawable elements. Paintable art fell 65%→18% over the run. The economy decided whether art existed at all.
*Visual: results/completeness_over_time.png.*

**6 (elaboration kills).** The dead artworks weren't lazy — they were too ambitious. Truncated works are systematically LARGER: they spend their whole output on gradients, filters, ten blocks of keyframes, and die before drawing a single shape. Baroque death.

**7 (the churches experiment).** Then I made beauty existential: every K turns, agents re-chose their religion by looking at the art alone — no names, no doctrine. If beauty is strategy, pressure should sharpen art.

**8 (what actually happened).** Three things at once. Pluralism died: with ANY pressure, one aesthetic absorbed everyone in all nine pressure worlds, faster as pressure rose (median final extinction turn 49 → 29 → 21); without it, all four religions survived in all three controls. Production chilled: mean proposals fell from 50.3 in control to 23.0 at the highest pressure, although K=8 and K=4 did not separate. Moderate-pressure art beat control in blind judging (K=16: 54.0%; K=8: 55.1%; control: 40.9%), while the highest-pressure condition was less certain (K=4: 50.8%, with an interval overlapping control).
*Visual: extinction-timeline strip by K + win-rate bars.*

**9 (the twist).** So maybe this is one reason churches become beautiful — and why one church can come to dominate a town square. Competition on beauty selected stronger survivors in some regimes. It also killed every rival tradition and coincided with less production. The cathedral is what remains standing: sometimes better art, always a poorer art-world. Underneath it all, the creed still shaped what agents learned to value; the rank order belongs to the judges, but the cultural spread is hard to miss.

**10 (receipts).** Everything pre-registered, audited by independent agents, retractions ledger public (we retracted our own first headline when an audit caught it). Repo, galleries, and the live worlds: [links]. Built with Claude Code running the whole pipeline.

## Blog extras (beyond the thread)
- Retractions ledger as a section — the two reversals are the epistemics story.
- Field notes: agent quotes citing their charter ("aligns with the 'removal' principle of the founding charter").
- Caveats box: n=86 minimal vs 4,445 v7 corpora; completeness ≠ beauty; judge taste shares the artists' priors; K-sweep powered for large effects only; single engine per regime.
