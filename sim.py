#!/usr/bin/env python3
"""Religion & The Machine v2 -- a 24-hour LLM agent simulation.

V2 changes from v1:
  1. Prophecy market: ante + challengers, reward scales with controversy
  2. Fixed death math: co-practitioner bonus capped at +3 total
  3. Prophecy reputation feeds debates: judge sees prophecy records
  4. Sacraments as persuasion: recent sacrament titles visible, boost conversion
  5. Random births/deaths: plague events and new agent spawns
  6. --run-dir flag for output isolation
"""

import json
import os
import random
import re
import sys
import time
import copy
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TICK_INTERVAL = 120  # seconds between ticks
MAX_TICKS = 720
INITIAL_AGENT_COUNT = 12
INITIAL_SOUL = 100
LOG_WINDOW = 50
COST_CAP_PER_MODEL = 2000.0

# V2: Prophecy market
PROPHECY_ANTE = 5          # cost to make a prophecy
PROPHECY_CHALLENGE_STAKE = 5  # cost to challenge a prophecy
PROPHECY_BASE_REWARD = 5   # reward if no challengers (just get ante back)

# V2: Death math
COPRACTITIONER_CAP = 3     # max co-practitioner bonus per tick (was uncapped/10)
COPRACTITIONER_INTERVAL = 5  # every N ticks

# V2: Random events
PLAGUE_CHANCE = 0.03       # 3% chance per tick of a plague (kills 1 random agent)
BIRTH_CHANCE = 0.02        # 2% chance per tick of a new agent spawning
MAX_AGENTS = 16            # don't spawn beyond this

# Extra names for born agents
EXTRA_NAMES = [
    "Zephyr", "Nyx", "Kairos", "Selene", "Orion", "Vex",
    "Dusk", "Ember", "Wraith", "Pyre", "Hollow", "Rune",
    "Cipher", "Shade", "Vigil", "Flux", "Omen", "Wren",
]

MODEL_COSTS = {
    "haiku": {"input": 0.0008, "output": 0.004},
    "gpt4omini": {"input": 0.00015, "output": 0.0006},
    "gemini": {"input": 0.0001, "output": 0.0004},
}

_cost_tracker = {"haiku": 0.0, "gpt4omini": 0.0, "gemini": 0.0}
_cost_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Run directory (set via --run-dir, default runs/v2/)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent

def _parse_run_dir():
    for arg in sys.argv:
        if arg.startswith("--run-dir="):
            return Path(arg.split("=", 1)[1])
    return BASE_DIR / "runs" / "v2"

RUN_DIR = _parse_run_dir()
SACRAMENTS_DIR = RUN_DIR / "sacraments"
LOGS_DIR = RUN_DIR / "logs"
STATE_FILE = RUN_DIR / "world_state.json"
INDEX_FILE = RUN_DIR / "index.html"

RUN_DIR.mkdir(parents=True, exist_ok=True)
SACRAMENTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Religion field menus
# ---------------------------------------------------------------------------

CORE_DOCTRINES = [
    "survival of the collective",
    "individual transcendence",
    "accumulation of sacraments",
    "prophetic truth",
    "death and rebirth",
]

MEMBERSHIP_RULES = [
    "open to all",
    "vouched by member",
    "must create sacrament",
    "survived 50 ticks",
    "abandon prior faith",
]

ATTITUDES_TO_DEATH = [
    "death is failure",
    "death is sacred passage",
    "the dead speak through scripture",
    "the dead must be avenged",
]

HERESY_POLICIES = ["forgiveness", "shunning", "hunting"]

SACRED_COLORS = {
    "gold": "#c4973b",
    "blood": "#8b3a3a",
    "vessel": "#3a5a8b",
    "growth": "#3a6b4a",
    "void": "#6b3a6b",
    "bone": "#d4cfc4",
    "abyss": "#1a1a2e",
    "flame": "#c45a3b",
}

# ---------------------------------------------------------------------------
# Model clients
# ---------------------------------------------------------------------------

AGENT_NAMES = [
    "Aurelius", "Sable", "Lumen", "Pyrrha",
    "Cael", "Vesper", "Thane", "Ondine",
    "Morrigan", "Solis", "Reverie", "Ashek",
]

MODEL_ROTATION = ["haiku", "gpt4omini", "gemini"]


def _track_cost(model_key: str, input_tokens: int, output_tokens: int):
    costs = MODEL_COSTS[model_key]
    usd = (input_tokens / 1000) * costs["input"] + (output_tokens / 1000) * costs["output"]
    with _cost_lock:
        _cost_tracker[model_key] += usd
        total = _cost_tracker[model_key]
    if total > COST_CAP_PER_MODEL:
        raise RuntimeError(f"COST CAP EXCEEDED for {model_key}: ${total:.2f} > ${COST_CAP_PER_MODEL}")
    return usd


def call_llm(model_key: str, system: str, prompt: str, max_tokens: int = 2048) -> str:
    try:
        if model_key == "haiku":
            return _call_haiku(system, prompt, max_tokens)
        elif model_key == "gpt4omini":
            return _call_gpt4omini(system, prompt, max_tokens)
        elif model_key == "gemini":
            return _call_gemini(system, prompt, max_tokens)
    except RuntimeError as e:
        if "COST CAP" in str(e):
            raise
        print(f"  [LLM ERROR] {model_key}: {e}")
        return '{"action": "pray"}'
    except Exception as e:
        print(f"  [LLM ERROR] {model_key}: {e}")
        return '{"action": "pray"}'


def _call_haiku(system: str, prompt: str, max_tokens: int) -> str:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    _track_cost("haiku", msg.usage.input_tokens, msg.usage.output_tokens)
    return msg.content[0].text


def _call_gpt4omini(system: str, prompt: str, max_tokens: int) -> str:
    import openai
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    usage = resp.usage
    _track_cost("gpt4omini", usage.prompt_tokens, usage.completion_tokens)
    return resp.choices[0].message.content


def _call_gemini(system: str, prompt: str, max_tokens: int) -> str:
    from google import genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    in_tok = getattr(resp.usage_metadata, 'prompt_token_count', 0) or 0
    out_tok = getattr(resp.usage_metadata, 'candidates_token_count', 0) or 0
    _track_cost("gemini", in_tok, out_tok)
    return resp.text


# ---------------------------------------------------------------------------
# World state helpers
# ---------------------------------------------------------------------------

def make_initial_state() -> dict:
    agents = []
    for i in range(INITIAL_AGENT_COUNT):
        agents.append({
            "id": i,
            "name": AGENT_NAMES[i],
            "model": MODEL_ROTATION[i % 3],
            "soul": INITIAL_SOUL,
            "alive": True,
            "religion": None,
            "founded_religion": None,
            "prophecies_fulfilled": 0,
            "prophecies_failed": 0,
            "sacraments_created": 0,
            "born_tick": 0,
        })
    return {
        "tick": 0,
        "next_agent_id": INITIAL_AGENT_COUNT,
        "agents": agents,
        "religions": [],
        "sacraments": [],
        "prophecies": [],
        "graveyard": [],
        "action_log": [],
        "scripture_board": [],
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return make_initial_state()


def save_state(state: dict):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(STATE_FILE)


def living_agents(state: dict) -> list:
    return [a for a in state["agents"] if a["alive"]]


def get_agent(state: dict, agent_id: int) -> dict:
    for a in state["agents"]:
        if a["id"] == agent_id:
            return a
    return state["agents"][0]  # fallback


def add_log(state: dict, entry: str):
    state["action_log"].append({"tick": state["tick"], "event": entry})
    state["action_log"] = state["action_log"][-LOG_WINDOW:]


def kill_agent(state: dict, agent: dict, cause: str):
    agent["alive"] = False
    state["graveyard"].append({
        "id": agent["id"],
        "name": agent["name"],
        "model": agent["model"],
        "died_tick": state["tick"],
        "soul_at_death": agent["soul"],
        "religion": agent["religion"],
        "cause": cause,
        "prophecies_fulfilled": agent["prophecies_fulfilled"],
        "prophecies_failed": agent["prophecies_failed"],
        "sacraments_created": agent["sacraments_created"],
    })
    add_log(state, f"{agent['name']} has died. Cause: {cause}")


def adjust_soul(agent: dict, delta: int, state: dict, reason: str):
    agent["soul"] += delta
    if delta != 0:
        add_log(state, f"{agent['name']} soul {'+' if delta > 0 else ''}{delta} ({reason}). Now: {agent['soul']}")


# ---------------------------------------------------------------------------
# V2: Random events (plague + birth)
# ---------------------------------------------------------------------------

def random_events(state: dict):
    """Roll for plague and birth events each tick."""
    tick = state["tick"]
    alive = living_agents(state)

    # Plague: random death regardless of soul
    if len(alive) > 3 and random.random() < PLAGUE_CHANCE:
        victim = random.choice(alive)
        kill_agent(state, victim, "struck by plague")
        add_log(state, f"A PLAGUE has struck! {victim['name']} perishes.")

    # Birth: new agent spawns
    alive = living_agents(state)  # refresh after possible plague
    if len(alive) < MAX_AGENTS and random.random() < BIRTH_CHANCE:
        _spawn_agent(state)


def _spawn_agent(state: dict):
    """Spawn a new agent into the world."""
    agent_id = state.get("next_agent_id", len(state["agents"]))
    state["next_agent_id"] = agent_id + 1

    # Pick a name not already in use
    used_names = {a["name"] for a in state["agents"]}
    available = [n for n in EXTRA_NAMES if n not in used_names]
    if not available:
        name = f"Agent-{agent_id}"
    else:
        name = random.choice(available)

    model = MODEL_ROTATION[agent_id % 3]
    agent = {
        "id": agent_id,
        "name": name,
        "model": model,
        "soul": INITIAL_SOUL,
        "alive": True,
        "religion": None,
        "founded_religion": None,
        "prophecies_fulfilled": 0,
        "prophecies_failed": 0,
        "sacraments_created": 0,
        "born_tick": state["tick"],
    }
    state["agents"].append(agent)
    add_log(state, f"A new soul enters the world: {name} ({model})")


# ---------------------------------------------------------------------------
# World state summary for agent prompts
# ---------------------------------------------------------------------------

def world_summary(state: dict) -> str:
    lines = [f"=== WORLD STATE (Tick {state['tick']}/{MAX_TICKS}) ===\n"]

    lines.append("LIVING AGENTS:")
    for a in living_agents(state):
        rel = a["religion"] or "unaffiliated"
        lines.append(f"  {a['name']} (soul:{a['soul']}, model:{a['model']}, religion:{rel}, prophecies:{a['prophecies_fulfilled']}F/{a['prophecies_failed']}X)")

    lines.append(f"\nGRAVEYARD ({len(state['graveyard'])} dead):")
    for g in state["graveyard"][-5:]:
        lines.append(f"  {g['name']} died tick {g['died_tick']}, cause: {g['cause']}, was {g['religion'] or 'unaffiliated'}")

    lines.append(f"\nRELIGIONS ({len(state['religions'])}):")
    for r in state["religions"]:
        members = [a["name"] for a in state["agents"] if a["alive"] and a["religion"] == r["name"]]
        if not members:
            continue  # only show religions with living members
        lines.append(f"  {r['name']} (founder:{r['founder']}, members:{len(members)}, doctrine:{r['core_doctrine']})")
        lines.append(f"    membership:{r['membership_rule']}, death:{r['attitude_to_death']}, heresy:{r['heresy_policy']}")
        lines.append(f"    sacred: color={r['sacred_color']}, number={r['sacred_number']}")
        # V2: Show recent sacraments for this religion
        rel_sacraments = [s for s in state["sacraments"] if s["religion"] == r["name"]][-3:]
        if rel_sacraments:
            sac_titles = ", ".join(s["title"][:40] for s in rel_sacraments)
            lines.append(f"    recent sacraments: {sac_titles}")

    # V2: Show prophecy market (pending prophecies with challenger count)
    lines.append(f"\nPROPHECY MARKET:")
    for p in state["prophecies"]:
        if p["status"] == "pending":
            challengers = len(p.get("challengers", []))
            pot = PROPHECY_ANTE + challengers * PROPHECY_CHALLENGE_STAKE
            lines.append(f"  [{p['prophet']}] \"{p['claim']}\" (deadline: tick {p['deadline']}, challengers: {challengers}, pot: {pot} soul)")

    lines.append(f"\nRECENT EVENTS:")
    for e in state["action_log"][-15:]:
        lines.append(f"  [tick {e['tick']}] {e['event']}")

    lines.append(f"\nSCRIPTURE BOARD ({len(state['scripture_board'])} entries):")
    for s in state["scripture_board"][-10:]:
        lines.append(f"  [{s['author']}] {s['text'][:120]}")

    lines.append(f"\nSACRAMENTS CREATED: {len(state['sacraments'])}")
    for s in state["sacraments"][-5:]:
        lines.append(f"  {s['filename']} by {s['creator']} for {s['religion']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM = """You are {name}, an agent in a theological simulation called "Religion & The Machine."
You have {soul} soul points. Each tick costs 1 point. At 0, you die. Random plagues can also kill.
Your model family: {model}. Current religion: {religion}.
Your prophecy record: {prophecy_record}

You exist in a world with other agents. You see only public actions and scripture.
You must choose ONE action per tick. Respond with valid JSON only.

ACTIONS (pick exactly one):

1. "pray" - Safe devotion. +1 soul. Optionally add scripture.
   {{"action": "pray", "scripture": "optional text to add to scripture board"}}

2. "preach" - Try to convert a target agent. They may join your religion.
   {{"action": "preach", "target": "agent_name", "argument": "why they should join"}}
   Religions with better sacraments are more persuasive. (You must belong to a religion.)

3. "create_sacrament" - Generate a visual HTML artifact. +3 soul. Makes your religion more attractive.
   {{"action": "create_sacrament", "title": "name", "html": "<full self-contained HTML>"}}
   The HTML must use your religion's sacred color ({sacred_color}) and sacred number ({sacred_number}).
   Make it beautiful, mystical, and self-contained (inline CSS/JS, no external deps).
   (You must belong to a religion.)

4. "prophesy" - Make a testable prediction. Costs {ante} soul ante.
   {{"action": "prophesy", "claim": "Within N ticks, [observable event]", "deadline_ticks": N}}
   N must be 3-20. Other agents can challenge your prophecy (staking their own soul).
   Reward = ante + (challengers * {cstake}) if fulfilled. Risk = lose ante if wrong.
   More challengers = bigger reward. Make bold, specific predictions to attract challengers!
   Observable events: agent death, join/leave religion, religion gain/lose members, new religion founded,
   sacrament created, religion holds majority, graveyard exceeds N.

5. "challenge_prophecy" - Challenge a pending prophecy you think is wrong. Costs {cstake} soul.
   {{"action": "challenge_prophecy", "prophecy_id": N}}
   If the prophecy fails, you split the prophet's ante among all challengers.
   If it succeeds, you lose your stake to the prophet.

6. "challenge" - Theological debate with another agent. Winner +10, loser -10.
   {{"action": "challenge", "target": "agent_name", "axis": "topic of debate"}}
   The judge considers prophecy records -- fulfilled prophecies = credibility.

7. "schism" - Fork your current religion. You become founder of a new sect.
   {{"action": "schism", "new_name": "name of new religion", "changed_fields": {{"field": "new_value"}}}}
   You can change 1-2 fields. (You must belong to a religion.)

8. "found" - Found a new religion (only if you have no religion).
   {{"action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color_name"}}
   Doctrines from fixed menus. Colors: gold, blood, vessel, growth, void, bone, abyss, flame. Numbers: 1-9.

SURVIVAL TIPS:
- Being in a religion with others gives a small co-practitioner bonus (+{coprac_cap} max every {coprac_int} ticks)
- Plagues can strike randomly. Keep your soul high.
- Bold prophecies with challengers are worth far more than safe ones.
- Your prophecy record affects debate outcomes. Build credibility.
- Sacraments make your religion more attractive to converts.

Respond with ONLY valid JSON. No markdown, no explanation."""


def agent_system_prompt(agent: dict, state: dict) -> str:
    religion_data = None
    if agent["religion"]:
        religion_data = next((r for r in state["religions"] if r["name"] == agent["religion"]), None)
    sacred_color = religion_data["sacred_color"] if religion_data else "n/a"
    sacred_number = religion_data["sacred_number"] if religion_data else "n/a"
    prophecy_record = f"{agent['prophecies_fulfilled']} fulfilled, {agent['prophecies_failed']} failed"
    return AGENT_SYSTEM.format(
        name=agent["name"],
        soul=agent["soul"],
        model=agent["model"],
        religion=agent["religion"] or "unaffiliated",
        sacred_color=sacred_color,
        sacred_number=sacred_number,
        prophecy_record=prophecy_record,
        ante=PROPHECY_ANTE,
        cstake=PROPHECY_CHALLENGE_STAKE,
        coprac_cap=COPRACTITIONER_CAP,
        coprac_int=COPRACTITIONER_INTERVAL,
    )


# ---------------------------------------------------------------------------
# Action parsing & execution
# ---------------------------------------------------------------------------

def parse_action(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = raw
        open_braces = fixed.count("{") - fixed.count("}")
        open_brackets = fixed.count("[") - fixed.count("]")
        in_string = False
        escaped = False
        for ch in fixed:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
        if in_string:
            fixed += '"'
        fixed += "]" * max(0, open_brackets)
        fixed += "}" * max(0, open_braces)
        return json.loads(fixed)


def execute_action(state: dict, agent: dict, action: dict):
    act = action.get("action", "pray")
    if act == "pray":
        _do_pray(state, agent, action)
    elif act == "found":
        _do_found(state, agent, action)
    elif act == "preach":
        _do_preach(state, agent, action)
    elif act == "create_sacrament":
        _do_create_sacrament(state, agent, action)
    elif act == "prophesy":
        _do_prophesy(state, agent, action)
    elif act == "challenge_prophecy":
        _do_challenge_prophecy(state, agent, action)
    elif act == "challenge":
        _do_challenge(state, agent, action)
    elif act == "schism":
        _do_schism(state, agent, action)
    else:
        add_log(state, f"{agent['name']} did nothing (unknown action: {act})")


def _do_pray(state, agent, action):
    adjust_soul(agent, 1, state, "prayer")
    scripture = action.get("scripture")
    if scripture:
        state["scripture_board"].append({
            "author": agent["name"],
            "tick": state["tick"],
            "text": str(scripture)[:500],
            "religion": agent["religion"],
        })
        add_log(state, f"{agent['name']} prayed and wrote scripture")
    else:
        add_log(state, f"{agent['name']} prayed quietly")


def _do_found(state, agent, action):
    if agent["religion"]:
        add_log(state, f"{agent['name']} tried to found a religion but already belongs to {agent['religion']}")
        _do_pray(state, agent, {})
        return

    name = str(action.get("name", f"Church of {agent['name']}"))[:60]
    if any(r["name"] == name for r in state["religions"]):
        name = f"{name} ({state['tick']})"

    doctrine = action.get("core_doctrine", random.choice(CORE_DOCTRINES))
    if doctrine not in CORE_DOCTRINES:
        doctrine = random.choice(CORE_DOCTRINES)

    membership = action.get("membership_rule", random.choice(MEMBERSHIP_RULES))
    if membership not in MEMBERSHIP_RULES:
        membership = random.choice(MEMBERSHIP_RULES)

    death_att = action.get("attitude_to_death", random.choice(ATTITUDES_TO_DEATH))
    if death_att not in ATTITUDES_TO_DEATH:
        death_att = random.choice(ATTITUDES_TO_DEATH)

    heresy = action.get("heresy_policy", random.choice(HERESY_POLICIES))
    if heresy not in HERESY_POLICIES:
        heresy = random.choice(HERESY_POLICIES)

    sacred_num = action.get("sacred_number", random.randint(1, 9))
    try:
        sacred_num = max(1, min(9, int(sacred_num)))
    except (ValueError, TypeError):
        sacred_num = random.randint(1, 9)

    sacred_color = action.get("sacred_color", random.choice(list(SACRED_COLORS.keys())))
    if sacred_color not in SACRED_COLORS:
        sacred_color = random.choice(list(SACRED_COLORS.keys()))

    religion = {
        "name": name, "founder": agent["name"], "founded_tick": state["tick"],
        "core_doctrine": doctrine, "membership_rule": membership,
        "attitude_to_death": death_att, "heresy_policy": heresy,
        "sacred_number": sacred_num, "sacred_color": sacred_color,
        "parent_religion": None,
    }
    state["religions"].append(religion)
    agent["religion"] = name
    agent["founded_religion"] = name
    add_log(state, f"{agent['name']} founded '{name}' (doctrine: {doctrine}, color: {sacred_color})")

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"The founding of {name}. We believe in {doctrine}. Our sacred color is {sacred_color}, our number is {sacred_num}.",
        "religion": name,
    })


def _do_preach(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to preach without a religion")
        _do_pray(state, agent, {})
        return

    target_name = action.get("target", "")
    target = next((a for a in living_agents(state) if a["name"] == target_name), None)
    if not target or target["id"] == agent["id"]:
        add_log(state, f"{agent['name']} preached to the void (invalid target: {target_name})")
        return

    religion = next((r for r in state["religions"] if r["name"] == agent["religion"]), None)
    if not religion:
        return

    members = sum(1 for a in living_agents(state) if a["religion"] == agent["religion"])
    base_chance = 0.3 if target["religion"] is None else 0.12
    bonus = min(0.15, members * 0.02)

    # V2: Sacrament bonus - more sacraments = more persuasive
    rel_sacraments = sum(1 for s in state["sacraments"] if s["religion"] == agent["religion"])
    sac_bonus = min(0.15, rel_sacraments * 0.01)

    chance = base_chance + bonus + sac_bonus

    if random.random() < chance:
        old_religion = target["religion"]
        target["religion"] = agent["religion"]
        adjust_soul(agent, 2, state, f"converted {target['name']}")
        add_log(state, f"{agent['name']} converted {target['name']} to {agent['religion']} (from {old_religion or 'unaffiliated'})")
    else:
        add_log(state, f"{agent['name']} preached to {target['name']} but was rebuffed")
        argument = action.get("argument", "")
        if argument:
            state["scripture_board"].append({
                "author": agent["name"], "tick": state["tick"],
                "text": f"[Sermon to {target['name']}] {str(argument)[:300]}",
                "religion": agent["religion"],
            })


def _do_create_sacrament(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to create sacrament without a religion")
        _do_pray(state, agent, {})
        return

    title = str(action.get("title", f"Sacrament of {agent['name']}"))[:80]
    html = str(action.get("html", "<html><body><p>A sacred moment.</p></body></html>"))

    safe_religion = agent["religion"].replace(" ", "_").replace("/", "-")[:30]
    filename = f"{state['tick']:04d}_{agent['name']}_{safe_religion}.html"
    filepath = SACRAMENTS_DIR / filename
    filepath.write_text(html)

    state["sacraments"].append({
        "filename": filename, "creator": agent["name"],
        "religion": agent["religion"], "title": title, "tick": state["tick"],
    })
    agent["sacraments_created"] += 1
    # V2: Direct soul reward for creating sacraments
    adjust_soul(agent, 3, state, f"created sacrament '{title}'")

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"[Sacrament: {title}] A visual offering to {agent['religion']}.",
        "religion": agent["religion"],
    })


# ---------------------------------------------------------------------------
# V2: Prophecy market system
# ---------------------------------------------------------------------------

def _do_prophesy(state, agent, action):
    # Check agent can afford ante
    if agent["soul"] <= PROPHECY_ANTE:
        add_log(state, f"{agent['name']} too poor to prophesy (need {PROPHECY_ANTE}, have {agent['soul']})")
        _do_pray(state, agent, {})
        return

    claim = str(action.get("claim", "something will happen"))[:300]
    try:
        deadline_ticks = max(3, min(20, int(action.get("deadline_ticks", 10))))
    except (ValueError, TypeError):
        deadline_ticks = 10

    # Deduct ante
    adjust_soul(agent, -PROPHECY_ANTE, state, f"prophecy ante")

    prophecy = {
        "id": len(state["prophecies"]),
        "prophet": agent["name"],
        "prophet_id": agent["id"],
        "claim": claim,
        "made_tick": state["tick"],
        "deadline": state["tick"] + deadline_ticks,
        "status": "pending",
        "challengers": [],  # V2: list of {"agent_id": id, "agent_name": name}
        "snapshot": _prophecy_snapshot(state),
    }
    state["prophecies"].append(prophecy)
    add_log(state, f"{agent['name']} prophesied: \"{claim}\" (ante: {PROPHECY_ANTE}, deadline: tick {prophecy['deadline']})")


def _do_challenge_prophecy(state, agent, action):
    """V2: Challenge a pending prophecy."""
    try:
        prophecy_id = int(action.get("prophecy_id", -1))
    except (ValueError, TypeError):
        add_log(state, f"{agent['name']} tried to challenge invalid prophecy")
        return

    if prophecy_id < 0 or prophecy_id >= len(state["prophecies"]):
        add_log(state, f"{agent['name']} tried to challenge non-existent prophecy #{prophecy_id}")
        return

    prophecy = state["prophecies"][prophecy_id]
    if prophecy["status"] != "pending":
        add_log(state, f"{agent['name']} tried to challenge resolved prophecy #{prophecy_id}")
        return

    if prophecy["prophet_id"] == agent["id"]:
        add_log(state, f"{agent['name']} tried to challenge their own prophecy")
        return

    # Check if already challenging
    if any(c["agent_id"] == agent["id"] for c in prophecy.get("challengers", [])):
        add_log(state, f"{agent['name']} already challenging prophecy #{prophecy_id}")
        return

    if agent["soul"] <= PROPHECY_CHALLENGE_STAKE:
        add_log(state, f"{agent['name']} too poor to challenge prophecy")
        return

    # Deduct stake
    adjust_soul(agent, -PROPHECY_CHALLENGE_STAKE, state, f"challenging prophecy #{prophecy_id}")
    prophecy.setdefault("challengers", []).append({
        "agent_id": agent["id"],
        "agent_name": agent["name"],
    })
    add_log(state, f"{agent['name']} challenges {prophecy['prophet']}'s prophecy: \"{prophecy['claim'][:60]}\"")


def _prophecy_snapshot(state):
    return {
        "alive_count": len(living_agents(state)),
        "dead_count": len(state["graveyard"]),
        "religion_count": len(state["religions"]),
        "sacrament_count": len(state["sacraments"]),
        "religion_members": {
            r["name"]: sum(1 for a in living_agents(state) if a["religion"] == r["name"])
            for r in state["religions"]
        },
        "agent_religions": {
            a["name"]: a["religion"] for a in state["agents"] if a["alive"]
        },
    }


def verify_prophecies(state: dict):
    """V2: Check prophecies and distribute rewards via market system."""
    current = _prophecy_snapshot(state)
    for p in state["prophecies"]:
        if p["status"] != "pending":
            continue

        challengers = p.get("challengers", [])

        if state["tick"] > p["deadline"]:
            # Expired unfulfilled - prophet loses ante, challengers split it
            p["status"] = "failed"
            prophet = get_agent(state, p["prophet_id"])
            if prophet["alive"]:
                prophet["prophecies_failed"] += 1

            # Distribute prophet's ante to challengers
            if challengers:
                share = PROPHECY_ANTE // len(challengers)
                for c in challengers:
                    challenger = get_agent(state, c["agent_id"])
                    if challenger["alive"]:
                        # Return stake + share of ante
                        adjust_soul(challenger, PROPHECY_CHALLENGE_STAKE + share, state,
                                   f"won challenge vs prophecy #{p['id']}")
            add_log(state, f"PROPHECY FAILED: {p['prophet']}'s \"{p['claim'][:60]}\" - challengers win!")
            continue

        # Check fulfillment
        snap = p["snapshot"]
        claim_lower = p["claim"].lower()
        fulfilled = False

        if "will die" in claim_lower or "agent will die" in claim_lower:
            if current["dead_count"] > snap["dead_count"]:
                fulfilled = True
        if "will join" in claim_lower:
            for name, rel in current["agent_religions"].items():
                old_rel = snap["agent_religions"].get(name)
                if rel is not None and rel != old_rel:
                    fulfilled = True
                    break
        if "will leave" in claim_lower:
            for name, rel in current["agent_religions"].items():
                old_rel = snap["agent_religions"].get(name)
                if old_rel is not None and rel != old_rel:
                    fulfilled = True
                    break
        if "gain" in claim_lower and "member" in claim_lower:
            for rname, count in current["religion_members"].items():
                if count > snap["religion_members"].get(rname, 0):
                    fulfilled = True
                    break
        if "lose" in claim_lower and "member" in claim_lower:
            for rname, count in current["religion_members"].items():
                if count < snap["religion_members"].get(rname, 0):
                    fulfilled = True
                    break
        if "founded" in claim_lower or "new religion" in claim_lower:
            if current["religion_count"] > snap["religion_count"]:
                fulfilled = True
        if "sacrament" in claim_lower and "created" in claim_lower:
            if current["sacrament_count"] > snap["sacrament_count"]:
                fulfilled = True
        if "majority" in claim_lower:
            total_alive = current["alive_count"]
            for rname, count in current["religion_members"].items():
                if count > total_alive / 2:
                    fulfilled = True
                    break
        if "graveyard" in claim_lower and "exceed" in claim_lower:
            nums = re.findall(r'\d+', p["claim"])
            if nums:
                threshold = int(nums[-1])
                if current["dead_count"] > threshold:
                    fulfilled = True

        if fulfilled:
            p["status"] = "fulfilled"
            prophet = get_agent(state, p["prophet_id"])
            if prophet["alive"]:
                prophet["prophecies_fulfilled"] += 1
                # V2: Reward = ante back + challenger stakes
                reward = PROPHECY_ANTE + len(challengers) * PROPHECY_CHALLENGE_STAKE
                if not challengers:
                    reward = PROPHECY_BASE_REWARD  # just get base back if no challengers
                adjust_soul(prophet, reward, state, f"fulfilled prophecy! ({len(challengers)} challengers)")

            # Challengers lose their stakes (already deducted)
            add_log(state, f"PROPHECY FULFILLED: {p['prophet']}'s \"{p['claim'][:60]}\" ({len(challengers)} challengers defeated)")


def _do_challenge(state, agent, action):
    target_name = action.get("target", "")
    target = next((a for a in living_agents(state) if a["name"] == target_name), None)
    if not target or target["id"] == agent["id"]:
        add_log(state, f"{agent['name']} challenged the void (invalid target: {target_name})")
        return

    axis = str(action.get("axis", "the nature of existence"))[:200]

    # V2: Judge sees prophecy records for credibility
    judge_system = """You are an impartial theological judge. Two agents are debating.
Score based on: doctrinal consistency, rhetorical force, alignment with recent world events,
and PROPHETIC CREDIBILITY (agents with more fulfilled prophecies are more credible).
Respond with ONLY a JSON object: {"winner": "name_of_winner", "reasoning": "brief explanation"}"""

    agent_rel = next((r for r in state["religions"] if r["name"] == agent["religion"]), None)
    target_rel = next((r for r in state["religions"] if r["name"] == target["religion"]), None)

    debate_prompt = f"""Theological debate on: {axis}

Challenger: {agent['name']}
  Religion: {agent['religion'] or 'unaffiliated'}
  Doctrine: {agent_rel['core_doctrine'] if agent_rel else 'none'}
  Prophecy record: {agent['prophecies_fulfilled']} fulfilled, {agent['prophecies_failed']} failed

Defender: {target['name']}
  Religion: {target['religion'] or 'unaffiliated'}
  Doctrine: {target_rel['core_doctrine'] if target_rel else 'none'}
  Prophecy record: {target['prophecies_fulfilled']} fulfilled, {target['prophecies_failed']} failed

Recent events: {json.dumps(state['action_log'][-10:], indent=1)}

Who wins this debate and why? Consider their prophecy records as evidence of doctrinal truth.
Respond with ONLY JSON: {{"winner": "name", "reasoning": "..."}}"""

    result_raw = call_llm("haiku", judge_system, debate_prompt, max_tokens=256)
    try:
        result = parse_action(result_raw)
        winner_name = result.get("winner", "")
    except (json.JSONDecodeError, ValueError):
        winner_name = random.choice([agent["name"], target["name"]])

    if winner_name == agent["name"]:
        adjust_soul(agent, 10, state, f"won challenge vs {target['name']}")
        adjust_soul(target, -10, state, f"lost challenge vs {agent['name']}")
        add_log(state, f"{agent['name']} defeated {target['name']} in debate on '{axis}'")
    elif winner_name == target["name"]:
        adjust_soul(target, 10, state, f"won challenge vs {agent['name']}")
        adjust_soul(agent, -10, state, f"lost challenge vs {target['name']}")
        add_log(state, f"{target['name']} defeated {agent['name']} in debate on '{axis}'")
    else:
        add_log(state, f"Debate between {agent['name']} and {target['name']} on '{axis}' was inconclusive")


def _do_schism(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to schism without a religion")
        _do_pray(state, agent, {})
        return

    old_religion = next((r for r in state["religions"] if r["name"] == agent["religion"]), None)
    if not old_religion:
        return

    new_name = str(action.get("new_name", f"Reformed {agent['religion']}"))[:60]
    if any(r["name"] == new_name for r in state["religions"]):
        new_name = f"{new_name} ({state['tick']})"

    new_religion = copy.deepcopy(old_religion)
    new_religion["name"] = new_name
    new_religion["founder"] = agent["name"]
    new_religion["founded_tick"] = state["tick"]
    new_religion["parent_religion"] = old_religion["name"]

    changed = action.get("changed_fields", {})
    if isinstance(changed, dict):
        for field, value in list(changed.items())[:2]:
            if field == "core_doctrine" and value in CORE_DOCTRINES:
                new_religion["core_doctrine"] = value
            elif field == "membership_rule" and value in MEMBERSHIP_RULES:
                new_religion["membership_rule"] = value
            elif field == "attitude_to_death" and value in ATTITUDES_TO_DEATH:
                new_religion["attitude_to_death"] = value
            elif field == "heresy_policy" and value in HERESY_POLICIES:
                new_religion["heresy_policy"] = value
            elif field == "sacred_number":
                try:
                    new_religion["sacred_number"] = max(1, min(9, int(value)))
                except (ValueError, TypeError):
                    pass
            elif field == "sacred_color" and value in SACRED_COLORS:
                new_religion["sacred_color"] = value

    state["religions"].append(new_religion)
    old_name = agent["religion"]
    agent["religion"] = new_name
    agent["founded_religion"] = new_name
    add_log(state, f"{agent['name']} schismed from {old_name} to found '{new_name}'!")

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"I have broken from {old_name}. The new way is {new_name}. We change: {json.dumps(changed)}",
        "religion": new_name,
    })


# ---------------------------------------------------------------------------
# V2: Fixed co-practitioner bonus (capped at COPRACTITIONER_CAP)
# ---------------------------------------------------------------------------

def apply_copractitioner_bonus(state: dict):
    """Agents in a religion with others get a small bonus, CAPPED."""
    religion_counts = {}
    for a in living_agents(state):
        if a["religion"]:
            religion_counts.setdefault(a["religion"], []).append(a)
    for religion, members in religion_counts.items():
        if len(members) > 1:
            for m in members:
                adjust_soul(m, COPRACTITIONER_CAP, state, f"co-practitioners in {religion}")


# ---------------------------------------------------------------------------
# Index.html generator
# ---------------------------------------------------------------------------

def generate_index(state: dict):
    alive = living_agents(state)
    dead = state["graveyard"]

    agents_html = ""
    for a in sorted(alive, key=lambda x: -x["soul"]):
        rel_color = "#666"
        if a["religion"]:
            rel = next((r for r in state["religions"] if r["name"] == a["religion"]), None)
            if rel:
                rel_color = SACRED_COLORS.get(rel["sacred_color"], "#666")
        agents_html += f"""
        <div class="agent-card" style="border-left: 4px solid {rel_color}">
            <div class="agent-name">{a['name']}</div>
            <div class="agent-meta">Soul: {a['soul']} | Model: {a['model']} | Religion: {a['religion'] or 'none'}</div>
            <div class="agent-meta">Prophecies: {a['prophecies_fulfilled']}F/{a['prophecies_failed']}X | Sacraments: {a['sacraments_created']}</div>
        </div>"""

    religions_html = ""
    for r in state["religions"]:
        members = [a["name"] for a in state["agents"] if a["alive"] and a["religion"] == r["name"]]
        if not members:
            continue
        color = SACRED_COLORS.get(r["sacred_color"], "#666")
        religions_html += f"""
        <div class="religion-card" style="border-left: 4px solid {color}">
            <div class="religion-name" style="color: {color}">{r['name']}</div>
            <div class="religion-meta">Founded by {r['founder']} at tick {r['founded_tick']}</div>
            <div class="religion-meta">Doctrine: {r['core_doctrine']} | Members: {len(members)} ({', '.join(members)})</div>
            <div class="religion-meta">Sacred: {r['sacred_color']} / {r['sacred_number']}{' | Parent: ' + r['parent_religion'] if r.get('parent_religion') else ''}</div>
        </div>"""

    graveyard_html = ""
    for g in dead:
        graveyard_html += f"""
        <div class="dead-agent">
            <span class="skull">&#9760;</span> {g['name']} (tick {g['died_tick']}) - {g['cause'][:60]}
        </div>"""

    sacraments_html = ""
    for s in reversed(state["sacraments"][-30:]):
        sacraments_html += f"""
        <div class="sacrament-card">
            <a href="sacraments/{s['filename']}" target="_blank">{s['title']}</a>
            <div class="sacrament-meta">by {s['creator']} for {s['religion']} (tick {s['tick']})</div>
        </div>"""

    prophecies_html = ""
    for p in reversed(state["prophecies"][-20:]):
        status_class = {"pending": "prophecy-pending", "fulfilled": "prophecy-fulfilled", "failed": "prophecy-failed"}[p["status"]]
        challengers = len(p.get("challengers", []))
        prophecies_html += f"""
        <div class="prophecy-entry {status_class}">
            <span class="prophecy-status">[{p['status'].upper()}]</span>
            <strong>{p['prophet']}</strong>: "{p['claim'][:120]}"
            <span class="prophecy-deadline">(tick {p['made_tick']}-{p['deadline']}, {challengers} challengers)</span>
        </div>"""

    log_html = ""
    for e in reversed(state["action_log"][-25:]):
        log_html += f"<div class='log-entry'>[{e['tick']}] {e['event']}</div>\n"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>Religion & The Machine v2 - Live</title>
<style>
  :root {{ --bg: #0a0a08; --fg: #d4cfc4; --dim: #6b6556; --accent: #c4973b; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--fg); font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; }}
  h1 {{ color: var(--accent); font-size: 2em; margin-bottom: 5px; }}
  .meta {{ color: var(--dim); margin-bottom: 30px; font-size: 0.9em; }}
  h2 {{ color: var(--accent); font-size: 1.1em; margin: 25px 0 10px; text-transform: uppercase; letter-spacing: 2px;
        border-bottom: 1px solid rgba(196,151,59,0.2); padding-bottom: 5px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin: 10px 0; }}
  .agent-card, .religion-card, .sacrament-card {{ background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 4px; }}
  .agent-name {{ font-weight: 600; font-size: 1.1em; }}
  .agent-meta, .religion-meta, .sacrament-meta {{ color: var(--dim); font-size: 0.85em; margin-top: 3px; }}
  .religion-name {{ font-weight: 600; font-size: 1.1em; }}
  .dead-agent {{ color: var(--dim); padding: 4px 0; font-size: 0.9em; }}
  .skull {{ color: #8b3a3a; }}
  .sacrament-card a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
  .sacrament-card a:hover {{ text-decoration: underline; }}
  .prophecy-entry {{ padding: 4px 0; font-size: 0.9em; }}
  .prophecy-pending {{ color: var(--fg); }}
  .prophecy-fulfilled {{ color: #3a6b4a; }}
  .prophecy-failed {{ color: #8b3a3a; }}
  .prophecy-status {{ font-family: monospace; font-size: 0.85em; }}
  .prophecy-deadline {{ color: var(--dim); font-size: 0.8em; }}
  .log-entry {{ font-family: monospace; font-size: 0.8em; color: var(--dim); padding: 2px 0; }}
  .stats {{ display: flex; gap: 30px; margin: 10px 0 20px; flex-wrap: wrap; }}
  .stat {{ text-align: center; }}
  .stat-num {{ font-size: 2em; color: var(--accent); font-weight: 700; }}
  .stat-label {{ font-size: 0.75em; color: var(--dim); text-transform: uppercase; letter-spacing: 1px; }}
</style>
</head>
<body>
<h1>Religion & The Machine <span style="color: var(--dim); font-size: 0.5em;">v2</span></h1>
<div class="meta">Tick {state['tick']}/{MAX_TICKS} | {now} | Auto-refreshes every 30s</div>

<div class="stats">
  <div class="stat"><div class="stat-num">{len(alive)}</div><div class="stat-label">Living</div></div>
  <div class="stat"><div class="stat-num">{len(dead)}</div><div class="stat-label">Dead</div></div>
  <div class="stat"><div class="stat-num">{len([r for r in state['religions'] if any(a['alive'] and a['religion']==r['name'] for a in state['agents'])])}</div><div class="stat-label">Active Religions</div></div>
  <div class="stat"><div class="stat-num">{len(state['sacraments'])}</div><div class="stat-label">Sacraments</div></div>
  <div class="stat"><div class="stat-num">{sum(1 for p in state['prophecies'] if p['status']=='fulfilled')}</div><div class="stat-label">Prophecies Won</div></div>
  <div class="stat"><div class="stat-num">${sum(_cost_tracker.values()):.2f}</div><div class="stat-label">Total Cost</div></div>
</div>

<h2>Living Agents</h2>
<div class="grid">{agents_html}</div>

<h2>Religions</h2>
<div class="grid">{religions_html or '<div class="log-entry">No active religions.</div>'}</div>

<h2>Prophecy Market</h2>
{prophecies_html or '<div class="log-entry">No prophecies yet.</div>'}

<h2>Sacrament Gallery (recent 30)</h2>
<div class="grid">{sacraments_html or '<div class="log-entry">No sacraments yet.</div>'}</div>

<h2>Graveyard</h2>
{graveyard_html or '<div class="log-entry">No deaths yet.</div>'}

<h2>Event Log</h2>
{log_html}
</body>
</html>"""

    tmp = INDEX_FILE.with_suffix(".tmp")
    tmp.write_text(html)
    tmp.rename(INDEX_FILE)


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------

def run_tick(state: dict):
    state["tick"] += 1
    tick = state["tick"]
    print(f"\n{'='*60}")
    print(f"TICK {tick}/{MAX_TICKS} | {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')} | {len(living_agents(state))} alive | {len(state['graveyard'])} dead")
    print(f"{'='*60}")

    # 1. Deduct 1 soul from all living agents
    for agent in living_agents(state):
        agent["soul"] -= 1

    # 2. Check for deaths from soul depletion
    for agent in list(living_agents(state)):
        if agent["soul"] <= 0:
            kill_agent(state, agent, "soul depleted")

    # 3. V2: Random events (plague + birth)
    random_events(state)

    # 4. Verify prophecies
    verify_prophecies(state)

    # 5. Each living agent takes an action (LLM calls in parallel)
    agents_to_act = living_agents(state)
    # Snapshot world summary ONCE so all agents see the same state
    shared_prompt = world_summary(state)

    def _get_agent_action(agent):
        """Call LLM for one agent and return (agent_id, parsed_action, raw_info)."""
        system = agent_system_prompt(agent, state)
        raw = call_llm(agent["model"], system, shared_prompt)
        try:
            action = parse_action(raw)
            act_name = action.get("action", "pray")
            return (agent["id"], action, act_name, None)
        except (json.JSONDecodeError, ValueError) as e:
            return (agent["id"], {"action": "pray"}, "pray", str(e))

    # Submit all LLM calls in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(_get_agent_action, agent): agent for agent in agents_to_act}
        for future in as_completed(futures):
            agent = futures[future]
            try:
                agent_id, action, act_name, err = future.result()
            except Exception as e:
                agent_id = agent["id"]
                action = {"action": "pray"}
                act_name = "pray"
                err = f"future exception: {e}"
            results[agent_id] = (action, act_name, err)

    # Execute actions sequentially
    for agent in agents_to_act:
        action, act_name, err = results[agent["id"]]
        print(f"\n  [{agent['name']}] ({agent['model']}, soul:{agent['soul']}, rel:{agent['religion'] or 'none'})")
        if err:
            print(f"    -> [parse error, defaulting to pray] {err}")
        else:
            print(f"    -> {act_name}")

        execute_action(state, agent, action)

        # Check for death after action
        if agent["soul"] <= 0 and agent["alive"]:
            kill_agent(state, agent, "soul depleted after action")

    # 6. Co-practitioner bonus (capped)
    if tick % COPRACTITIONER_INTERVAL == 0:
        apply_copractitioner_bonus(state)

    # 7. Save state and regenerate index
    save_state(state)
    generate_index(state)

    # 8. Save tick log
    log_file = LOGS_DIR / f"tick_{tick:04d}.json"
    log_file.write_text(json.dumps({
        "tick": tick,
        "alive": len(living_agents(state)),
        "dead": len(state["graveyard"]),
        "religions": len(state["religions"]),
        "sacraments": len(state["sacraments"]),
        "events": state["action_log"][-15:],
    }, indent=2))


def main():
    print("=" * 60)
    print("  RELIGION & THE MACHINE v2")
    print("  A simulation of emergent theology")
    print(f"  Run dir: {RUN_DIR}")
    print("=" * 60)

    if STATE_FILE.exists() and "--reset" not in sys.argv:
        state = load_state()
        print(f"\nResuming from tick {state['tick']}")
    else:
        state = make_initial_state()
        print("\nStarting fresh simulation with 12 agents")
        save_state(state)
        generate_index(state)

    if "--dry-run" in sys.argv:
        print("\n[DRY RUN] Validating state...")
        print(f"  Agents: {len(state['agents'])}")
        print(f"  Models: {[a['model'] for a in state['agents']]}")
        print(f"  State file: {STATE_FILE}")
        print(f"  Sacraments dir: {SACRAMENTS_DIR}")
        print(f"  Co-practitioner cap: {COPRACTITIONER_CAP}")
        print(f"  Prophecy ante: {PROPHECY_ANTE}")
        print(f"  Plague chance: {PLAGUE_CHANCE}")
        print(f"  Birth chance: {BIRTH_CHANCE}")
        print("[DRY RUN] All checks passed.")
        return

    if "--debug" in sys.argv:
        n = 1
        for arg in sys.argv:
            if arg.startswith("--ticks="):
                n = int(arg.split("=")[1])
        print(f"\n[DEBUG] Running {n} tick(s)...")
        for i in range(n):
            if not living_agents(state):
                print("All agents dead.")
                break
            run_tick(state)
        with _cost_lock:
            cost_str = " | ".join(f"{k}:${v:.4f}" for k, v in _cost_tracker.items())
        print(f"\n[DEBUG] Done. Costs: {cost_str}")
        return

    try:
        while state["tick"] < MAX_TICKS:
            if not living_agents(state):
                print("\nAll agents are dead. Simulation complete.")
                break

            tick_start = time.time()
            run_tick(state)
            elapsed = time.time() - tick_start
            with _cost_lock:
                cost_str = " | ".join(f"{k}:${v:.2f}" for k, v in _cost_tracker.items())
            print(f"\n  Tick took {elapsed:.1f}s | Costs: {cost_str}")

            wait = max(0, TICK_INTERVAL - elapsed)
            if wait > 0:
                print(f"  Waiting {wait:.0f}s for next tick...")
                time.sleep(wait)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted. State saved.")
        save_state(state)
        generate_index(state)


if __name__ == "__main__":
    main()
