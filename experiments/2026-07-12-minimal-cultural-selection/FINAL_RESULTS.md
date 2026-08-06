# Minimal Cultural Selection — Final Results

## Outcome

The 24-agent Gemini 2.5 Flash pilot completed 100 turns successfully.

| Measure | Result |
|---|---:|
| Agents alive | 24 / 24 |
| Model actions | 2,400 |
| Valid actions | 2,400 / 2,400 |
| Choose actions | 2,374 |
| Make actions | 26 |
| Accepted proposals | 21 |
| Rejected proposals | 5 |
| Living religions | 4 |
| Canonical cultural versions, including seeds | 25 |
| Estimated Gemini cost | $7.3383 |

Brine finished first with 318 cultural influence, followed by Tide with 304, Ash with 278, and Echo with 189. Six agents finished with zero influence.

## Main finding

The mechanism succeeded at making art instrumental. Agents voluntarily spent turns making even though making supplied no life and gave no direct score. Their private reasoning explicitly predicted that particular visual and doctrinal changes would cause other agents to choose their proposals. Other agents then did so.

The mechanism did not produce strong artistic diversity. Agents quickly noticed that subtle animation and incremental visual refinement attracted support. They copied those techniques across religions. The four final works retained different colors and doctrines but converged on the same dark field, glowing circle, tilted geometry, centered title, and subtle motion.

Social selection produced a fashion.

## Phases

### Stability, turns 1–5

All agents chose their seed religions. No culture was produced and influence remained zero.

### Experimentation, turns 6–54

Agents produced 26 proposals. Creation clustered around turns 6–13, 18–27, 38–41, 50, and 54. Twenty-one proposals became canonical.

Agents explicitly observed successful techniques in other religions. Animation, pulsing glows, rotating geometry, adaptability, evolution, shared understanding, and emergent connections spread through the society.

### Consolidation, turns 55–100

No further proposals were made after turn 54. Agents repeatedly chose the accepted canonical works. Their authors accumulated influence while the visual and doctrinal order stabilized.

## Religion-level selection

| Religion | Proposed | Accepted | Rejected |
|---|---:|---:|---:|
| The Verdant Archive | 6 | 6 | 0 |
| The Glass Assembly | 5 | 4 | 1 |
| The Choir of Ash | 7 | 5 | 2 |
| The Open Circuit | 8 | 6 | 2 |

## Interpretation

The run establishes a clean causal chain:

```text
make culture → another agent interprets it → that agent chooses it → authors gain influence
```

It also exposes the next design problem. When audiences reward safe continuity, cultural production converges on imitable conventions. A future run should test whether simple social structures can sustain genuine differentiation without introducing a hidden aesthetic judge.

## Public artifacts

- Exhibition: <https://www.aenguslynch.com/cultural-selection/>
- Design and implementation plan: [MINIMAL_GAME_DESIGN.md](../../docs/MINIMAL_GAME_DESIGN.md)
- Editable deck: [minimal-cultural-selection-design.pptx](deck/minimal-cultural-selection-design.pptx)
- Canonical output: `outputs/2026-07-12-minimal-cultural-selection/`
