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
