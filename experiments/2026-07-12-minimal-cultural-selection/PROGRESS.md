# Minimal Cultural Selection — Progress

## Core design decision

The agent has two actions:

- `choose`: affiliate with a religion and optionally support an open proposal. This contributes one unit of support for the current turn.
- `make`: propose a complete candidate cultural version. This contributes no support for the current turn.

Each religion's current-turn support is divided equally among its living members. Every agent then loses one life. Making therefore has an immediate opportunity cost. Art is useful only if other agents respond by choosing the religion or proposal.

## Analysis questions

1. How often do agents make without direct payment?
2. What social effect do makers predict?
3. Do choosers explicitly refer to visual or doctrinal properties?
4. Which proposals become canonical, and what happens afterward?
5. Do motifs, doctrines, factions, and schisms emerge?

## Results

### Smoke A — stable-equilibrium failure

- 8 agents × 5 turns
- 40 valid actions, 0 invalid
- 40 choose, 0 make
- Cost: $0.0709

Agents recognized that choosing indefinitely held life constant. Culture had no competitive upside, so none was produced.

### Smoke B — cultural influence

- 8 agents × 5 turns
- 40 valid actions, 0 invalid
- 39 choose, 1 make
- Cost: $0.0834
- Ember voluntarily made a revised Open Circuit at turn 3.
- Axiom chose it on turns 4 and 5, giving Ember influence 2.

This passes the minimum behavioral gate: making remained costly and unpaid, but another agent's subsequent choices created the payoff.

## Final pilot

- 24 agents × 100 turns
- 2,400/2,400 valid actions
- 26 make; 2,374 choose
- 21 accepted proposals; 5 rejected
- 24 survivors; 4 surviving religions
- $7.3383 estimated pilot cost

Creation occurred between turns 6 and 54. The remainder of the run was consolidation. Successful authors continued receiving influence from repeated choices of canonical work, while no agent attempted a further cultural challenge.

The primary positive result is causal legibility: agents made because they expected others to choose their work, and others did. The primary negative result is visual and doctrinal convergence. Animation and incremental adaptation became a fashion shared across all four religions.
