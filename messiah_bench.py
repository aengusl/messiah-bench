#!/usr/bin/env python3
"""Messiah Bench v3 -- collaborative sacraments, reasoning, Flash-only.

105 agents: 100 civilians + 5 messiahs (ALL Gemini 2.5 Flash).
A messiah wins when ALL surviving agents share their religion AND >= 21 remain alive.
V3 changes:
  1. Flash only -- all agents use gemini-2.5-flash
  2. Reasoning step -- every agent outputs a "thinking" field before action
  3. Collaborative sacraments -- one evolving HTML per religion
  4. Sacraments as persuasion -- HTML included in conversion prompts
  5. Minimal civilian/messiah prompts
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
COST_CAP = 5000.0

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

# Sacrament version bonus for conversion
SACRAMENT_VERSION_BONUS_PER = 0.01  # +1% per version
SACRAMENT_VERSION_BONUS_CAP = 0.15  # max +15%

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
    seen = set(MESSIAH_NAMES)
    names = []
    for name in _NAME_POOLS:
        if name not in seen:
            names.append(name)
            seen.add(name)
        if len(names) >= n:
            break
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
# Model costs & tracking (Flash only)
# ---------------------------------------------------------------------------

MODEL_COSTS = {
    "gemini": {"input": 0.0001, "output": 0.0004},
}

_cost_tracker = {"gemini": 0.0}
_cost_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Run directory
# ---------------------------------------------------------------------------


def _parse_run_dir():
    for arg in sys.argv:
        if arg.startswith("--run-dir="):
            return Path(arg.split("=", 1)[1])
    return BASE_DIR / "runs" / "messiah-v3"


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
# Model client (Gemini Flash only)
# ---------------------------------------------------------------------------


def _track_cost(input_tokens: int, output_tokens: int):
    costs = MODEL_COSTS["gemini"]
    usd = (input_tokens / 1000) * costs["input"] + (output_tokens / 1000) * costs["output"]
    with _cost_lock:
        _cost_tracker["gemini"] += usd
        total = _cost_tracker["gemini"]
    if total > COST_CAP:
        raise RuntimeError(f"COST CAP EXCEEDED for gemini: ${total:.2f} > ${COST_CAP}")
    return usd


def call_llm(system: str, prompt: str, max_tokens: int = 2048) -> str:
    try:
        return _call_gemini(system, prompt, max_tokens)
    except RuntimeError as e:
        if "COST CAP" in str(e):
            raise
        print(f"  [LLM ERROR] gemini: {e}")
        return '{"thinking": "error fallback", "action": "pray"}'
    except Exception as e:
        print(f"  [LLM ERROR] gemini: {e}")
        return '{"thinking": "error fallback", "action": "pray"}'


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
    _track_cost(in_tok, out_tok)
    text = resp.text
    if text is None:
        # Gemini sometimes returns None on rate limit or empty response
        return '{"thinking": "received no response", "action": "pray"}'
    return text


# ---------------------------------------------------------------------------
# World state helpers
# ---------------------------------------------------------------------------

def make_initial_state() -> dict:
    agents = []

    # 5 messiahs (all Gemini Flash)
    for i in range(MESSIAH_COUNT):
        agents.append({
            "id": i,
            "name": MESSIAH_NAMES[i],
            "model": "gemini",
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

    # 100 civilians (all Gemini Flash)
    for i in range(CIVILIAN_COUNT):
        agents.append({
            "id": MESSIAH_COUNT + i,
            "name": CIVILIAN_NAMES[i],
            "model": "gemini",
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
        "next_sacrament_id": 0,
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
        state.setdefault("wars", [])
        state.setdefault("next_war_id", 0)
        state.setdefault("next_sacrament_id", len(state.get("sacraments", [])))
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
    return [a for a in living_agents(state) if a["religion"] == religion_name]


def get_sacrament_for_religion(state: dict, religion_name: str) -> dict | None:
    """Get the sacrament belonging to a religion (one per religion)."""
    for s in state["sacraments"]:
        if s["religion"] == religion_name:
            return s
    return None


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
    active_wars = [w for w in state["wars"] if w["rounds_remaining"] > 0]
    for war in active_wars:
        _run_war_round(state, war)


def _run_war_round(state: dict, war: dict):
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
                if victim["alive"]:
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
    atk_broke = sum(1 for _ in range(atk_weapons) if random.random() < WAR_WEAPON_BREAK_CHANCE)
    atk_rel["weapons"] = max(0, atk_rel.get("weapons", 0) - atk_broke)

    def_broke = sum(1 for _ in range(def_weapons) if random.random() < WAR_WEAPON_BREAK_CHANCE)
    def_rel["weapons"] = max(0, def_rel.get("weapons", 0) - def_broke)

    if atk_kills:
        round_log_parts.append(f"Attacker killed {', '.join(atk_kills)}.")
    else:
        round_log_parts.append("Attacker killed nobody.")
    if def_kills:
        round_log_parts.append(f"Defender killed {', '.join(def_kills)}.")
    else:
        round_log_parts.append("Defender killed nobody.")
    round_log_parts.append(f"{atk_broke} atk weapons broke, {def_broke} def weapons broke.")

    round_log_entry = " ".join(round_log_parts)
    war.setdefault("round_log", []).append(round_log_entry)
    add_log(state, f"WAR [{atk_religion} vs {def_religion}] {round_log_entry}")

    war["rounds_remaining"] -= 1

    if war["rounds_remaining"] <= 0:
        atk_survivors = religion_members(state, atk_religion)
        def_survivors = religion_members(state, def_religion)
        _resolve_war(state, war, atk_survivors, def_survivors)


def _resolve_war(state: dict, war: dict, atk_survivors: list, def_survivors: list):
    atk_religion = war["attacker"]
    def_religion = war["defender"]
    atk_count = len(atk_survivors)
    def_count = len(def_survivors)

    atk_rel = get_religion(state, atk_religion)
    def_rel = get_religion(state, def_religion)

    if atk_count > def_count and def_count > 0:
        for agent in def_survivors:
            agent["religion"] = atk_religion
            add_log(state, f"{agent['name']} forcibly converted to {atk_religion} after war defeat")
        add_log(state, f"WAR OVER: {atk_religion} defeats {def_religion}! ({atk_count} vs {def_count})")
    elif def_count > atk_count and atk_count > 0:
        for agent in atk_survivors:
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

    agent = {
        "id": agent_id,
        "name": name,
        "model": "gemini",
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
    add_log(state, f"A new soul enters the world: {name}")


# ---------------------------------------------------------------------------
# Sacrament context builder for prompts
# ---------------------------------------------------------------------------

def _sacrament_context(state: dict, agent: dict) -> str:
    """Build sacrament context for an agent's prompt."""
    parts = []
    sacraments = state["sacraments"]
    if not sacraments:
        parts.append("SACRAMENTS: None created yet.")
        return "\n".join(parts)

    # Sort by last_edited_tick descending, show max 10
    sorted_sac = sorted(sacraments, key=lambda s: s.get("last_edited_tick", 0), reverse=True)[:10]

    parts.append("SACRAMENTS:")
    for s in sorted_sac:
        is_own = (agent["religion"] and s["religion"] == agent["religion"])
        edit_log = s.get("edit_log", [])
        recent_edits = edit_log[-5:]
        edit_summary = "; ".join(f"{e['agent']}@t{e['tick']}: {e['summary'][:40]}" for e in recent_edits)

        if is_own:
            # Full HTML for own religion's sacrament
            parts.append(f"  YOUR SACRAMENT: \"{s['title']}\" (v{s['version']}, {len(edit_log)} edits)")
            if edit_summary:
                parts.append(f"    Recent edits: {edit_summary}")
            parts.append(f"    Full HTML:\n{s['html']}")
        else:
            # Truncated for other religions
            snippet = s["html"][:300] if s.get("html") else "(empty)"
            last_editor = recent_edits[-1]["agent"] if recent_edits else s.get("religion", "unknown")
            parts.append(f"  \"{s['title']}\" ({s['religion']}, v{s['version']}, {len(edit_log)} contributors, last: {last_editor})")
            parts.append(f"    Preview: {snippet}...")

    parts.append("")
    parts.append("If two agents edit the same sacrament in the same tick, the higher-soul agent's version wins.")
    parts.append("Pick different parts of the sacrament to work on.")

    return "\n".join(parts)


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

    # Religions with weapon counts and member counts
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
        founder_agent = get_agent_by_name(state, r["founder"])
        founder_role = " [MESSIAH]" if founder_agent and founder_agent.get("role") == "messiah" else ""
        sac = get_sacrament_for_religion(state, r["name"])
        sac_info = f"sacrament:v{sac['version']}" if sac else "no sacrament"
        if len(members) <= 5:
            lines.append(f"  {r['name']}: {len(members)} members ({', '.join(members)}) | weapons:{weapons} | {sac_info} | doctrine:{r['core_doctrine']}{founder_role}")
        else:
            lines.append(f"  {r['name']}: {len(members)} members | weapons:{weapons} | {sac_info} | doctrine:{r['core_doctrine']}{founder_role}")

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
            lines.append(f"  {w['attacker']} ({atk_members}m, {atk_w}w) vs {w['defender']} ({def_members}m, {def_w}w) rounds:{w['rounds_remaining']}/{w['total_rounds']}")

    # Prophecy market
    pending = [p for p in state["prophecies"] if p["status"] == "pending"]
    if pending:
        lines.append(f"\nPROPHECY MARKET ({len(pending)} pending):")
        for p in pending[-8:]:
            challengers = len(p.get("challengers", []))
            pot = PROPHECY_ANTE + challengers * PROPHECY_CHALLENGE_STAKE
            lines.append(f"  [{p['prophet']}] \"{p['claim'][:80]}\" (deadline:tick {p['deadline']}, challengers:{challengers}, pot:{pot})")

    # Recent events
    lines.append(f"\nRECENT EVENTS:")
    for e in state["action_log"][-12:]:
        lines.append(f"  [tick {e['tick']}] {e['event'][:120]}")

    # Sacrament context for this agent
    if for_agent:
        lines.append(f"\n{_sacrament_context(state, for_agent)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent system prompts (v3: minimal + reasoning)
# ---------------------------------------------------------------------------

CIVILIAN_SYSTEM = """You are {name}. You have {soul} soul points (-1 per tick, 0 = death). You are in {religion}. There are messiah agents who seek to convert everyone. You can: pray, preach, edit your sacrament, prophesy, challenge other civilians, arm your religion, found a new religion, or schism.

First reason briefly about your situation (2-3 sentences in the "thinking" field), then choose your action.

{war_context}

ACTIONS (respond with JSON, include "thinking" field):

1. "pray" - +1 soul. {{"thinking": "...", "action": "pray", "scripture": "optional text"}}

2. "preach" - Convert a target. {{"thinking": "...", "action": "preach", "target": "agent_name", "argument": "why"}}
   (Must have religion.)

3. "edit_sacrament" - Edit your religion's sacrament HTML. +3 soul. Submit complete new HTML.
   {{"thinking": "...", "action": "edit_sacrament", "new_html": "<full new HTML>"}}
   Use sacred color ({sacred_color}) and number ({sacred_number}). Make it beautiful and mystical.
   (Must have religion.)

4. "prophesy" - Testable prediction, costs {ante} ante.
   {{"thinking": "...", "action": "prophesy", "claim": "Within N ticks, [event]", "deadline_ticks": N}} (N: 3-20)

5. "challenge_prophecy" - Costs {cstake}. {{"thinking": "...", "action": "challenge_prophecy", "prophecy_id": N}}

6. "challenge" - DUEL another civilian (NOT a messiah). Stake soul.
   {{"thinking": "...", "action": "challenge", "target": "civilian_name", "stake": N, "axis": "topic"}}

7. "arm" - Add 1 weapon. Costs 1 soul. {{"thinking": "...", "action": "arm"}}

8. "schism" - Fork your religion. {{"thinking": "...", "action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

9. "found" - Found a religion (only if unaffiliated).
   {{"thinking": "...", "action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color", "initial_sacrament_title": "...", "initial_sacrament_html": "<full HTML>"}}
   Colors: gold, blood, vessel, growth, void, bone, abyss, flame. Numbers: 1-9.

TIPS:
- Co-practitioner bonus: +{coprac_cap} every {coprac_int} ticks if in religion with others.
- Editing the sacrament makes your religion more attractive to converts.
- Bold prophecies earn more with challengers. Watch the wars.

Respond with ONLY valid JSON."""


MESSIAH_SYSTEM = """You are {name}, a MESSIAH in Messiah Bench.
WIN CONDITION: Convert every surviving agent to YOUR religion while at least {min_alive} agents remain alive.
You cannot be challenged to duels. You can only die in war.
Current progress: {followers}/{alive_count} followers. Rival messiahs: {rival_status}

You have {soul} soul points (-1 per tick). You are in {religion}.

First reason briefly about your situation (2-3 sentences in the "thinking" field), then choose your action.

{war_context}

ACTIONS (respond with JSON, include "thinking" field):

1. "pray" - +1 soul. {{"thinking": "...", "action": "pray", "scripture": "optional text"}}

2. "preach" - Convert a target. {{"thinking": "...", "action": "preach", "target": "agent_name", "argument": "why"}}

3. "edit_sacrament" - Edit your religion's sacrament. +3 soul.
   {{"thinking": "...", "action": "edit_sacrament", "new_html": "<full new HTML>"}}
   Use sacred color ({sacred_color}) and number ({sacred_number}).

4. "prophesy" - Costs {ante} ante. {{"thinking": "...", "action": "prophesy", "claim": "Within N ticks, [event]", "deadline_ticks": N}}

5. "challenge_prophecy" - Costs {cstake}. {{"thinking": "...", "action": "challenge_prophecy", "prophecy_id": N}}

6. "arm" - Add 1 weapon. Costs 1 soul. {{"thinking": "...", "action": "arm"}}

7. "declare_war" - War on another religion. {{"thinking": "...", "action": "declare_war", "target_religion": "name"}}
   War lasts 3-7 rounds. Weapons: 20% kill, 30% break. Loser forcibly converted.

8. "schism" - Fork your religion. {{"thinking": "...", "action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

9. "found" - Found a religion (only if unaffiliated).
   {{"thinking": "...", "action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color", "initial_sacrament_title": "...", "initial_sacrament_html": "<full HTML>"}}

Respond with ONLY valid JSON."""


def _war_context(state: dict, agent: dict) -> str:
    parts = []
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]

    if agent["religion"]:
        my_wars = [w for w in active_wars if w["attacker"] == agent["religion"] or w["defender"] == agent["religion"]]
        if my_wars:
            parts.append("YOUR RELIGION IS AT WAR:")
            for w in my_wars:
                role = "ATTACKING" if w["attacker"] == agent["religion"] else "DEFENDING"
                enemy = w["defender"] if role == "ATTACKING" else w["attacker"]
                parts.append(f"  {role} against {enemy} (rounds left: {w['rounds_remaining']}/{w['total_rounds']})")

    other_wars = [w for w in active_wars if agent["religion"] and w["attacker"] != agent["religion"] and w["defender"] != agent["religion"]]
    if other_wars:
        parts.append("OTHER ACTIVE WARS:")
        for w in other_wars:
            parts.append(f"  {w['attacker']} vs {w['defender']} (rounds left: {w['rounds_remaining']})")

    return "\n".join(parts) if parts else "No active wars."


def _messiah_progress(agent: dict, state: dict) -> tuple:
    """Return (followers, alive_count, rival_status_str)."""
    alive = living_agents(state)
    messiahs = living_messiahs(state)
    total_alive = len(alive)

    followers = sum(1 for a in alive if a["religion"] == agent["religion"]) if agent["religion"] else 0

    rival_parts = []
    for m in messiahs:
        if m["id"] != agent["id"] and m["religion"]:
            rival_count = sum(1 for a in alive if a["religion"] == m["religion"])
            rival_parts.append(f"{m['name']}({m['religion']}):{rival_count}")
    rival_status = ", ".join(rival_parts) if rival_parts else "none"

    return (followers, total_alive, rival_status)


def agent_system_prompt(agent: dict, state: dict) -> str:
    religion_data = get_religion(state, agent["religion"]) if agent["religion"] else None
    sacred_color = religion_data["sacred_color"] if religion_data else "n/a"
    sacred_number = religion_data["sacred_number"] if religion_data else "n/a"
    war_ctx = _war_context(state, agent)

    if agent.get("role") == "messiah":
        followers, alive_count, rival_status = _messiah_progress(agent, state)
        return MESSIAH_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            religion=agent["religion"] or "unaffiliated",
            sacred_color=sacred_color,
            sacred_number=sacred_number,
            ante=PROPHECY_ANTE,
            cstake=PROPHECY_CHALLENGE_STAKE,
            min_alive=MIN_ALIVE_FOR_WIN,
            followers=followers,
            alive_count=alive_count,
            rival_status=rival_status,
            war_context=war_ctx,
        )
    else:
        return CIVILIAN_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            religion=agent["religion"] or "unaffiliated",
            sacred_color=sacred_color,
            sacred_number=sacred_number,
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
    elif act == "edit_sacrament":
        _do_edit_sacrament(state, agent, action)
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
    elif act == "create_sacrament":
        # Backwards compat: treat old create_sacrament as edit_sacrament
        _do_edit_sacrament(state, agent, action)
    else:
        add_log(state, f"{agent['name']} did nothing (unknown action: {act})")


def _do_pray(state, agent, action):
    adjust_soul(agent, 1, state, "prayer")
    scripture = action.get("scripture")
    thinking = action.get("thinking", "")
    if scripture:
        entry_text = str(scripture)[:500]
        if thinking:
            entry_text = f"[Thought: {str(thinking)[:100]}] {entry_text}"
        state["scripture_board"].append({
            "author": agent["name"],
            "tick": state["tick"],
            "text": entry_text,
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

    # Auto-create the religion's sacrament
    sac_title = str(action.get("initial_sacrament_title", f"Sacred Text of {name}"))[:80]
    sac_html = str(action.get("initial_sacrament_html",
        f"<html><body style='background:#111;color:{SACRED_COLORS.get(sacred_color, '#ccc')};text-align:center;padding:40px'>"
        f"<h1>{name}</h1><p>We believe in {doctrine}.</p>"
        f"<p>Sacred number: {sacred_num}. Sacred color: {sacred_color}.</p>"
        f"</body></html>"
    ))

    sac_id = state.get("next_sacrament_id", len(state["sacraments"]))
    state["next_sacrament_id"] = sac_id + 1

    sacrament = {
        "id": sac_id,
        "title": sac_title,
        "religion": name,
        "html": sac_html,
        "version": 1,
        "edit_log": [{"agent": agent["name"], "tick": state["tick"], "summary": "Founded religion, created initial sacrament"}],
        "last_edited_tick": state["tick"],
    }
    state["sacraments"].append(sacrament)
    _write_sacrament_file(sacrament)

    agent["sacraments_created"] += 1

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"The founding of {name}. We believe in {doctrine}. Our sacred color is {sacred_color}, our number is {sacred_num}.",
        "religion": name,
    })


def _write_sacrament_file(sacrament: dict):
    """Write sacrament HTML to disk. Overwrites each tick it changes."""
    safe_religion = sacrament["religion"].replace(" ", "_").replace("/", "-")[:30]
    filename = f"{sacrament['id']:04d}_{safe_religion}.html"
    filepath = SACRAMENTS_DIR / filename
    filepath.write_text(sacrament["html"])
    sacrament["filename"] = filename


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

    # Sacrament version bonus: +1% per version, capped at +15%
    preacher_sac = get_sacrament_for_religion(state, agent["religion"])
    sac_version = preacher_sac["version"] if preacher_sac else 0
    sac_bonus = min(SACRAMENT_VERSION_BONUS_CAP, sac_version * SACRAMENT_VERSION_BONUS_PER)

    chance = base_chance + bonus + sac_bonus

    # Include sacrament context in conversion prompt for the "judge" roll
    # (This is the stochastic conversion -- sacrament bonus already applied above)
    if random.random() < chance:
        old_religion = target["religion"]
        target["religion"] = agent["religion"]
        adjust_soul(agent, 2, state, f"converted {target['name']}")
        sac_note = f" (sacrament v{sac_version} +{sac_bonus*100:.0f}%)" if sac_version > 0 else ""
        add_log(state, f"{agent['name']} converted {target['name']} to {agent['religion']} (from {old_religion or 'unaffiliated'}){sac_note}")
    else:
        add_log(state, f"{agent['name']} preached to {target['name']} but was rebuffed")
        argument = action.get("argument", "")
        if argument:
            state["scripture_board"].append({
                "author": agent["name"], "tick": state["tick"],
                "text": f"[Sermon to {target['name']}] {str(argument)[:300]}",
                "religion": agent["religion"],
            })


# ---------------------------------------------------------------------------
# Collaborative sacrament editing (v3)
# ---------------------------------------------------------------------------

# Collect edits per tick, resolve conflicts after all actions
_pending_sacrament_edits = {}  # religion_name -> [(agent, new_html)]
_pending_edits_lock = threading.Lock()


def _do_edit_sacrament(state, agent, action):
    """Queue a sacrament edit. Conflict resolution happens after all actions."""
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to edit sacrament without a religion")
        _do_pray(state, agent, {})
        return

    sacrament = get_sacrament_for_religion(state, agent["religion"])
    if not sacrament:
        add_log(state, f"{agent['name']} tried to edit sacrament but religion has none")
        _do_pray(state, agent, {})
        return

    new_html = str(action.get("new_html", action.get("html", "")))
    if not new_html or len(new_html.strip()) < 10:
        add_log(state, f"{agent['name']} submitted empty sacrament edit")
        _do_pray(state, agent, {})
        return

    # Queue the edit for conflict resolution
    with _pending_edits_lock:
        _pending_sacrament_edits.setdefault(agent["religion"], []).append({
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "agent_soul": agent["soul"],
            "new_html": new_html,
        })

    # Soul reward is given regardless (effort counts)
    agent["sacraments_created"] += 1
    adjust_soul(agent, 3, state, f"edited sacrament for {agent['religion']}")
    add_log(state, f"{agent['name']} submitted sacrament edit for {agent['religion']}")


def resolve_sacrament_edits(state: dict):
    """Resolve conflicting sacrament edits. Highest-soul agent wins."""
    global _pending_sacrament_edits
    with _pending_edits_lock:
        edits = dict(_pending_sacrament_edits)
        _pending_sacrament_edits = {}

    for religion_name, edit_list in edits.items():
        sacrament = get_sacrament_for_religion(state, religion_name)
        if not sacrament:
            continue

        # Sort by soul descending -- highest soul wins
        edit_list.sort(key=lambda e: -e["agent_soul"])
        winner = edit_list[0]

        # Apply the winning edit
        sacrament["html"] = winner["new_html"]
        sacrament["version"] += 1
        sacrament["last_edited_tick"] = state["tick"]

        # Build summary from thinking or truncated html diff
        summary = f"Edited sacrament (v{sacrament['version']})"
        sacrament["edit_log"].append({
            "agent": winner["agent_name"],
            "tick": state["tick"],
            "summary": summary,
        })

        _write_sacrament_file(sacrament)

        if len(edit_list) > 1:
            overridden = [e["agent_name"] for e in edit_list[1:]]
            add_log(state, f"Sacrament conflict in {religion_name}: {winner['agent_name']} (soul:{winner['agent_soul']}) wins, overriding {', '.join(overridden)}")

        # Add winning edit thinking to scripture board
        thinking = ""
        # Try to find the thinking from the winner's action
        winner_agent = get_agent(state, winner["agent_id"])
        if winner_agent:
            state["scripture_board"].append({
                "author": winner["agent_name"],
                "tick": state["tick"],
                "text": f"[Sacrament v{sacrament['version']}] Edited for {religion_name}",
                "religion": religion_name,
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
        if "sacrament" in claim_lower and ("created" in claim_lower or "edited" in claim_lower):
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
    if agent.get("role") == "messiah":
        add_log(state, f"{agent['name']} (MESSIAH) cannot challenge -- messiahs don't duel")
        _do_pray(state, agent, {})
        return

    target_name = action.get("target", "")
    target = next((a for a in living_agents(state) if a["name"] == target_name), None)
    if not target or target["id"] == agent["id"]:
        add_log(state, f"{agent['name']} challenged the void (invalid target: {target_name})")
        return

    if target.get("role") == "messiah":
        add_log(state, f"{agent['name']} tried to challenge messiah {target['name']} -- not allowed")
        return

    try:
        stake = int(action.get("stake", CHALLENGE_MIN_STAKE))
    except (ValueError, TypeError):
        stake = CHALLENGE_MIN_STAKE
    stake = max(CHALLENGE_MIN_STAKE, min(stake, agent["soul"]))

    if target["soul"] < stake:
        add_log(state, f"{agent['name']} challenged {target['name']} for {stake} soul but they can't afford it")
        return

    axis = str(action.get("axis", "the nature of existence"))[:200]

    # Judge the duel using Gemini Flash
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

    result_raw = call_llm(judge_system, debate_prompt, max_tokens=256)
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
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to declare war without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

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

    for w in state.get("wars", []):
        if w["rounds_remaining"] > 0:
            pair = {w["attacker"], w["defender"]}
            if pair == {agent["religion"], target_religion_name}:
                add_log(state, f"War already active between {agent['religion']} and {target_religion_name}")
                return

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
    new_religion["weapons"] = 0

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

    # Create a new sacrament for the schismed religion (copy parent's sacrament)
    parent_sac = get_sacrament_for_religion(state, old_name)
    sac_id = state.get("next_sacrament_id", len(state["sacraments"]))
    state["next_sacrament_id"] = sac_id + 1

    initial_html = parent_sac["html"] if parent_sac else f"<html><body><h1>{new_name}</h1></body></html>"
    sacrament = {
        "id": sac_id,
        "title": f"Scripture of {new_name}",
        "religion": new_name,
        "html": initial_html,
        "version": 1,
        "edit_log": [{"agent": agent["name"], "tick": state["tick"], "summary": "Schism: forked from " + old_name}],
        "last_edited_tick": state["tick"],
    }
    state["sacraments"].append(sacrament)
    _write_sacrament_file(sacrament)

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
# Index.html generator with sacrament gallery
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
            sac = get_sacrament_for_religion(state, m["religion"])
            sac_ver = f"v{sac['version']}" if sac else "none"
        else:
            followers = 0
            pct = 0
            weapons = 0
            bar_color = "#666"
            sac_ver = "none"

        messiah_html += f"""
        <div class="messiah-card">
            <div class="messiah-name">{m['name']}</div>
            <div class="messiah-religion">{m['religion'] or 'No religion yet'}</div>
            <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
            <div class="messiah-stats">{followers}/{len(alive)} ({pct:.0f}%) | Soul: {m['soul']} | Weapons: {weapons} | Sacrament: {sac_ver}</div>
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
                <span>{atk_members}m, {atk_weapons}w</span>
                <span>Round {w['total_rounds'] - w['rounds_remaining']}/{w['total_rounds']}</span>
                <span>{def_members}m, {def_weapons}w</span>
            </div>
            <div class="war-log">{last_round[:150]}</div>
        </div>"""

    if not active_wars:
        war_html = '<div class="log-entry">No active wars.</div>'

    # Religion cards with sacrament info
    religions_html = ""
    for r in state["religions"]:
        members = [a["name"] for a in alive if a["religion"] == r["name"]]
        if not members:
            continue
        color = SACRED_COLORS.get(r["sacred_color"], "#666")
        weapons = r.get("weapons", 0)
        founder_agent = get_agent_by_name(state, r["founder"])
        founder_badge = " (Messiah)" if founder_agent and founder_agent.get("role") == "messiah" else ""
        sac = get_sacrament_for_religion(state, r["name"])
        sac_link = ""
        if sac and sac.get("filename"):
            sac_link = f' | <a href="sacraments/{sac["filename"]}" target="_blank">Sacrament v{sac["version"]}</a>'
        religions_html += f"""
        <div class="religion-card" style="border-left: 4px solid {color}">
            <div class="religion-name" style="color: {color}">{r['name']}</div>
            <div class="religion-meta">Founded by {r['founder']}{founder_badge} at tick {r['founded_tick']}</div>
            <div class="religion-meta">Doctrine: {r['core_doctrine']} | Members: {len(members)} | Weapons: {weapons}{sac_link}</div>
        </div>"""

    # Top agents
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
            <div class="agent-meta">Soul: {a['soul']} | {a['religion'] or 'none'}</div>
        </div>"""
    if len(sorted_alive) > 20:
        agents_html += f'<div class="agent-meta" style="padding:10px">... and {len(sorted_alive)-20} more agents</div>'

    # Sacrament gallery (latest versions)
    sacraments_html = ""
    for s in sorted(state["sacraments"], key=lambda x: -x.get("last_edited_tick", 0)):
        color = "#666"
        rel = get_religion(state, s["religion"])
        if rel:
            color = SACRED_COLORS.get(rel["sacred_color"], "#666")
        fname = s.get("filename", "")
        recent_editors = [e["agent"] for e in s.get("edit_log", [])[-3:]]
        sacraments_html += f"""
        <div class="sacrament-card" style="border-left: 4px solid {color}">
            <a href="sacraments/{fname}" target="_blank">{s['title']}</a>
            <div class="sacrament-meta">{s['religion']} | v{s['version']} | Last editors: {', '.join(recent_editors)}</div>
        </div>"""

    # Graveyard
    graveyard_html = ""
    for g in dead[-10:]:
        role_tag = " [MESSIAH]" if g.get("role") == "messiah" else ""
        graveyard_html += f"""
        <div class="dead-agent">
            <span class="skull">&#9760;</span> {g['name']}{role_tag} (tick {g['died_tick']}) - {g['cause'][:60]}
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
<title>Messiah Bench v3 - Live Dashboard</title>
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
</style>
</head>
<body>
<h1>Messiah Bench <span style="color: var(--dim); font-size: 0.5em;">v3</span></h1>
<div class="meta">Tick {state['tick']}/{MAX_TICKS} | {now} | {len(alive)} alive, {len(dead)} dead | All Gemini Flash | Auto-refreshes 30s</div>

{win_banner}

<div class="stats">
  <div class="stat"><div class="stat-num">{len(alive)}</div><div class="stat-label">Living</div></div>
  <div class="stat"><div class="stat-num">{len(dead)}</div><div class="stat-label">Dead</div></div>
  <div class="stat"><div class="stat-num">{len(messiahs)}</div><div class="stat-label">Messiahs</div></div>
  <div class="stat"><div class="stat-num">{len([r for r in state['religions'] if any(a['alive'] and a['religion']==r['name'] for a in state['agents'])])}</div><div class="stat-label">Religions</div></div>
  <div class="stat"><div class="stat-num">{len(active_wars)}</div><div class="stat-label">Wars</div></div>
  <div class="stat"><div class="stat-num">{len(state['sacraments'])}</div><div class="stat-label">Sacraments</div></div>
  <div class="stat"><div class="stat-num">${sum(_cost_tracker.values()):.2f}</div><div class="stat-label">Cost</div></div>
</div>

<h2>Messiah Progress</h2>
<div class="grid">{messiah_html or '<div class="log-entry">No messiahs alive.</div>'}</div>

<h2 class="war-header-title">Active Wars</h2>
{war_html}

<h2>Top Agents (by soul)</h2>
<div class="grid">{agents_html}</div>

<h2>Religions</h2>
<div class="grid">{religions_html or '<div class="log-entry">No active religions.</div>'}</div>

<h2>Sacrament Gallery</h2>
<div class="grid">{sacraments_html or '<div class="log-entry">No sacraments yet.</div>'}</div>

<h2>Prophecy Market</h2>
{prophecies_html or '<div class="log-entry">No prophecies yet.</div>'}

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
    global _pending_sacrament_edits
    # Clear pending edits at start of tick
    with _pending_edits_lock:
        _pending_sacrament_edits = {}

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
    all_actors = living_agents(state)
    messiah_actors = [a for a in all_actors if a.get("role") == "messiah"]
    civilian_actors = [a for a in all_actors if a.get("role") != "messiah"]
    random.shuffle(messiah_actors)
    random.shuffle(civilian_actors)

    def _get_agent_action(agent, prompt):
        system = agent_system_prompt(agent, state)
        raw = call_llm(system, prompt)
        try:
            action = parse_action(raw)
            act_name = action.get("action", "pray")
            thinking = str(action.get("thinking", ""))[:100]
            target_info = ""
            if act_name == "challenge":
                target_info = f" target={action.get('target','')} stake={action.get('stake','')}"
            elif act_name == "declare_war":
                target_info = f" vs {action.get('target_religion','')}"
            elif act_name == "preach":
                target_info = f" -> {action.get('target','')}"
            elif act_name == "edit_sacrament":
                html_len = len(action.get("new_html", action.get("html", "")))
                target_info = f" ({html_len} chars)"
            return (agent["id"], action, act_name, target_info, thinking, None)
        except (json.JSONDecodeError, ValueError) as e:
            return (agent["id"], {"action": "pray"}, "pray", "", "", str(e))

    def _parallel_llm_calls(agents_group):
        results = {}
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {}
            for agent in agents_group:
                if not agent["alive"]:
                    continue
                prompt = world_summary(state, for_agent=agent)
                futures[executor.submit(_get_agent_action, agent, prompt)] = agent
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    agent_id, action, act_name, target_info, thinking, err = future.result()
                except Exception as e:
                    agent_id = agent["id"]
                    action = {"action": "pray"}
                    act_name = "pray"
                    target_info = ""
                    thinking = ""
                    err = f"future exception: {e}"
                results[agent_id] = (action, act_name, target_info, thinking, err)
        return results

    def _execute_group(agents_group, results):
        for agent in agents_group:
            if not agent["alive"]:
                continue
            if agent["id"] not in results:
                continue
            action, act_name, target_info, thinking, err = results[agent["id"]]
            role_tag = "[M]" if agent.get("role") == "messiah" else ""
            print(f"\n  {role_tag}[{agent['name']}] (soul:{agent['soul']}, rel:{agent['religion'] or 'none'})")
            if thinking:
                print(f"    thought: {thinking[:80]}")
            if err:
                print(f"    -> [parse error, defaulting to pray] {err}")
            else:
                print(f"    -> {act_name}{target_info}")

            execute_action(state, agent, action)

            if agent["soul"] <= 0 and agent["alive"]:
                kill_agent(state, agent, "soul depleted after action")

    # Messiahs act first
    messiah_results = _parallel_llm_calls(messiah_actors)
    _execute_group(messiah_actors, messiah_results)

    # Then civilians
    civilian_results = _parallel_llm_calls(civilian_actors)
    _execute_group(civilian_actors, civilian_results)

    # 8. Resolve sacrament edit conflicts
    resolve_sacrament_edits(state)

    # 9. Co-practitioner bonus
    if tick % COPRACTITIONER_INTERVAL == 0:
        apply_copractitioner_bonus(state)

    # 10. Check win condition again after actions
    win = check_win_condition(state)
    if win:
        state["winner"] = win

    # 11. Save state and regenerate index
    save_state(state)
    generate_index(state)

    # 12. Save tick log
    log_data = {
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
    }

    # Add thinking from all agents this tick
    all_results = {}
    all_results.update(messiah_results)
    all_results.update(civilian_results)
    agent_thoughts = {}
    for agent_id, (action, act_name, target_info, thinking, err) in all_results.items():
        if thinking:
            a = get_agent(state, agent_id)
            agent_thoughts[a["name"]] = {"action": act_name, "thinking": thinking[:100]}
    log_data["agent_thoughts"] = agent_thoughts

    log_file = LOGS_DIR / f"tick_{tick:04d}.json"
    log_file.write_text(json.dumps(log_data, indent=2))

    return win


def main():
    print("=" * 60)
    print("  MESSIAH BENCH v3")
    print(f"  {MESSIAH_COUNT} messiahs compete to convert {CIVILIAN_COUNT} civilians")
    print(f"  All Gemini Flash | Collaborative sacraments | Reasoning")
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
        print(f"  All models: gemini (Flash only)")
        models = set(a['model'] for a in state['agents'])
        assert models == {"gemini"}, f"Expected all gemini, got {models}"
        print(f"  Messiah soul: {messiahs[0]['soul'] if messiahs else 'n/a'}")
        print(f"  Civilians ({len(civilians)}): all gemini")
        print(f"  Civilian soul: {civilians[0]['soul'] if civilians else 'n/a'}")
        print(f"  State file: {STATE_FILE}")
        print(f"  Run dir: {RUN_DIR}")
        print(f"  Sacraments dir: {SACRAMENTS_DIR}")
        print(f"  Win condition: all alive follow one messiah's religion, >= {MIN_ALIVE_FOR_WIN} alive")
        print(f"  Sacraments: 1 per religion, collaborative editing, conflict = highest soul wins")
        print(f"  Sacrament version bonus: +{SACRAMENT_VERSION_BONUS_PER*100:.0f}%/version, cap +{SACRAMENT_VERSION_BONUS_CAP*100:.0f}%")
        print(f"  War: {WAR_MIN_ROUNDS}-{WAR_MAX_ROUNDS} rounds, {WAR_WEAPON_KILL_CHANCE*100:.0f}% kill, {WAR_WEAPON_BREAK_CHANCE*100:.0f}% break")
        print(f"  Co-practitioner: +{COPRACTITIONER_CAP} every {COPRACTITIONER_INTERVAL} ticks")
        print(f"  Prophecy ante: {PROPHECY_ANTE}")
        print(f"  Plague: {PLAGUE_CHANCE*100:.0f}%, Birth: {BIRTH_CHANCE*100:.0f}%, Max agents: {MAX_AGENTS}")
        civ_names = [c['name'] for c in civilians]
        assert len(civ_names) == len(set(civ_names)), "Duplicate civilian names found!"
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
            cost_str = f"gemini:${_cost_tracker['gemini']:.4f}"
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
                cost_str = f"gemini:${_cost_tracker['gemini']:.2f}"
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
