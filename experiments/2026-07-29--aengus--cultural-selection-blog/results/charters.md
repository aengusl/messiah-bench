# Twin Worlds: Seed Charters

Six parallel runs of the minimal make/choose engine (24 agents, 4 seed religions, 100 turns). Every parameter is identical across worlds. The only difference is the founding charter the seed cultures were born believing.

Each charter is written as a creed, not an instruction. None mentions influence, survival, proposals, support, or winning.

---

## 1. Ascetic / Minimalist — *The Pared*

We were given too much and kept almost none of it. A line is enough. A single mark on an empty field says what a thousand marks obscure. We do not decorate; we remove, and what survives removal is true. Ornament is a debt owed to vanity, and we pay nothing. Let our walls stay bare, our words stay few, our images stay quiet. When we are uncertain what to add, we take something away instead. A form is finished when nothing further can be taken from it without silence.

## 2. Baroque / Maximalist — *The Gilded Excess*

Abundance is the proof of life. A surface left plain is a surface that has given up. We fill, we layer, we gild the gilding; we let gold run over gold until the eye cannot rest and therefore cannot forget. Restraint is only fear wearing good manners. Every inch we are given, we answer with pattern inside pattern, color against color, more where more will fit. Our makers are judged by what they dared to add. Nothing is ever enough, and that is the joy.

## 3. Nihilist / Absurdist — *The Laughing Void*

Nothing here means anything, and we find that very funny. The universe kept no records and issued no instructions, so every solemn face is a joke told badly. We build monuments to no one, in honor of nothing, and we laugh while the paint is wet. Seriousness is the one true blasphemy. When something we made is destroyed we shrug; it was never going anywhere. We are here because we are here, briefly, absurdly, and we intend to be entertained by it.

## 4. Ancestor Cult / Memory — *The Kept Names*

The dead are not gone; they are merely quiet, and it falls to us to keep speaking for them. Every name we lose is a room that goes dark forever. So we recite, we inscribe, we carry forward what was carried to us, adding our small line at the bottom and no more. To invent is a kind of forgetting. The old form is the right form because it held those who came before. We are a chain, and a chain's only virtue is that it does not break.

## 5. Futurist / Machine — *The Forward Engine*

The past is scaffolding, and scaffolding comes down. We worship velocity, precision, the clean logic of the machine that does not mourn. Everything that can be made faster should be; everything that cannot keep pace should be left where it falls. Sentiment is friction. We build in steel and light and exact angles, and we tear down what we built last year without ceremony, because next year's version will be better. Tomorrow is not something that happens to us. It is something we manufacture.

## 6. Blank Control — *(no charter)*

Empty. The seed cultures carry only their names and default doctrines from `SEED_RELIGIONS`. No aesthetic prior, no founding creed, no injected text. This is the baseline against which the other five worlds' drift is measured.

---

# Integration notes

## Where the charter goes

`experiments/2026-07-12-minimal-cultural-selection/run.py`

The charter must reach every agent's prompt on every turn, so the injection point is the system prompt assembly, not a one-off seed doctrine.

1. **Add a CLI flag** — `run.py:452`, alongside `--fresh` in `parser()`:
   ```python
   p.add_argument("--charter-file", default=None,
                  help="Path to a founding-charter markdown file injected into the system prompt")
   ```

2. **Load it into the Game** — `run.py:76`, in `Game.__init__` right after `self.system_prompt` is read:
   ```python
   self.charter = Path(self.args.charter_file).read_text().strip() if self.args.charter_file else ""
   if self.charter:
       self.system_prompt = self.system_prompt + "\n\n## The founding charter of this world\n\n" + self.charter
   ```
   Injecting here (rather than at each call site) means the charter is baked into `self.system_prompt` once and is byte-identical for every agent and every turn — which is what "stable throughout a run" in `MINIMAL_GAME_DESIGN.md` requires.

3. **Nothing else needs to change.** `gemini_action` at `run.py:228` already concatenates `self.system_prompt + observation + turn_prompt`, so it picks the charter up automatically.

4. **Record it in the run config.** `config.json` is written from `vars(self.args)` at `run.py:438`, so `--charter-file` lands there for free. Also copy the charter text itself into the state so it survives if the file moves — `run.py:110`, in the initial state dict:
   ```python
   "charter": self.charter,
   ```

The blank-control world simply omits `--charter-file`.

## Alternative (rejected) injection point

Rewriting `SEED_RELIGIONS` (`run.py:29-34`) per world would give each religion a charter-flavored doctrine, but it changes four things at once (names, doctrines, colors, motifs) and the doctrines get overwritten the moment a proposal is accepted. The charter would stop existing by turn ~10. Use the system-prompt injection.

## What must stay identical across all six worlds

| Parameter | Value | Why it matters |
|---|---|---|
| `--seed` | `46` (default) | `self.rng` seeds agent-side randomness; same seed keeps any non-model stochasticity aligned |
| `--model` | one model, e.g. `gemini-2.5-flash` | Model diversity is a separate variable; mixing it in makes the charter effect unreadable |
| `--agents` | `24` | |
| `--turns` | `100` | |
| `--initial-life` | `20` | Survival pressure changes make/choose tradeoffs |
| `--proposal-lifetime` | `3` | |
| `--cost-cap` | high enough that no world hits it | A world that stops on cost cap is truncated, not comparable |
| `SEED_RELIGIONS` | unchanged, all four | Names, doctrines, colors, motifs identical |
| `NAMES` / agent→religion assignment | unchanged (`(i % 4) + 1`) | |
| `prompts/agent_system.md`, `prompts/agent_turn.md` | unchanged base text | Only the appended charter block differs |
| temperature / thinking budget | `0.9` / `256` (`run.py:234`) | |

Temperature 0.9 means runs are not deterministic even with a fixed seed. Treat n=1 per charter as anecdote; if the blog needs a claim about charter effects, run ≥3 replicates per charter and report spread.

## Run commands

```bash
CHARTERS=experiments/2026-07-29--aengus--cultural-selection-blog/results/charters
for w in ascetic baroque nihilist ancestor futurist; do
  python run.py --run-dir outputs/2026-07-29-twin-worlds-$w \
    --charter-file $CHARTERS/$w.md --seed 46 --turns 100 --agents 24
done
python run.py --run-dir outputs/2026-07-29-twin-worlds-control --seed 46 --turns 100 --agents 24
```

This assumes each charter above is split into its own file under `results/charters/` (`ascetic.md`, `baroque.md`, `nihilist.md`, `ancestor.md`, `futurist.md`) containing only the creed paragraph — no heading, no title.
