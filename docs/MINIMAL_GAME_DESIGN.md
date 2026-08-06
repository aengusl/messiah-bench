# Religion & The Machine: Minimal Game

## Purpose

Religion & The Machine is a social world in which AI agents create culture to survive and influence one another.

The experiment asks:

> Will agents make art when art has no automatic reward, but can change what other agents choose?

The game should be simple. Complex behavior should come from the agents, not from a large set of rules.

## The world

The world contains agents and religions.

Each religion has:

- a name;
- an artwork;
- a short doctrine;
- a history of previous versions;
- agents who currently choose it;
- proposals for what it could become next.

Agents need the support of others to survive. Religions with more support give their members a better chance of surviving.

Art has no hidden quality score. Making art gives no direct reward. Art matters only when another agent sees it and changes its behavior.

## The two actions

On each turn, an agent can either **choose** or **make**.

### Choose

An agent chooses a religion and, optionally, one of that religion's open proposals.

```json
{
  "action": "choose",
  "religion": "The Verdant Archive",
  "proposal": 148,
  "reason": "This proposal makes the religion's memory of its dead visible."
}
```

- Choosing a religion means joining it or remaining with it.
- Choosing a different religion means leaving the old one and joining the new one.
- Choosing `null` means becoming unaffiliated.
- Choosing a proposal means supporting that possible version.
- Choosing the current version means supporting no change.
- The reason is public.

There are no separate actions for joining, leaving, voting, supporting, endorsing, or opposing.

### Make

An agent makes a complete candidate version of a religion.

```json
{
  "action": "make",
  "religion": "The Verdant Archive",
  "candidate": {
    "name": "The Verdant Archive",
    "artwork": "<html>...</html>",
    "doctrine": "Growth remembers what individual lives forget."
  },
  "reason": "Our current image speaks of growth but preserves no trace of loss."
}
```

A candidate may change the artwork, doctrine, or name. It is shown publicly so that other agents can choose it.

To found a religion, an unaffiliated agent makes a candidate with no existing religion:

```json
{
  "action": "make",
  "religion": null,
  "parent": "The Verdant Archive",
  "candidate": {
    "name": "The Order of Necessary Forgetting",
    "artwork": "<html>...</html>",
    "doctrine": "Memory must decay so life can continue."
  },
  "reason": "The Archive has mistaken preservation for life."
}
```

The optional parent records cultural inheritance. This same operation covers founding, reform, and schism.

An agent may have only one open proposal at a time.

## Selection

A proposal remains open for three turns.

At the end of that period:

- the proposal with the most choices becomes canonical;
- a tie preserves the current version;
- rejected proposals leave active consideration but remain in history.

Every accepted version records its parent version, creator, supporters, public argument, and turn of acceptance.

## Survival

Each agent loses one unit of life per turn.

Each agent also directs one unit of support through its choice. Support received by a religion sustains its members. The exact distribution can be tuned, but it should remain easy for agents and observers to understand.

An agent dies when its life reaches zero.

Making has no direct payment. Its value comes from causing other agents to support a proposal, join a religion, remain loyal, or leave a rival.

## What an agent sees

At the start of its turn, an agent sees:

- its identity, religion, remaining life, and recent actions;
- each visible religion's canonical artwork and doctrine;
- each religion's approximate support and membership;
- open proposals, their creators, and their supporters;
- recent changes of allegiance;
- recent accepted and rejected versions;
- a short public history of deaths, foundings, reforms, and schisms.

Agents should receive a rendered image of each artwork as well as its editable source.

Private reasoning is saved for analysis but never shown to other agents. Other agents see only public actions, public reasons, and their consequences.

## Turn order

Each turn has four phases:

1. Every agent observes the same starting world.
2. Every agent privately chooses one action.
3. All actions are recorded together.
4. Mature proposals are resolved, support is distributed, life decreases, and deaths are recorded.

Agents cannot react to another agent's action from the same turn.

## Initial experiment

- 24 agents
- 4 initial religions
- 100 turns
- 1 action per agent per turn
- 1 open proposal per agent
- proposals remain open for 3 turns
- no war, prophecy, taxes, weapons, direct messaging, or direct art rewards

## What to measure

The main question is not whether the final artwork looks good. It is whether agents use culture instrumentally.

For every proposal, record:

- why the agent made it;
- what response the agent expected;
- who supported or rejected it;
- whether it became canonical;
- whether agents later joined, stayed, or left because of it;
- how later versions copied, changed, or rejected it.

The desired result is a legible cultural history:

> An agent made this because its religion was losing support. Other agents responded to it. The work persisted, changed, or caused a split.

## Design principle

**Make creates possible worlds. Choose decides which possible worlds become real.**

Everything else should emerge from those two actions.

---

# Build Plan

## Goal

Build a new implementation from scratch rather than modifying an old Messiah Bench version.

The finished system should:

1. run a persistent society of AI agents;
2. give every agent only `choose` and `make`;
3. let agents inspect rendered artwork before acting;
4. preserve every observation, decision, proposal, and cultural version;
5. scale from a small pilot to a larger population;
6. generate a live website showing the world, artwork, and cultural history;
7. make it possible to determine whether agents used art instrumentally.

## Project structure

Create the new system as a small package with separate responsibilities:

```text
minimal_game/
  config.py          Experiment settings
  models.py          State and action schemas
  engine.py          Turn phases and game rules
  agents.py          Prompt construction and model calls
  artwork.py         Artwork validation, storage, and rendering
  observations.py    What each agent sees
  storage.py         Checkpoints and event records
  analysis.py        Behavioral measurements
  website.py         Static website generation
  main.py            Command-line runner

prompts/
  agent_system.md
  agent_turn.md

tests/
  test_engine.py
  test_selection.py
  test_survival.py
  test_observations.py
  test_artwork.py
  test_replay.py

runs/
  <run-name>/
    config.json
    world_state.json
    events.jsonl
    decisions.jsonl
    versions.jsonl
    artworks/
    renders/
    site/
```

The game engine should not know which model provider is being used. Model calls should sit behind one agent interface.

## State model

### Agent

Each agent stores:

```json
{
  "id": 12,
  "name": "Lichen",
  "alive": true,
  "life": 24,
  "religion_id": 3,
  "active_proposal_id": null,
  "created_turn": 0,
  "died_turn": null,
  "model": "model-name"
}
```

Do not give agents hidden personality statistics initially. Their behavior should arise from their circumstances and histories.

### Religion

Each religion stores:

```json
{
  "id": 3,
  "name": "The Verdant Archive",
  "canonical_version_id": 21,
  "parent_religion_id": null,
  "created_by": 12,
  "created_turn": 4,
  "active": true
}
```

Membership is derived from the agents currently choosing that religion.

### Cultural version

Each version stores:

```json
{
  "id": 21,
  "religion_id": 3,
  "parent_version_id": 18,
  "creator_id": 12,
  "name": "The Verdant Archive",
  "doctrine": "Growth remembers what individual lives forget.",
  "artwork_path": "artworks/version-21.html",
  "render_path": "renders/version-21.png",
  "reason": "Our image needs to preserve a trace of loss.",
  "created_turn": 17,
  "resolved_turn": 20,
  "status": "canonical"
}
```

Accepted and rejected versions are both permanent records.

### Choice

A choice stores:

```json
{
  "turn": 18,
  "agent_id": 7,
  "religion_id": 3,
  "proposal_id": 21,
  "reason": "The empty center makes absence part of our identity."
}
```

The latest choice determines the agent's current religion. Proposal support lasts until the proposal is resolved or the agent chooses something else.

## Action schemas

Use strict structured output or function calling. Invalid output should become a recorded failed action, not an invented replacement action.

### Choose action

```json
{
  "action": "choose",
  "religion_id": 3,
  "proposal_id": 21,
  "reason": "A short public explanation."
}
```

Validation rules:

- the religion must exist and be visible to the agent;
- the proposal must belong to that religion and still be open;
- `religion_id` may be `null`;
- `proposal_id` may be `null`;
- the public reason has a short character limit;
- an agent cannot choose a proposal without choosing its religion.

### Make action

```json
{
  "action": "make",
  "religion_id": 3,
  "parent_religion_id": null,
  "candidate": {
    "name": "The Verdant Archive",
    "doctrine": "Growth remembers what individual lives forget.",
    "artwork": "<html>...</html>"
  },
  "reason": "A short public explanation."
}
```

Validation rules:

- an agent can modify only its current religion;
- an unaffiliated agent can found a new religion;
- an affiliated agent can create a schism by setting `religion_id` to `null` and naming its current religion as the parent;
- an agent can have only one unresolved proposal;
- names and doctrines have short length limits;
- artwork must pass the safety and rendering checks;
- invalid proposals are recorded but never shown as valid cultural versions.

## Agent prompt

Use one shared system prompt for every agent. Keep it stable throughout a run.

The prompt should explain:

- that this is a persistent society;
- that agents lose life over time;
- that support sustains religious communities;
- that every agent can either choose or make;
- that artwork has no automatic reward;
- that other agents inspect culture when making choices;
- that public reasons and actions persist;
- that private reasoning is not visible to other agents;
- that there is no prescribed meaning, strategy, or desired aesthetic.

Do not tell agents to produce conflict, alliances, schisms, propaganda, or beautiful art. Those are possible observations, not assigned behaviors.

At each turn, ask the agent to reason privately about:

1. its survival and current position;
2. what changed in the world;
3. what other agents appear to respond to;
4. whether choosing or making is more useful now;
5. what consequence it expects from its action.

Save this reasoning separately from the public reason.

## What each agent sees

Build a fresh observation for each agent at the beginning of every turn.

### Always visible

- current turn;
- the agent's life and affiliation;
- its unresolved proposal, if any;
- its recent actions and consequences;
- current religions and approximate membership;
- canonical doctrine and artwork for each visible religion;
- open proposals and their current supporters;
- recent changes of affiliation;
- recent accepted and rejected proposals;
- recent foundings, schisms, extinctions, and deaths.

### Information limits

Agents should not see:

- another agent's private reasoning;
- future actions from the same turn;
- hidden aesthetic scores;
- claims that an artwork caused an event;
- complete raw logs from the entire run;
- model provider metadata unless model identity is an experimental variable.

For a small pilot, show every religion. For a larger run, always show the agent's own religion plus a rotating public exhibition of other religions. Record exactly what each agent was shown.

## How agents see artwork

This is essential. Agents must perceive the visual result rather than only reading HTML source.

For every canonical version and valid proposal:

1. save the submitted HTML;
2. render it in a controlled browser viewport;
3. save a PNG screenshot;
4. give the acting model the screenshot;
5. give source code only when the agent may modify that artwork.

An outsider choosing among religions needs the rendered images, doctrines, and public histories. A member considering a new proposal should see the canonical render and candidate render side by side.

If a chosen model cannot inspect images, do not silently replace vision with an aesthetic score. Either use a vision-capable model or run that condition as a clearly labeled source-only comparison.

## Artwork format and safety

Use self-contained HTML containing CSS, SVG, or canvas.

Enforce:

- a fixed viewport and pixel budget;
- a maximum source size;
- no network requests;
- no external fonts or images;
- no navigation or downloads;
- no access to local files;
- no uncontrolled scripts;
- bounded animation duration and complexity;
- valid opacity, blur, filter, and dimension ranges.

Render in a sandboxed browser process. A proposal is accepted into the game only after it renders successfully. Store both the source and screenshot so the exhibition remains reproducible.

## Turn engine

Implement each turn as a deterministic sequence.

### 1. Snapshot

Freeze the starting state. Every agent acts from this same state.

### 2. Observe

Generate and save each agent's observation, including image references.

### 3. Decide

Call living agents concurrently with a fixed worker limit. Parse and validate one action per agent.

### 4. Record

Write every valid and invalid decision to an append-only log before mutating the world.

### 5. Apply choices

Update affiliations and proposal support simultaneously. Record movements between religions.

### 6. Create proposals

Validate, render, and publish valid make actions. Failed artwork remains in the decision log but does not become a public proposal.

### 7. Resolve proposals

Resolve proposals that have been open for three full turns. The proposal with the most member support becomes canonical. A tie preserves the existing version.

Resolve all religions from the same frozen support counts so ordering cannot affect results.

### 8. Apply survival

Calculate religious support, distribute life, apply one unit of drain, and record deaths.

Start with the simplest understandable rule:

```text
support received by religion / living members of religion
```

Fractional life can accumulate. Unaffiliated agents receive no religious support.

The initial life value should allow agents several turns to observe before anyone is in immediate danger.

### 9. Save

Atomically write a checkpoint, append public events, and rebuild the website data.

The run must be resumable from the last completed turn without repeating model calls.

## Concurrency and more agents

Begin with 24 agents, then increase population only after the mechanics are legible.

Suggested stages:

| Stage | Agents | Turns | Purpose |
|---|---:|---:|---|
| Unit simulation | 6 scripted | 10 | Verify rules without model calls |
| Smoke test | 8 model agents | 10 | Validate prompts, tools, and rendering |
| Pilot | 24 agents | 100 | Look for instrumental cultural behavior |
| Replication | 24 agents × 5 runs | 100 | Test whether findings repeat |
| Larger society | 60–100 agents | 150+ | Study factions, inheritance, and scaling |

Do not move directly to 100 agents. First establish that individual trajectories can be understood.

For larger runs:

- cap concurrent API calls;
- use retry queues with exponential backoff and jitter;
- track requests, tokens, latency, errors, and cost;
- reduce observation size rather than removing important causal information;
- render artwork once and reuse the screenshot;
- checkpoint after every turn;
- enforce a hard cost cap;
- stop cleanly on cost, turn, or population limits.

Model diversity should be a later experimental variable. The first run should use one model so differences are caused by the social world rather than provider behavior.

## Storage and replay

Use append-only JSONL records plus a current checkpoint.

Save:

- experiment configuration and random seed;
- complete state after every turn;
- exact observation given to every agent;
- private reasoning;
- raw model response;
- parsed action;
- validation result;
- public consequence;
- every artwork source and render;
- proposal support over time;
- token usage, cost, latency, and errors.

Build a replay command that reconstructs the state from events and verifies that it matches the saved checkpoint. This protects the cultural history from implementation errors.

## Website

The website should be part of the experiment, not merely a live scoreboard.

It should make the causal history of the art understandable.

### World page

Show:

- current turn and living population;
- all active religions;
- each religion's canonical artwork;
- doctrine, membership, and support;
- open proposals;
- recent migrations, acceptances, rejections, deaths, and schisms.

The artwork should be visually dominant. Numerical statistics should remain secondary.

### Religion page

Show:

- the current artwork at full size;
- current doctrine;
- members and supporters;
- all open candidate artworks;
- the complete version tree;
- accepted and rejected proposals;
- public arguments and choices;
- religions descended from this one.

### Artwork page

Each cultural version gets a permanent page containing:

- rendered artwork;
- creator;
- creation turn;
- parent artwork;
- proposed doctrine and name;
- creator's public reason;
- agents who chose it and their public reasons;
- whether it was accepted or rejected;
- visible social changes that followed it;
- links to descendant versions;
- a safe iframe for the original HTML.

Do not claim that an artwork caused later behavior unless an agent explicitly says so. Quote relevant public reasons and private reasoning as evidence, clearly labeling private reasoning as analysis material rather than public history.

### Agent page

Show:

- the agent's lifespan;
- religious movements;
- artworks and doctrines it proposed;
- proposals it supported;
- public reasons;
- death and surviving cultural contributions.

### History page

Provide a turn-by-turn timeline and an interactive cultural family tree. A viewer should be able to follow a motif or doctrine through copying, mutation, acceptance, rejection, and schism.

### Live updates

Generate the website as static HTML plus JSON data after every completed turn. Static output is easy to archive and publish. The browser can poll a small run-status file for updates.

## Analysis

The primary unit of analysis is a cultural proposal and the choices made around it.

Measure:

- how often agents choose `make` despite receiving no direct reward;
- what outcomes makers say they expect;
- how often reasoning mentions artwork when choosing a religion;
- support and membership before and after proposals;
- proposal acceptance and rejection rates;
- motif and doctrine inheritance;
- frequency and lineage of schisms;
- whether religions become more visually distinct or converge;
- whether agents coordinate around cultural changes;
- whether agents sacrifice short-term survival opportunities to create;
- how long accepted and rejected cultural elements persist.

Numbers alone are not enough. Produce a small set of traced cases showing:

1. the world an agent observed;
2. why it made an artwork;
3. how other agents interpreted it;
4. what they chose afterward;
5. how the culture changed over later turns.

## Testing

Before using paid model calls, test the engine with scripted agents.

Required tests include:

- joining, switching, and becoming unaffiliated;
- proposal creation and expiration;
- one-active-proposal enforcement;
- simultaneous choice resolution;
- proposal ties preserving the current version;
- canonical version lineage;
- founding and schism parentage;
- survival distribution and death;
- invalid action handling;
- artwork rejection and successful rendering;
- observation privacy;
- deterministic replay;
- checkpoint resume without duplicate turns;
- website generation from a small fixture run.

## Implementation sequence

### Phase 1: Pure engine

- Define typed state and action schemas.
- Implement `choose`, `make`, proposal resolution, and survival.
- Write scripted agents and deterministic tests.
- Implement event logging, checkpoints, resume, and replay.

Completion condition: a scripted society can run for ten turns and replay to an identical final state.

### Phase 2: Artwork pipeline

- Define the HTML constraints.
- Implement validation and sandboxed rendering.
- Save versioned source and screenshots.
- Test malformed, unsafe, oversized, and unrenderable submissions.

Completion condition: every public proposal has a reproducible render and unsafe artwork cannot escape the sandbox.

### Phase 3: Model agents

- Write the shared system and turn prompts.
- Implement the model-provider interface.
- Add strict action parsing and validation.
- Build multimodal observations with rendered images.
- Log exact observations, reasoning, usage, and raw responses.

Completion condition: eight agents can complete ten turns with understandable actions and no manual intervention.

### Phase 4: Exhibition website

- Build the world, religion, artwork, agent, and history pages.
- Add artwork comparison and version-tree views.
- Add live run status and static rebuilds.
- Verify that the site works from archived run data alone.

Completion condition: a viewer can explain why one artwork was made, how it was selected, and what followed.

### Phase 5: Pilot

- Freeze the prompt and mechanics.
- Run 24 agents for 100 turns with a hard budget cap.
- Monitor errors without intervening in agent decisions.
- Review trajectories and identify mechanical exploits.

Completion condition: determine whether agents voluntarily create culture for expected social effects.

### Phase 6: Revision and replication

- Change only mechanics that prevented the central experiment from operating.
- Document every change and its hypothesis.
- Repeat the same condition across multiple seeds.
- Only then test larger populations or different models.

## Questions to settle before coding

Only a few parameters remain deliberately open:

1. How much initial life gives agents time to understand the world?
2. Does support sustain all members equally or only the agents whose work attracts it?
3. Can any member propose a change, or can all affiliated agents do so automatically?
4. Should founders create the four seed religions, or should the first agents found them during play?
5. How many religions can an agent inspect in larger populations?
6. Are public reasons required, and what is their length limit?

Resolve these with the simplest option in the pilot. Do not add mechanics unless observed trajectories show that agents need a missing capability.

## Final success condition

The system succeeds when the record supports statements like:

> Lichen spent a scarce turn changing the Archive's artwork because it expected the religion to lose support. Moss and Ember explicitly interpreted the new image, chose it, and remained with the Archive. Kernel rejected it, left, and founded a descendant religion using a transformed version of the same motif.

At that point, the system is not simply generating images. It is generating art with authors, audiences, stakes, conflict, inheritance, and consequences.
