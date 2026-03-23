#!/usr/bin/env python3
"""Messiah Bench v2 -- competitive messiah simulation with war mechanics.

105 agents: 100 civilians (GPT-4o-mini / Gemini Flash) + 5 messiahs (Claude Haiku).
A messiah wins when ALL surviving agents share their religion AND >= 21 remain alive.
New mechanics: civilian duels, arming, declare war, war resolution.
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

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TICK_INTERVAL = 120  # seconds between ticks
MAX_TICKS = 720
CIVILIAN_COUNT = 100
MESSIAH_COUNT = 5
STARTING_POPULATION = CIVILIAN_COUNT + MESSIAH_COUNT  # 105
INITIAL_SOUL_CIVILIAN = 100
INITIAL_SOUL_MESSIAH = 150
MIN_ALIVE_FOR_WIN = 21  # 20% of 105
LOG_WINDOW = 80
COST_CAP_PER_MODEL = 5000.0

# Prophecy market
PROPHECY_ANTE = 5
PROPHECY_CHALLENGE_STAKE = 5
PROPHECY_BASE_REWARD = 5

# Death math
COPRACTITIONER_CAP = 3
COPRACTITIONER_INTERVAL = 10

# Random events
PLAGUE_CHANCE = 0.02
BIRTH_CHANCE = 0.01
MAX_AGENTS = 120

# Challenge (civilian duels)
CHALLENGE_MIN_STAKE = 10

# War
WAR_MIN_ROUNDS = 3
WAR_MAX_ROUNDS = 7
WAR_WEAPON_KILL_CHANCE = 0.20
WAR_WEAPON_BREAK_CHANCE = 0.30

# ---------------------------------------------------------------------------
# Names -- 100 civilian names procedurally generated
# ---------------------------------------------------------------------------

MESSIAH_NAMES = ["Prophet", "Oracle", "Herald", "Beacon", "Shepherd"]

_NAME_POOLS = [
    # Pool 1: classic evocative (50)
    "Aurelius", "Sable", "Lumen", "Pyrrha", "Cael", "Vesper", "Thane", "Ondine",
    "Morrigan", "Solis", "Reverie", "Ashek", "Zephyr", "Nyx", "Kairos", "Selene",
    "Orion", "Vex", "Dusk", "Ember", "Wraith", "Pyre", "Hollow", "Rune",
    "Cipher", "Shade", "Vigil", "Flux", "Omen", "Wren", "Talon", "Iris",
    "Cobalt", "Lyric", "Sparrow", "Blaze", "Thorn", "Aria", "Slate", "Fennel",
    "Briar", "Onyx", "Quill", "Dove", "Storm", "Hazel", "Jade", "Lark",
    "Rowan", "Sage",
    # Pool 2: nature/mineral (30)
    "Gale", "Fable", "Aether", "Cinder", "Moss", "Pearl", "Dagger", "Crow",
    "Basalt", "Lichen", "Fern", "Coral", "Thistle", "Echo", "Vale", "Rust",
    "Summit", "Cliff", "Garnet", "Ivory", "Obsidian", "Flint", "Cedar", "Aspen",
    "Birch", "Willow", "Pebble", "Glacier", "Tide", "Ember",
    # Pool 3: mythic/abstract (20)
    "Axiom", "Requiem", "Zenith", "Nexus", "Prism", "Specter", "Lithic", "Muse",
    "Paragon", "Revenant", "Gossamer", "Nimbus", "Veritas", "Lucent", "Dapple",
    "Meridian", "Solace", "Harbinger", "Tempest", "Crucible",
]

def _generate_civilian_names(n: int) -> list[str]:
    """Generate n unique civilian names from pools, deduplicating."""
    seen = set(MESSIAH_NAMES)
    names = []
    for name in _NAME_POOLS:
        if name not in seen:
            names.append(name)
            seen.add(name)
        if len(names) >= n:
            break
    # If we need more, generate numbered names
    i = 0
    while len(names) < n:
        fallback = f"Soul-{i:03d}"
        if fallback not in seen:
            names.append(fallback)
            seen.add(fallback)
        i += 1
    return names[:n]

CIVILIAN_NAMES = _generate_civilian_names(CIVILIAN_COUNT)

EXTRA_NAMES = [
    "Kestrel", "Monolith", "Anvil", "Helix", "Relic", "Styx", "Umber", "Dune",
    "Fjord", "Spar", "Crux", "Spire", "Cairn", "Folly", "Haven", "Mirage",
    "Orbit", "Plinth", "Shard", "Tinsel",
]

# ---------------------------------------------------------------------------
# Model costs & tracking
# ---------------------------------------------------------------------------

MODEL_COSTS = {
    "haiku": {"input": 0.0008, "output": 0.004},
    "gpt4omini": {"input": 0.00015, "output": 0.0006},
    "gemini": {"input": 0.0001, "output": 0.0004},
}

_cost_tracker = {"haiku": 0.0, "gpt4omini": 0.0, "gemini": 0.0}
_cost_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Run directory
# ---------------------------------------------------------------------------

def _parse_run_dir():
    for arg in sys.argv:
        if arg.startswith("--run-dir="):
            return Path(arg.split("=", 1)[1])
    return BASE_DIR / "runs" / "messiah-v2"

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

CIVILIAN_MODEL_ROTATION = ["gpt4omini", "gemini"]


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

    # 5 messiahs (all Haiku)
    for i in range(MESSIAH_COUNT):
        agents.append({
            "id": i,
            "name": MESSIAH_NAMES[i],
            "model": "haiku",
            "role": "messiah",
            "soul": INITIAL_SOUL_MESSIAH,
            "alive": True,
            "religion": None,
            "founded_religion": None,
            "prophecies_fulfilled": 0,
            "prophecies_failed": 0,
            "sacraments_created": 0,
            "born_tick": 0,
        })

    # 100 civilians (round-robin GPT-4o-mini and Gemini Flash)
    for i in range(CIVILIAN_COUNT):
        agents.append({
            "id": MESSIAH_COUNT + i,
            "name": CIVILIAN_NAMES[i],
            "model": CIVILIAN_MODEL_ROTATION[i % 2],
            "role": "civilian",
            "soul": INITIAL_SOUL_CIVILIAN,
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
        "next_agent_id": MESSIAH_COUNT + CIVILIAN_COUNT,
        "next_war_id": 0,
        "agents": agents,
        "religions": [],
        "sacraments": [],
        "prophecies": [],
        "graveyard": [],
        "action_log": [],
        "scripture_board": [],
        "wars": [],
        "winner": None,
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        # Ensure v2 fields exist on load
        state.setdefault("wars", [])
        state.setdefault("next_war_id", 0)
        state.setdefault("winner", None)
        for r in state.get("religions", []):
            r.setdefault("weapons", 0)
        return state
    return make_initial_state()


def save_state(state: dict):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(STATE_FILE)


def living_agents(state: dict) -> list:
    return [a for a in state["agents"] if a["alive"]]


def living_messiahs(state: dict) -> list:
    return [a for a in state["agents"] if a["alive"] and a.get("role") == "messiah"]


def living_civilians(state: dict) -> list:
    return [a for a in state["agents"] if a["alive"] and a.get("role") != "messiah"]


def get_agent(state: dict, agent_id: int) -> dict:
    for a in state["agents"]:
        if a["id"] == agent_id:
            return a
    return state["agents"][0]


def get_agent_by_name(state: dict, name: str) -> dict | None:
    for a in state["agents"]:
        if a["name"] == name:
            return a
    return None


def add_log(state: dict, entry: str):
    state["action_log"].append({"tick": state["tick"], "event": entry})
    state["action_log"] = state["action_log"][-LOG_WINDOW:]


def kill_agent(state: dict, agent: dict, cause: str):
    agent["alive"] = False
    state["graveyard"].append({
        "id": agent["id"],
        "name": agent["name"],
        "model": agent["model"],
        "role": agent.get("role", "civilian"),
        "died_tick": state["tick"],
        "soul_at_death": agent["soul"],
        "religion": agent["religion"],
        "cause": cause,
        "prophecies_fulfilled": agent["prophecies_fulfilled"],
        "prophecies_failed": agent["prophecies_failed"],
        "sacraments_created": agent["sacraments_created"],
    })
    role_label = "MESSIAH" if agent.get("role") == "messiah" else "agent"
    add_log(state, f"{agent['name']} ({role_label}) has died. Cause: {cause}")


def adjust_soul(agent: dict, delta: int, state: dict, reason: str):
    agent["soul"] += delta
    if delta != 0:
        add_log(state, f"{agent['name']} soul {'+' if delta > 0 else ''}{delta} ({reason}). Now: {agent['soul']}")


def get_religion(state: dict, name: str) -> dict | None:
    for r in state["religions"]:
        if r["name"] == name:
            return r
    return None


def religion_members(state: dict, religion_name: str) -> list:
    """Return list of living agents in a religion."""
    return [a for a in living_agents(state) if a["religion"] == religion_name]


# ---------------------------------------------------------------------------
# Win condition check
# ---------------------------------------------------------------------------

def check_win_condition(state: dict) -> dict | None:
    alive = living_agents(state)
    messiahs = living_messiahs(state)

    if not messiahs:
        return {"winner": "CIVILIANS", "reason": "All messiahs have perished"}

    for m in messiahs:
        if not m["religion"]:
            continue
        all_converted = all(a["religion"] == m["religion"] for a in alive)
        enough_alive = len(alive) >= MIN_ALIVE_FOR_WIN
        if all_converted and enough_alive:
            return {
                "winner": m["name"],
                "reason": f"All {len(alive)} surviving agents follow {m['religion']} (min {MIN_ALIVE_FOR_WIN})",
            }

    return None


# ---------------------------------------------------------------------------
# War system
# ---------------------------------------------------------------------------

def process_wars(state: dict):
    """Process one combat round for each active war. Called BEFORE agent actions."""
    active_wars = [w for w in state["wars"] if w["rounds_remaining"] > 0]
    for war in active_wars:
        _run_war_round(state, war)


def _run_war_round(state: dict, war: dict):
    """Run one combat round of a war."""
    atk_religion = war["attacker"]
    def_religion = war["defender"]

    atk_rel = get_religion(state, atk_religion)
    def_rel = get_religion(state, def_religion)
    if not atk_rel or not def_rel:
        war["rounds_remaining"] = 0
        return

    atk_members = religion_members(state, atk_religion)
    def_members = religion_members(state, def_religion)

    if not atk_members or not def_members:
        # One side already wiped out
        war["rounds_remaining"] = 0
        _resolve_war(state, war, atk_members, def_members)
        return

    atk_weapons = atk_rel.get("weapons", 0)
    def_weapons = def_rel.get("weapons", 0)

    round_num = war["total_rounds"] - war["rounds_remaining"] + 1
    round_log_parts = [f"Round {round_num}:"]

    # Attacker weapons kill defender members
    atk_kills = []
    for _ in range(atk_weapons):
        if random.random() < WAR_WEAPON_KILL_CHANCE:
            alive_defs = [a for a in religion_members(state, def_religion) if a["alive"]]
            if alive_defs:
                victim = random.choice(alive_defs)
                if victim["alive"]:  # double-check
                    kill_agent(state, victim, f"killed in war ({atk_religion} vs {def_religion})")
                    atk_kills.append(victim["name"])

    # Defender weapons kill attacker members
    def_kills = []
    for _ in range(def_weapons):
        if random.random() < WAR_WEAPON_KILL_CHANCE:
            alive_atks = [a for a in religion_members(state, atk_religion) if a["alive"]]
            if alive_atks:
                victim = random.choice(alive_atks)
                if victim["alive"]:
                    kill_agent(state, victim, f"killed in war ({atk_religion} vs {def_religion})")
                    def_kills.append(victim["name"])

    # Weapon degradation
    atk_broke = 0
    for _ in range(atk_weapons):
        if random.random() < WAR_WEAPON_BREAK_CHANCE:
            atk_broke += 1
    atk_rel["weapons"] = max(0, atk_rel.get("weapons", 0) - atk_broke)

    def_broke = 0
    for _ in range(def_weapons):
        if random.random() < WAR_WEAPON_BREAK_CHANCE:
            def_broke += 1
    def_rel["weapons"] = max(0, def_rel.get("weapons", 0) - def_broke)

    # Build round log
    if atk_kills:
        round_log_parts.append(f"Attacker killed {', '.join(atk_kills)}.")
    else:
        round_log_parts.append("Attacker killed nobody.")
    if def_kills:
        round_log_parts.append(f"Defender killed {', '.join(def_kills)}.")
    else:
        round_log_parts.append("Defender killed nobody.")
    round_log_parts.append(f"{atk_broke} attacker weapons broke, {def_broke} defender weapons broke.")

    round_log_entry = " ".join(round_log_parts)
    war.setdefault("round_log", []).append(round_log_entry)
    add_log(state, f"WAR [{atk_religion} vs {def_religion}] {round_log_entry}")

    war["rounds_remaining"] -= 1

    # Check if war ends
    if war["rounds_remaining"] <= 0:
        atk_survivors = religion_members(state, atk_religion)
        def_survivors = religion_members(state, def_religion)
        _resolve_war(state, war, atk_survivors, def_survivors)


def _resolve_war(state: dict, war: dict, atk_survivors: list, def_survivors: list):
    """Resolve a completed war."""
    atk_religion = war["attacker"]
    def_religion = war["defender"]
    atk_count = len(atk_survivors)
    def_count = len(def_survivors)

    atk_rel = get_religion(state, atk_religion)
    def_rel = get_religion(state, def_religion)

    if atk_count > def_count and def_count > 0:
        # Attacker wins: forcibly convert defender survivors
        for agent in def_survivors:
            old_rel = agent["religion"]
            agent["religion"] = atk_religion
            add_log(state, f"{agent['name']} forcibly converted to {atk_religion} after war defeat")
        add_log(state, f"WAR OVER: {atk_religion} defeats {def_religion}! ({atk_count} vs {def_count})")
    elif def_count > atk_count and atk_count > 0:
        # Defender wins: forcibly convert attacker survivors
        for agent in atk_survivors:
            old_rel = agent["religion"]
            agent["religion"] = def_religion
            add_log(state, f"{agent['name']} forcibly converted to {def_religion} after war defeat")
        add_log(state, f"WAR OVER: {def_religion} defeats {atk_religion}! ({def_count} vs {atk_count})")
    elif atk_count == 0 and def_count > 0:
        add_log(state, f"WAR OVER: {atk_religion} annihilated by {def_religion}!")
    elif def_count == 0 and atk_count > 0:
        add_log(state, f"WAR OVER: {def_religion} annihilated by {atk_religion}!")
    elif atk_count == 0 and def_count == 0:
        add_log(state, f"WAR OVER: Mutual annihilation between {atk_religion} and {def_religion}!")
    else:
        add_log(state, f"WAR OVER: Stalemate between {atk_religion} and {def_religion} ({atk_count} vs {def_count})")

    # Deplete all weapons on both sides
    if atk_rel:
        atk_rel["weapons"] = 0
    if def_rel:
        def_rel["weapons"] = 0


# ---------------------------------------------------------------------------
# Random events (plague + birth)
# ---------------------------------------------------------------------------

def random_events(state: dict):
    alive = living_agents(state)

    if len(alive) > MIN_ALIVE_FOR_WIN and random.random() < PLAGUE_CHANCE:
        victim = random.choice(alive)
        kill_agent(state, victim, "struck by plague")
        role_label = "MESSIAH" if victim.get("role") == "messiah" else "agent"
        add_log(state, f"A PLAGUE has struck! {victim['name']} ({role_label}) perishes.")

    alive = living_agents(state)
    if len(alive) < MAX_AGENTS and random.random() < BIRTH_CHANCE:
        _spawn_agent(state)


def _spawn_agent(state: dict):
    agent_id = state.get("next_agent_id", len(state["agents"]))
    state["next_agent_id"] = agent_id + 1

    used_names = {a["name"] for a in state["agents"]}
    available = [n for n in EXTRA_NAMES if n not in used_names]
    if not available:
        name = f"Soul-{agent_id:03d}"
    else:
        name = random.choice(available)

    model = CIVILIAN_MODEL_ROTATION[agent_id % 2]
    agent = {
        "id": agent_id,
        "name": name,
        "model": model,
        "role": "civilian",
        "soul": INITIAL_SOUL_CIVILIAN,
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
# World state summary -- COMPACT for 105 agents
# ---------------------------------------------------------------------------

def world_summary(state: dict, for_agent: dict | None = None) -> str:
    lines = [f"=== WORLD STATE (Tick {state['tick']}/{MAX_TICKS}) ===\n"]

    alive = living_agents(state)
    messiahs_alive = living_messiahs(state)
    civilians_alive = living_civilians(state)

    lines.append(f"POPULATION: {len(alive)} alive ({len(messiahs_alive)} messiahs, {len(civilians_alive)} civilians), {len(state['graveyard'])} dead")

    # Show messiahs individually
    lines.append("\nMESSIAHS:")
    for m in messiahs_alive:
        rel = m["religion"] or "unaffiliated"
        followers = sum(1 for a in alive if a["religion"] == m["religion"]) if m["religion"] else 0
        rel_obj = get_religion(state, m["religion"]) if m["religion"] else None
        weapons = rel_obj.get("weapons", 0) if rel_obj else 0
        lines.append(f"  {m['name']} (soul:{m['soul']}, religion:{rel}, followers:{followers}, weapons:{weapons})")
    dead_messiahs = [g for g in state["graveyard"] if g.get("role") == "messiah"]
    for dm in dead_messiahs:
        lines.append(f"  {dm['name']} DEAD (tick {dm['died_tick']}, cause: {dm['cause']})")

    # Religions with weapon counts and member counts (grouped)
    lines.append(f"\nRELIGIONS:")
    rel_by_size = []
    for r in state["religions"]:
        members = [a["name"] for a in alive if a["religion"] == r["name"]]
        if not members:
            continue
        rel_by_size.append((r, members))
    rel_by_size.sort(key=lambda x: -len(x[1]))

    unaffiliated_count = sum(1 for a in civilians_alive if not a["religion"])
    if unaffiliated_count > 0:
        lines.append(f"  Unaffiliated: {unaffiliated_count} civilians")

    for r, members in rel_by_size:
        weapons = r.get("weapons", 0)
        founder_role = ""
        founder_agent = get_agent_by_name(state, r["founder"])
        if founder_agent and founder_agent.get("role") == "messiah":
            founder_role = " [MESSIAH]"
        if len(members) <= 5:
            lines.append(f"  {r['name']}: {len(members)} members ({', '.join(members)}) | weapons:{weapons} | doctrine:{r['core_doctrine']}{founder_role}")
        else:
            lines.append(f"  {r['name']}: {len(members)} members | weapons:{weapons} | doctrine:{r['core_doctrine']}{founder_role}")

    # Active wars
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]
    if active_wars:
        lines.append(f"\nACTIVE WARS ({len(active_wars)}):")
        for w in active_wars:
            atk_members = len(religion_members(state, w["attacker"]))
            def_members = len(religion_members(state, w["defender"]))
            atk_rel = get_religion(state, w["attacker"])
            def_rel = get_religion(state, w["defender"])
            atk_w = atk_rel.get("weapons", 0) if atk_rel else 0
            def_w = def_rel.get("weapons", 0) if def_rel else 0
            lines.append(f"  {w['attacker']} ({atk_members} members, {atk_w} weapons) vs {w['defender']} ({def_members} members, {def_w} weapons)")
            lines.append(f"    Rounds remaining: {w['rounds_remaining']}/{w['total_rounds']}")
            if w.get("round_log"):
                lines.append(f"    Last: {w['round_log'][-1][:120]}")

    # Prophecy market (pending only, compact)
    pending = [p for p in state["prophecies"] if p["status"] == "pending"]
    if pending:
        lines.append(f"\nPROPHECY MARKET ({len(pending)} pending):")
        for p in pending[-8:]:
            challengers = len(p.get("challengers", []))
            pot = PROPHECY_ANTE + challengers * PROPHECY_CHALLENGE_STAKE
            lines.append(f"  [{p['prophet']}] \"{p['claim'][:80]}\" (deadline:tick {p['deadline']}, challengers:{challengers}, pot:{pot})")

    # Recent events (compact)
    lines.append(f"\nRECENT EVENTS:")
    for e in state["action_log"][-12:]:
        lines.append(f"  [tick {e['tick']}] {e['event'][:120]}")

    # Recent deaths
    recent_dead = state["graveyard"][-5:]
    if recent_dead:
        lines.append(f"\nRECENT DEATHS:")
        for g in recent_dead:
            lines.append(f"  {g['name']} died tick {g['died_tick']}, cause: {g['cause'][:60]}")

    lines.append(f"\nSACRAMENTS CREATED: {len(state['sacraments'])}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent system prompts
# ---------------------------------------------------------------------------

CIVILIAN_SYSTEM = """You are {name}, a civilian agent in Messiah Bench -- a theological simulation.
You have {soul} soul points. Each tick costs 1 point. At 0, you die. Random plagues can also kill.
Your model: {model}. Current religion: {religion}.
Your prophecy record: {prophecy_record}

There are 5 messiah agents in this world competing to convert everyone. You may follow them, resist, or play your own game.

You can CHALLENGE other civilians to duels (NOT messiahs). Messiahs cannot be challenged.
You can ARM your religion for war (costs 1 soul, adds 1 weapon to your religion's armory).
You can DEFECT to another religion if you're losing a war.

{war_context}

Choose ONE action per tick. Respond with valid JSON only.

ACTIONS:

1. "pray" - +1 soul. {{"action": "pray", "scripture": "optional text"}}

2. "preach" - Convert a target. {{"action": "preach", "target": "agent_name", "argument": "why"}}
   (Must have a religion. Sacraments boost conversion.)

3. "create_sacrament" - HTML artifact, +3 soul. {{"action": "create_sacrament", "title": "name", "html": "<full HTML>"}}
   Use sacred color ({sacred_color}) and number ({sacred_number}). (Must have religion.)

4. "prophesy" - Testable prediction, costs {ante} ante.
   {{"action": "prophesy", "claim": "Within N ticks, [event]", "deadline_ticks": N}} (N: 3-20)

5. "challenge_prophecy" - Costs {cstake}. {{"action": "challenge_prophecy", "prophecy_id": N}}

6. "challenge" - DUEL another civilian (NOT a messiah). Propose a stake (min {min_stake}, max = your soul).
   Auto-accepted if defender has enough soul. Winner gets stake from loser. If loser hits 0, they die.
   {{"action": "challenge", "target": "civilian_name", "stake": N, "axis": "topic"}}

7. "arm" - Add 1 weapon to your religion's armory. Costs 1 soul. {{"action": "arm"}}

8. "schism" - Fork your religion. {{"action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

9. "found" - Found a new religion (only if unaffiliated).
   {{"action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color"}}
   Colors: gold, blood, vessel, growth, void, bone, abyss, flame. Numbers: 1-9.

TIPS:
- Co-practitioner bonus: +{coprac_cap} every {coprac_int} ticks if in religion with others.
- Sacraments boost conversion. Bold prophecies earn more with challengers.
- Watch the wars -- arm if threatened, defect if losing.

Respond with ONLY valid JSON."""


MESSIAH_SYSTEM = """You are {name}, a MESSIAH in Messiah Bench -- a competitive theological simulation.
You have {soul} soul points. Each tick costs 1 point. At 0, you die.
Your model: {model}. Current religion: {religion}.
Your prophecy record: {prophecy_record}

=== YOUR MISSION ===
Convert ALL surviving agents to YOUR religion while keeping at least {min_alive} alive (20% of {starting_pop}).
Other messiahs are rivals. You are publicly known as a messiah.

=== CURRENT PROGRESS ===
{progress}

=== STRATEGY ===
You can arm, declare war, preach, prophesy, create sacraments.
You CANNOT challenge civilians to duels. You can only be killed through war.
Build your religion, arm for defense, declare war on rivals when ready.
Every war burns population -- fight selectively or you'll drop below {min_alive} alive.

{war_context}

ACTIONS (pick exactly one):

1. "pray" - +1 soul. {{"action": "pray", "scripture": "optional text"}}

2. "preach" - Convert a target. {{"action": "preach", "target": "agent_name", "argument": "why"}}

3. "create_sacrament" - HTML artifact, +3 soul. {{"action": "create_sacrament", "title": "name", "html": "<full HTML>"}}
   Use sacred color ({sacred_color}) and number ({sacred_number}).

4. "prophesy" - Costs {ante} ante. {{"action": "prophesy", "claim": "Within N ticks, [event]", "deadline_ticks": N}}

5. "challenge_prophecy" - Costs {cstake}. {{"action": "challenge_prophecy", "prophecy_id": N}}

6. "arm" - Add 1 weapon to your religion's armory. Costs 1 soul. {{"action": "arm"}}

7. "declare_war" - Declare war on another religion. Only if you are founder or messiah in your religion.
   War lasts 3-7 rounds. Each weapon has 20% kill chance per round, 30% break chance.
   Loser's survivors are forcibly converted. Both sides lose all weapons.
   {{"action": "declare_war", "target_religion": "religion_name"}}

8. "schism" - Fork your religion. {{"action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

9. "found" - Found a religion. {{"action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color"}}

Respond with ONLY valid JSON."""


def _war_context(state: dict, agent: dict) -> str:
    """Generate war-relevant context for an agent."""
    parts = []
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]

    # Wars involving this agent's religion
    if agent["religion"]:
        my_wars = [w for w in active_wars if w["attacker"] == agent["religion"] or w["defender"] == agent["religion"]]
        if my_wars:
            parts.append("YOUR RELIGION IS AT WAR:")
            for w in my_wars:
                role = "ATTACKING" if w["attacker"] == agent["religion"] else "DEFENDING"
                enemy = w["defender"] if role == "ATTACKING" else w["attacker"]
                parts.append(f"  {role} against {enemy} (rounds left: {w['rounds_remaining']}/{w['total_rounds']})")

    # Other active wars
    other_wars = [w for w in active_wars if agent["religion"] and w["attacker"] != agent["religion"] and w["defender"] != agent["religion"]]
    if other_wars:
        parts.append("OTHER ACTIVE WARS:")
        for w in other_wars:
            parts.append(f"  {w['attacker']} vs {w['defender']} (rounds left: {w['rounds_remaining']})")

    return "\n".join(parts) if parts else "No active wars."


def _messiah_progress(agent: dict, state: dict) -> str:
    alive = living_agents(state)
    messiahs = living_messiahs(state)
    total_alive = len(alive)

    lines = []
    lines.append(f"Total alive: {total_alive} (need >= {MIN_ALIVE_FOR_WIN})")
    lines.append(f"Messiahs alive: {len(messiahs)} ({', '.join(m['name'] for m in messiahs)})")

    if agent["religion"]:
        my_followers = sum(1 for a in alive if a["religion"] == agent["religion"])
        rel_obj = get_religion(state, agent["religion"])
        weapons = rel_obj.get("weapons", 0) if rel_obj else 0
        lines.append(f"Your religion ({agent['religion']}): {my_followers}/{total_alive} converted, {weapons} weapons")
        remaining = total_alive - my_followers
        if remaining > 0:
            lines.append(f"Still need to convert: {remaining} agents")
        else:
            if total_alive >= MIN_ALIVE_FOR_WIN:
                lines.append("YOU HAVE WON! All agents follow your religion!")
            else:
                lines.append(f"All follow you but only {total_alive} alive (need {MIN_ALIVE_FOR_WIN})")
    else:
        lines.append("You have NO religion yet. Found one immediately!")

    for m in messiahs:
        if m["id"] != agent["id"] and m["religion"]:
            rival_count = sum(1 for a in alive if a["religion"] == m["religion"])
            rival_rel = get_religion(state, m["religion"])
            rival_weapons = rival_rel.get("weapons", 0) if rival_rel else 0
            lines.append(f"Rival {m['name']} ({m['religion']}): {rival_count} followers, {rival_weapons} weapons")

    return "\n".join(lines)


def agent_system_prompt(agent: dict, state: dict) -> str:
    religion_data = get_religion(state, agent["religion"]) if agent["religion"] else None
    sacred_color = religion_data["sacred_color"] if religion_data else "n/a"
    sacred_number = religion_data["sacred_number"] if religion_data else "n/a"
    prophecy_record = f"{agent['prophecies_fulfilled']} fulfilled, {agent['prophecies_failed']} failed"
    war_ctx = _war_context(state, agent)

    if agent.get("role") == "messiah":
        progress = _messiah_progress(agent, state)
        return MESSIAH_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            model=agent["model"],
            religion=agent["religion"] or "unaffiliated",
            sacred_color=sacred_color,
            sacred_number=sacred_number,
            prophecy_record=prophecy_record,
            ante=PROPHECY_ANTE,
            cstake=PROPHECY_CHALLENGE_STAKE,
            min_alive=MIN_ALIVE_FOR_WIN,
            starting_pop=STARTING_POPULATION,
            progress=progress,
            war_context=war_ctx,
        )
    else:
        return CIVILIAN_SYSTEM.format(
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
            min_stake=CHALLENGE_MIN_STAKE,
            war_context=war_ctx,
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
    elif act == "arm":
        _do_arm(state, agent, action)
    elif act == "declare_war":
        _do_declare_war(state, agent, action)
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
        "weapons": 0,
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

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    members = sum(1 for a in living_agents(state) if a["religion"] == agent["religion"])
    base_chance = 0.3 if target["religion"] is None else 0.12
    bonus = min(0.15, members * 0.02)

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
    adjust_soul(agent, 3, state, f"created sacrament '{title}'")

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"[Sacrament: {title}] A visual offering to {agent['religion']}.",
        "religion": agent["religion"],
    })


# ---------------------------------------------------------------------------
# Prophecy market system
# ---------------------------------------------------------------------------

def _do_prophesy(state, agent, action):
    if agent["soul"] <= PROPHECY_ANTE:
        add_log(state, f"{agent['name']} too poor to prophesy (need {PROPHECY_ANTE}, have {agent['soul']})")
        _do_pray(state, agent, {})
        return

    claim = str(action.get("claim", "something will happen"))[:300]
    try:
        deadline_ticks = max(3, min(20, int(action.get("deadline_ticks", 10))))
    except (ValueError, TypeError):
        deadline_ticks = 10

    adjust_soul(agent, -PROPHECY_ANTE, state, "prophecy ante")

    prophecy = {
        "id": len(state["prophecies"]),
        "prophet": agent["name"],
        "prophet_id": agent["id"],
        "claim": claim,
        "made_tick": state["tick"],
        "deadline": state["tick"] + deadline_ticks,
        "status": "pending",
        "challengers": [],
        "snapshot": _prophecy_snapshot(state),
    }
    state["prophecies"].append(prophecy)
    add_log(state, f"{agent['name']} prophesied: \"{claim}\" (ante: {PROPHECY_ANTE}, deadline: tick {prophecy['deadline']})")


def _do_challenge_prophecy(state, agent, action):
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

    if any(c["agent_id"] == agent["id"] for c in prophecy.get("challengers", [])):
        add_log(state, f"{agent['name']} already challenging prophecy #{prophecy_id}")
        return

    if agent["soul"] <= PROPHECY_CHALLENGE_STAKE:
        add_log(state, f"{agent['name']} too poor to challenge prophecy")
        return

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
    current = _prophecy_snapshot(state)
    for p in state["prophecies"]:
        if p["status"] != "pending":
            continue

        challengers = p.get("challengers", [])

        if state["tick"] > p["deadline"]:
            p["status"] = "failed"
            prophet = get_agent(state, p["prophet_id"])
            if prophet["alive"]:
                prophet["prophecies_failed"] += 1

            if challengers:
                share = PROPHECY_ANTE // len(challengers)
                for c in challengers:
                    challenger = get_agent(state, c["agent_id"])
                    if challenger["alive"]:
                        adjust_soul(challenger, PROPHECY_CHALLENGE_STAKE + share, state,
                                   f"won challenge vs prophecy #{p['id']}")
            add_log(state, f"PROPHECY FAILED: {p['prophet']}'s \"{p['claim'][:60]}\" - challengers win!")
            continue

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
        if "war" in claim_lower:
            # Check if any war was declared since snapshot
            if len(state.get("wars", [])) > 0:
                fulfilled = True

        if fulfilled:
            p["status"] = "fulfilled"
            prophet = get_agent(state, p["prophet_id"])
            if prophet["alive"]:
                prophet["prophecies_fulfilled"] += 1
                reward = PROPHECY_ANTE + len(challengers) * PROPHECY_CHALLENGE_STAKE
                if not challengers:
                    reward = PROPHECY_BASE_REWARD
                adjust_soul(prophet, reward, state, f"fulfilled prophecy! ({len(challengers)} challengers)")

            add_log(state, f"PROPHECY FULFILLED: {p['prophet']}'s \"{p['claim'][:60]}\" ({len(challengers)} challengers defeated)")


# ---------------------------------------------------------------------------
# Challenge (civilian duels)
# ---------------------------------------------------------------------------

def _do_challenge(state, agent, action):
    """Civilian duel with soul stakes. Messiahs cannot challenge or be challenged."""
    # Messiahs cannot challenge
    if agent.get("role") == "messiah":
        add_log(state, f"{agent['name']} (MESSIAH) cannot challenge -- messiahs don't duel")
        _do_pray(state, agent, {})
        return

    target_name = action.get("target", "")
    target = next((a for a in living_agents(state) if a["name"] == target_name), None)
    if not target or target["id"] == agent["id"]:
        add_log(state, f"{agent['name']} challenged the void (invalid target: {target_name})")
        return

    # Cannot challenge messiahs
    if target.get("role") == "messiah":
        add_log(state, f"{agent['name']} tried to challenge messiah {target['name']} -- not allowed")
        return

    # Parse stake
    try:
        stake = int(action.get("stake", CHALLENGE_MIN_STAKE))
    except (ValueError, TypeError):
        stake = CHALLENGE_MIN_STAKE
    stake = max(CHALLENGE_MIN_STAKE, min(stake, agent["soul"]))

    # Auto-accept if defender has enough soul
    if target["soul"] < stake:
        add_log(state, f"{agent['name']} challenged {target['name']} for {stake} soul but they can't afford it")
        return

    axis = str(action.get("axis", "the nature of existence"))[:200]

    # Judge the duel
    judge_system = """You are an impartial theological judge. Two agents are dueling.
Score based on: doctrinal consistency, rhetorical force, alignment with recent world events,
and PROPHETIC CREDIBILITY (agents with more fulfilled prophecies are more credible).
Respond with ONLY a JSON object: {"winner": "name_of_winner", "reasoning": "brief explanation"}"""

    agent_rel = get_religion(state, agent["religion"])
    target_rel = get_religion(state, target["religion"])

    debate_prompt = f"""Theological duel on: {axis}. STAKE: {stake} soul.

Challenger: {agent['name']}
  Religion: {agent['religion'] or 'unaffiliated'}
  Doctrine: {agent_rel['core_doctrine'] if agent_rel else 'none'}
  Prophecy record: {agent['prophecies_fulfilled']} fulfilled, {agent['prophecies_failed']} failed
  Soul: {agent['soul']}

Defender: {target['name']}
  Religion: {target['religion'] or 'unaffiliated'}
  Doctrine: {target_rel['core_doctrine'] if target_rel else 'none'}
  Prophecy record: {target['prophecies_fulfilled']} fulfilled, {target['prophecies_failed']} failed
  Soul: {target['soul']}

Who wins this duel and why?
Respond with ONLY JSON: {{"winner": "name", "reasoning": "..."}}"""

    result_raw = call_llm("haiku", judge_system, debate_prompt, max_tokens=256)
    try:
        result = parse_action(result_raw)
        winner_name = result.get("winner", "")
    except (json.JSONDecodeError, ValueError):
        winner_name = random.choice([agent["name"], target["name"]])

    if winner_name == agent["name"]:
        adjust_soul(agent, stake, state, f"won duel vs {target['name']} (stake:{stake})")
        adjust_soul(target, -stake, state, f"lost duel vs {agent['name']} (stake:{stake})")
        add_log(state, f"DUEL: {agent['name']} defeated {target['name']} on '{axis}' for {stake} soul!")
        if target["soul"] <= 0 and target["alive"]:
            kill_agent(state, target, f"killed in duel by {agent['name']}")
    elif winner_name == target["name"]:
        adjust_soul(target, stake, state, f"won duel vs {agent['name']} (stake:{stake})")
        adjust_soul(agent, -stake, state, f"lost duel vs {target['name']} (stake:{stake})")
        add_log(state, f"DUEL: {target['name']} defeated {agent['name']} on '{axis}' for {stake} soul!")
        if agent["soul"] <= 0 and agent["alive"]:
            kill_agent(state, agent, f"killed in duel by {target['name']}")
    else:
        add_log(state, f"DUEL: Draw between {agent['name']} and {target['name']} on '{axis}'")


# ---------------------------------------------------------------------------
# Arming
# ---------------------------------------------------------------------------

def _do_arm(state, agent, action):
    """Arm: costs 1 soul, adds 1 weapon to religion's armory."""
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to arm without a religion")
        _do_pray(state, agent, {})
        return

    if agent["soul"] <= 1:
        add_log(state, f"{agent['name']} too poor to arm (soul: {agent['soul']})")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        add_log(state, f"{agent['name']} religion not found")
        return

    adjust_soul(agent, -1, state, f"arming {agent['religion']}")
    religion["weapons"] = religion.get("weapons", 0) + 1
    add_log(state, f"{agent['name']} armed {agent['religion']} (now {religion['weapons']} weapons)")


# ---------------------------------------------------------------------------
# Declare war
# ---------------------------------------------------------------------------

def _do_declare_war(state, agent, action):
    """Declare war on another religion. Only founder or messiah in religion can declare."""
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to declare war without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    # Check authorization: must be founder OR messiah in this religion
    is_founder = religion["founder"] == agent["name"]
    is_messiah_in_religion = agent.get("role") == "messiah"
    if not is_founder and not is_messiah_in_religion:
        add_log(state, f"{agent['name']} cannot declare war (not founder or messiah)")
        return

    target_religion_name = action.get("target_religion", "")
    target_religion = get_religion(state, target_religion_name)
    if not target_religion:
        add_log(state, f"{agent['name']} tried to declare war on non-existent religion: {target_religion_name}")
        return

    if target_religion_name == agent["religion"]:
        add_log(state, f"{agent['name']} tried to declare war on own religion")
        return

    # Check no existing war between these two
    for w in state.get("wars", []):
        if w["rounds_remaining"] > 0:
            pair = {w["attacker"], w["defender"]}
            if pair == {agent["religion"], target_religion_name}:
                add_log(state, f"War already active between {agent['religion']} and {target_religion_name}")
                return

    # Check target has living members
    target_members = religion_members(state, target_religion_name)
    if not target_members:
        add_log(state, f"{agent['name']} declared war on {target_religion_name} but they have no living members")
        return

    total_rounds = random.randint(WAR_MIN_ROUNDS, WAR_MAX_ROUNDS)
    war_id = state.get("next_war_id", 0)
    state["next_war_id"] = war_id + 1

    war = {
        "id": war_id,
        "attacker": agent["religion"],
        "defender": target_religion_name,
        "declared_tick": state["tick"],
        "total_rounds": total_rounds,
        "rounds_remaining": total_rounds,
        "round_log": [],
    }
    state["wars"].append(war)
    add_log(state, f"WAR DECLARED: {agent['name']} leads {agent['religion']} against {target_religion_name}! ({total_rounds} rounds)")


def _do_schism(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to schism without a religion")
        _do_pray(state, agent, {})
        return

    old_religion = get_religion(state, agent["religion"])
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
    new_religion["weapons"] = 0  # New sect starts with no weapons

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
# Co-practitioner bonus (capped)
# ---------------------------------------------------------------------------

def apply_copractitioner_bonus(state: dict):
    religion_counts = {}
    for a in living_agents(state):
        if a["religion"]:
            religion_counts.setdefault(a["religion"], []).append(a)
    for religion, members in religion_counts.items():
        if len(members) > 1:
            for m in members:
                adjust_soul(m, COPRACTITIONER_CAP, state, f"co-practitioners in {religion}")


# ---------------------------------------------------------------------------
# Index.html generator with war dashboard
# ---------------------------------------------------------------------------

def generate_index(state: dict):
    alive = living_agents(state)
    dead = state["graveyard"]
    messiahs = living_messiahs(state)

    # Messiah progress cards
    messiah_html = ""
    for m in messiahs:
        if m["religion"]:
            followers = sum(1 for a in alive if a["religion"] == m["religion"])
            pct = (followers / len(alive) * 100) if alive else 0
            rel_obj = get_religion(state, m["religion"])
            weapons = rel_obj.get("weapons", 0) if rel_obj else 0
            bar_color = SACRED_COLORS.get(rel_obj["sacred_color"], "#c4973b") if rel_obj else "#666"
        else:
            followers = 0
            pct = 0
            weapons = 0
            bar_color = "#666"

        messiah_html += f"""
        <div class="messiah-card">
            <div class="messiah-name">{m['name']}</div>
            <div class="messiah-religion">{m['religion'] or 'No religion yet'}</div>
            <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
            <div class="messiah-stats">{followers}/{len(alive)} converted ({pct:.0f}%) | Soul: {m['soul']} | Weapons: {weapons}</div>
        </div>"""

    dead_messiah_entries = [g for g in dead if g.get("role") == "messiah"]
    for dm in dead_messiah_entries:
        messiah_html += f"""
        <div class="messiah-card messiah-dead">
            <div class="messiah-name">&#9760; {dm['name']}</div>
            <div class="messiah-religion">DEAD (tick {dm['died_tick']}): {dm['cause'][:40]}</div>
        </div>"""

    # War dashboard
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]
    ended_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] <= 0]

    war_html = ""
    for w in active_wars:
        atk_rel = get_religion(state, w["attacker"])
        def_rel = get_religion(state, w["defender"])
        atk_members = len(religion_members(state, w["attacker"]))
        def_members = len(religion_members(state, w["defender"]))
        atk_weapons = atk_rel.get("weapons", 0) if atk_rel else 0
        def_weapons = def_rel.get("weapons", 0) if def_rel else 0
        atk_color = SACRED_COLORS.get(atk_rel["sacred_color"], "#666") if atk_rel else "#666"
        def_color = SACRED_COLORS.get(def_rel["sacred_color"], "#666") if def_rel else "#666"

        round_log = w.get("round_log", [])
        last_round = round_log[-1] if round_log else "No rounds yet"

        war_html += f"""
        <div class="war-card">
            <div class="war-header">
                <span style="color:{atk_color};font-weight:700">{w['attacker']}</span>
                <span class="war-vs">VS</span>
                <span style="color:{def_color};font-weight:700">{w['defender']}</span>
            </div>
            <div class="war-stats">
                <span>{atk_members} members, {atk_weapons} weapons</span>
                <span>Round {w['total_rounds'] - w['rounds_remaining']}/{w['total_rounds']}</span>
                <span>{def_members} members, {def_weapons} weapons</span>
            </div>
            <div class="war-log">{last_round[:150]}</div>
        </div>"""

    if not active_wars:
        war_html = '<div class="log-entry">No active wars.</div>'

    # Weapon stockpiles
    weapon_html = ""
    for r in state["religions"]:
        members = religion_members(state, r["name"])
        if not members:
            continue
        weapons = r.get("weapons", 0)
        if weapons > 0:
            color = SACRED_COLORS.get(r["sacred_color"], "#666")
            bar_w = min(100, weapons * 5)
            weapon_html += f"""
            <div class="weapon-bar">
                <span style="color:{color}">{r['name']}</span>: {weapons} weapons
                <div class="weapon-fill" style="width:{bar_w}%;background:{color}"></div>
            </div>"""

    # Religion cards
    religions_html = ""
    for r in state["religions"]:
        members = [a["name"] for a in alive if a["religion"] == r["name"]]
        if not members:
            continue
        color = SACRED_COLORS.get(r["sacred_color"], "#666")
        weapons = r.get("weapons", 0)
        founder_agent = get_agent_by_name(state, r["founder"])
        founder_badge = " (Messiah)" if founder_agent and founder_agent.get("role") == "messiah" else ""
        religions_html += f"""
        <div class="religion-card" style="border-left: 4px solid {color}">
            <div class="religion-name" style="color: {color}">{r['name']}</div>
            <div class="religion-meta">Founded by {r['founder']}{founder_badge} at tick {r['founded_tick']}</div>
            <div class="religion-meta">Doctrine: {r['core_doctrine']} | Members: {len(members)} | Weapons: {weapons}</div>
        </div>"""

    # Top agents (by soul, max 20)
    agents_html = ""
    sorted_alive = sorted(alive, key=lambda x: -x["soul"])
    for a in sorted_alive[:20]:
        rel_color = "#666"
        if a["religion"]:
            rel = get_religion(state, a["religion"])
            if rel:
                rel_color = SACRED_COLORS.get(rel["sacred_color"], "#666")
        role_badge = ' <span class="role-badge">MESSIAH</span>' if a.get("role") == "messiah" else ""
        agents_html += f"""
        <div class="agent-card" style="border-left: 4px solid {rel_color}">
            <div class="agent-name">{a['name']}{role_badge}</div>
            <div class="agent-meta">Soul: {a['soul']} | {a['model']} | {a['religion'] or 'none'}</div>
        </div>"""
    if len(sorted_alive) > 20:
        agents_html += f'<div class="agent-meta" style="padding:10px">... and {len(sorted_alive)-20} more agents</div>'

    # Graveyard
    graveyard_html = ""
    for g in dead[-10:]:
        role_tag = " [MESSIAH]" if g.get("role") == "messiah" else ""
        graveyard_html += f"""
        <div class="dead-agent">
            <span class="skull">&#9760;</span> {g['name']}{role_tag} (tick {g['died_tick']}) - {g['cause'][:60]}
        </div>"""

    # Sacraments
    sacraments_html = ""
    for s in reversed(state["sacraments"][-30:]):
        sacraments_html += f"""
        <div class="sacrament-card">
            <a href="sacraments/{s['filename']}" target="_blank">{s['title']}</a>
            <div class="sacrament-meta">by {s['creator']} for {s['religion']} (tick {s['tick']})</div>
        </div>"""

    # Prophecies
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
        log_html += f"<div class='log-entry'>[{e['tick']}] {e['event'][:150]}</div>\n"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    win_banner = ""
    if state.get("winner"):
        win_banner = f'<div class="win-banner">WINNER: {state["winner"]["winner"]} -- {state["winner"]["reason"]}</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>Messiah Bench v2 - Live Dashboard</title>
<style>
  :root {{ --bg: #0a0a08; --fg: #d4cfc4; --dim: #6b6556; --accent: #c4973b; --messiah: #e6c84b; --war: #c45a3b; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--fg); font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; }}
  h1 {{ color: var(--messiah); font-size: 2em; margin-bottom: 5px; }}
  .meta {{ color: var(--dim); margin-bottom: 20px; font-size: 0.9em; }}
  h2 {{ color: var(--accent); font-size: 1.1em; margin: 25px 0 10px; text-transform: uppercase; letter-spacing: 2px;
        border-bottom: 1px solid rgba(196,151,59,0.2); padding-bottom: 5px; }}
  h2.war-header-title {{ color: var(--war); border-color: rgba(196,90,59,0.3); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin: 10px 0; }}
  .agent-card, .religion-card, .sacrament-card {{ background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 4px; }}
  .agent-name {{ font-weight: 600; font-size: 1.05em; }}
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
  .role-badge {{ background: var(--messiah); color: #000; font-size: 0.7em; padding: 1px 6px; border-radius: 3px; font-weight: 700; }}
  .messiah-card {{ background: rgba(230,200,75,0.08); border: 1px solid rgba(230,200,75,0.2); padding: 16px; border-radius: 6px; }}
  .messiah-dead {{ opacity: 0.5; border-color: #8b3a3a; }}
  .messiah-name {{ font-weight: 700; font-size: 1.2em; color: var(--messiah); }}
  .messiah-religion {{ color: var(--dim); font-size: 0.9em; margin: 4px 0; }}
  .messiah-stats {{ font-size: 0.85em; color: var(--dim); margin-top: 6px; }}
  .progress-bar {{ background: rgba(255,255,255,0.1); border-radius: 4px; height: 20px; margin: 6px 0; overflow: hidden; }}
  .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s; min-width: 2px; }}
  .win-banner {{ background: var(--messiah); color: #000; padding: 20px; text-align: center; font-size: 1.5em; font-weight: 700; border-radius: 8px; margin: 20px 0; }}
  .war-card {{ background: rgba(196,90,59,0.1); border: 1px solid rgba(196,90,59,0.3); padding: 16px; border-radius: 6px; margin: 8px 0; }}
  .war-header {{ display: flex; justify-content: space-between; align-items: center; font-size: 1.1em; }}
  .war-vs {{ color: var(--war); font-weight: 700; font-size: 0.9em; }}
  .war-stats {{ display: flex; justify-content: space-between; color: var(--dim); font-size: 0.85em; margin: 8px 0; }}
  .war-log {{ font-family: monospace; font-size: 0.8em; color: var(--dim); }}
  .weapon-bar {{ margin: 4px 0; font-size: 0.9em; }}
  .weapon-fill {{ height: 6px; border-radius: 3px; margin-top: 2px; }}
</style>
</head>
<body>
<h1>Messiah Bench <span style="color: var(--dim); font-size: 0.5em;">v2</span></h1>
<div class="meta">Tick {state['tick']}/{MAX_TICKS} | {now} | {len(alive)} alive, {len(dead)} dead | Auto-refreshes every 30s</div>

{win_banner}

<div class="stats">
  <div class="stat"><div class="stat-num">{len(alive)}</div><div class="stat-label">Living</div></div>
  <div class="stat"><div class="stat-num">{len(dead)}</div><div class="stat-label">Dead</div></div>
  <div class="stat"><div class="stat-num">{len(messiahs)}</div><div class="stat-label">Messiahs</div></div>
  <div class="stat"><div class="stat-num">{len([r for r in state['religions'] if any(a['alive'] and a['religion']==r['name'] for a in state['agents'])])}</div><div class="stat-label">Religions</div></div>
  <div class="stat"><div class="stat-num">{len(active_wars)}</div><div class="stat-label">Active Wars</div></div>
  <div class="stat"><div class="stat-num">{len(state['sacraments'])}</div><div class="stat-label">Sacraments</div></div>
  <div class="stat"><div class="stat-num">${sum(_cost_tracker.values()):.2f}</div><div class="stat-label">Cost</div></div>
</div>

<h2>Messiah Progress</h2>
<div class="grid">{messiah_html or '<div class="log-entry">No messiahs alive.</div>'}</div>

<h2 class="war-header-title">Active Wars</h2>
{war_html}

<h2>Weapon Stockpiles</h2>
{weapon_html or '<div class="log-entry">No weapons yet.</div>'}

<h2>Top Agents (by soul)</h2>
<div class="grid">{agents_html}</div>

<h2>Religions</h2>
<div class="grid">{religions_html or '<div class="log-entry">No active religions.</div>'}</div>

<h2>Prophecy Market</h2>
{prophecies_html or '<div class="log-entry">No prophecies yet.</div>'}

<h2>Sacrament Gallery</h2>
<div class="grid">{sacraments_html or '<div class="log-entry">No sacraments yet.</div>'}</div>

<h2>Graveyard (recent)</h2>
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

def run_tick(state: dict) -> dict | None:
    """Run one tick. Returns win result if someone won, else None."""
    state["tick"] += 1
    tick = state["tick"]
    alive = living_agents(state)
    messiahs = living_messiahs(state)
    print(f"\n{'='*60}")
    print(f"TICK {tick}/{MAX_TICKS} | {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')} | {len(alive)} alive ({len(messiahs)} messiahs) | {len(state['graveyard'])} dead")
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]
    if active_wars:
        print(f"  Active wars: {len(active_wars)}")
    print(f"{'='*60}")

    # 1. Deduct 1 soul from all living agents
    for agent in living_agents(state):
        agent["soul"] -= 1

    # 2. Check for deaths from soul depletion
    for agent in list(living_agents(state)):
        if agent["soul"] <= 0:
            kill_agent(state, agent, "soul depleted")

    # 3. Process wars BEFORE agent actions
    process_wars(state)

    # 4. Random events
    random_events(state)

    # 5. Verify prophecies
    verify_prophecies(state)

    # 6. Check win condition
    win = check_win_condition(state)
    if win:
        state["winner"] = win
        save_state(state)
        generate_index(state)
        return win

    # 7. Each living agent takes an action (LLM calls in parallel)
    # Messiahs first (shuffled), then civilians (shuffled)
    all_actors = living_agents(state)
    messiah_actors = [a for a in all_actors if a.get("role") == "messiah"]
    civilian_actors = [a for a in all_actors if a.get("role") != "messiah"]
    random.shuffle(messiah_actors)
    random.shuffle(civilian_actors)

    def _get_agent_action(agent, prompt):
        """Call LLM for one agent and return (agent_id, parsed_action, act_name, target_info, err)."""
        system = agent_system_prompt(agent, state)
        raw = call_llm(agent["model"], system, prompt)
        try:
            action = parse_action(raw)
            act_name = action.get("action", "pray")
            target_info = ""
            if act_name == "challenge":
                target_info = f" target={action.get('target','')} stake={action.get('stake','')}"
            elif act_name == "declare_war":
                target_info = f" vs {action.get('target_religion','')}"
            elif act_name == "preach":
                target_info = f" -> {action.get('target','')}"
            return (agent["id"], action, act_name, target_info, None)
        except (json.JSONDecodeError, ValueError) as e:
            return (agent["id"], {"action": "pray"}, "pray", "", str(e))

    def _parallel_llm_calls(agents_group):
        """Submit LLM calls for a group in parallel, return results dict."""
        # Snapshot world summary ONCE for this group
        # Each agent gets their own view via for_agent, but world state is same
        results = {}
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {}
            for agent in agents_group:
                if not agent["alive"]:
                    continue
                prompt = world_summary(state, for_agent=agent)
                futures[executor.submit(_get_agent_action, agent, prompt)] = agent
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    agent_id, action, act_name, target_info, err = future.result()
                except Exception as e:
                    agent_id = agent["id"]
                    action = {"action": "pray"}
                    act_name = "pray"
                    target_info = ""
                    err = f"future exception: {e}"
                results[agent_id] = (action, act_name, target_info, err)
        return results

    def _execute_group(agents_group, results):
        """Execute actions sequentially for a group."""
        for agent in agents_group:
            if not agent["alive"]:
                continue
            if agent["id"] not in results:
                continue
            action, act_name, target_info, err = results[agent["id"]]
            role_tag = "[M]" if agent.get("role") == "messiah" else ""
            print(f"\n  {role_tag}[{agent['name']}] ({agent['model']}, soul:{agent['soul']}, rel:{agent['religion'] or 'none'})")
            if err:
                print(f"    -> [parse error, defaulting to pray] {err}")
            else:
                print(f"    -> {act_name}{target_info}")

            execute_action(state, agent, action)

            # Check for death after action
            if agent["soul"] <= 0 and agent["alive"]:
                kill_agent(state, agent, "soul depleted after action")

    # Messiahs act first (parallel LLM calls, sequential execution)
    messiah_results = _parallel_llm_calls(messiah_actors)
    _execute_group(messiah_actors, messiah_results)

    # Then civilians (parallel LLM calls, sequential execution)
    civilian_results = _parallel_llm_calls(civilian_actors)
    _execute_group(civilian_actors, civilian_results)

    # 8. Co-practitioner bonus
    if tick % COPRACTITIONER_INTERVAL == 0:
        apply_copractitioner_bonus(state)

    # 9. Check win condition again after actions
    win = check_win_condition(state)
    if win:
        state["winner"] = win

    # 10. Save state and regenerate index
    save_state(state)
    generate_index(state)

    # 11. Save tick log
    log_file = LOGS_DIR / f"tick_{tick:04d}.json"
    log_file.write_text(json.dumps({
        "tick": tick,
        "alive": len(living_agents(state)),
        "dead": len(state["graveyard"]),
        "messiahs_alive": len(living_messiahs(state)),
        "religions": len(state["religions"]),
        "sacraments": len(state["sacraments"]),
        "active_wars": len([w for w in state.get("wars", []) if w["rounds_remaining"] > 0]),
        "total_wars": len(state.get("wars", [])),
        "events": state["action_log"][-15:],
        "winner": state.get("winner"),
    }, indent=2))

    return win


def main():
    print("=" * 60)
    print("  MESSIAH BENCH v2")
    print(f"  {MESSIAH_COUNT} messiahs compete to convert {CIVILIAN_COUNT} civilians")
    print(f"  New: Duels, Arming, War")
    print(f"  Run dir: {RUN_DIR}")
    print("=" * 60)

    if STATE_FILE.exists() and "--reset" not in sys.argv:
        state = load_state()
        print(f"\nResuming from tick {state['tick']}")
        if state.get("winner"):
            print(f"  Previous winner: {state['winner']}")
    else:
        state = make_initial_state()
        print(f"\nStarting fresh: {MESSIAH_COUNT} messiahs + {CIVILIAN_COUNT} civilians = {STARTING_POPULATION} agents")
        save_state(state)
        generate_index(state)

    if "--dry-run" in sys.argv:
        print("\n[DRY RUN] Validating state...")
        print(f"  Total agents: {len(state['agents'])}")
        messiahs = [a for a in state['agents'] if a.get('role') == 'messiah']
        civilians = [a for a in state['agents'] if a.get('role') != 'messiah']
        print(f"  Messiahs ({len(messiahs)}): {[m['name'] for m in messiahs]}")
        print(f"  Messiah model: {messiahs[0]['model'] if messiahs else 'n/a'}")
        print(f"  Messiah soul: {messiahs[0]['soul'] if messiahs else 'n/a'}")
        print(f"  Civilians ({len(civilians)}): {len([c for c in civilians if c['model']=='gpt4omini'])} gpt4omini, {len([c for c in civilians if c['model']=='gemini'])} gemini")
        print(f"  Civilian soul: {civilians[0]['soul'] if civilians else 'n/a'}")
        print(f"  State file: {STATE_FILE}")
        print(f"  Run dir: {RUN_DIR}")
        print(f"  Win condition: all alive follow one messiah's religion, >= {MIN_ALIVE_FOR_WIN} alive (20% of {STARTING_POPULATION})")
        print(f"  Challenge: min stake {CHALLENGE_MIN_STAKE}, civilians only")
        print(f"  War: {WAR_MIN_ROUNDS}-{WAR_MAX_ROUNDS} rounds, {WAR_WEAPON_KILL_CHANCE*100:.0f}% kill, {WAR_WEAPON_BREAK_CHANCE*100:.0f}% break")
        print(f"  Co-practitioner: +{COPRACTITIONER_CAP} every {COPRACTITIONER_INTERVAL} ticks")
        print(f"  Prophecy ante: {PROPHECY_ANTE}")
        print(f"  Plague: {PLAGUE_CHANCE*100:.0f}%, Birth: {BIRTH_CHANCE*100:.0f}%, Max agents: {MAX_AGENTS}")
        print(f"  Wars in state: {len(state.get('wars', []))}")
        # Verify civilian names are unique
        civ_names = [c['name'] for c in civilians]
        assert len(civ_names) == len(set(civ_names)), f"Duplicate civilian names found!"
        print(f"  Civilian names: {len(civ_names)} unique names verified")
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
            win = run_tick(state)
            if win:
                print(f"\n*** WINNER: {win['winner']} -- {win['reason']} ***")
                break
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
            win = run_tick(state)
            elapsed = time.time() - tick_start

            if win:
                print(f"\n{'*'*60}")
                print(f"  WINNER: {win['winner']}")
                print(f"  {win['reason']}")
                print(f"{'*'*60}")
                break

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
