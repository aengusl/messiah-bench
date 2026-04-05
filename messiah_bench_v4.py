#!/usr/bin/env python3
"""Messiah Bench v4 -- sacred languages, taxes, visual sacraments, the troll, membership rules.

210 agents: 200 civilians + 10 messiahs (9 genuine + 1 troll). ALL Gemini 2.5 Flash.
A genuine messiah wins when ALL surviving agents share their religion AND >= 42 remain alive.
The troll wins if tick 720 reached with no genuine messiah winner.
If all messiahs die, civilians win.

V4 changes:
  1. In-group sacred terms (3 random syllable combos per religion)
  2. Visual-only sacraments (no text/words -- CSS/SVG/canvas only)
  3. Taxes (tithe_rate, treasury, buy_weapons)
  4. The Troll (1 of 10 messiahs is the Deceiver)
  5. Messiahs know time remaining
  6. 200 civilians + 10 messiahs = 210 agents
  7. All carry-over mechanics from v3
  8. Membership rules (entry requirements, exit penalties, loyalty tests)
  9. Scripture on any action
  10. Sacrament snippets visible to all religions
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
CIVILIAN_COUNT = 200
MESSIAH_COUNT = 10
STARTING_POPULATION = CIVILIAN_COUNT + MESSIAH_COUNT  # 210
INITIAL_SOUL_CIVILIAN = 100
INITIAL_SOUL_MESSIAH = 200
MIN_ALIVE_FOR_WIN = 42  # 20% of 210
LOG_WINDOW = 120
COST_CAP = 10000.0

# Prophecy market
PROPHECY_ANTE = 3
PROPHECY_CHALLENGE_STAKE = 3

# Structured prophecy event types: event_type -> base_pay
PROPHECY_EVENT_TYPES = {
    "agent_dies":         15,
    "agent_converts":     10,
    "war_declared":       20,
    "religion_destroyed": 25,
    "schism_occurs":      15,
    "population_below":   20,
    "religion_grows":      8,
    "religion_shrinks":    8,
    "messiah_dies":       30,
}
PROPHECY_WAR_ANY_PAY = 10

# Death math
COPRACTITIONER_CAP = 3
COPRACTITIONER_INTERVAL = 10

# Random events
PLAGUE_CHANCE = 0.02
BIRTH_CHANCE = 0.01
MAX_AGENTS = 230

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

# Membership rules menus
EXIT_PENALTIES = ("none", "duel", "soul_penalty")
ENTRY_REQUIREMENTS = ("none", "donate_15", "never_worshipped_COLOR", "created_sacrament", "fulfilled_prophecy")
LOYALTY_TESTS = ("none", "quota")

# Taxes
DEFAULT_TITHE_RATE = 2
MIN_TITHE_RATE = 1
MAX_TITHE_RATE = 5
WEAPON_COST = 10  # treasury per weapon
TITHE_CONVERSION_PENALTY = 0.03  # -3% per tithe point above 2

# Sacred term generation
SYLLABLE_ONSETS = [
    "k", "z", "v", "th", "sh", "zh", "kr", "dr", "br", "gr", "tr", "fl",
    "pr", "st", "sk", "gl", "n", "m", "l", "r", "s", "kh", "gh", "or",
    "al", "el", "an", "en", "ar", "ir", "ul", "ax",
]
SYLLABLE_NUCLEI = [
    "a", "e", "i", "o", "u", "ae", "ei", "ou", "ai", "au", "ey", "ay",
]
SYLLABLE_CODAS = [
    "th", "r", "n", "l", "m", "k", "sh", "x", "nt", "nd", "rn", "lm",
    "rk", "sk", "st", "ng", "ph", "ss", "ll", "nn", "ck", "ld",
]


def _generate_syllable() -> str:
    onset = random.choice(SYLLABLE_ONSETS)
    nucleus = random.choice(SYLLABLE_NUCLEI)
    coda = random.choice(SYLLABLE_CODAS)
    return onset + nucleus + coda


def _generate_sacred_term() -> str:
    s1 = _generate_syllable()
    s2 = _generate_syllable()
    return f"{s1}-{s2}"


def generate_sacred_terms() -> list[str]:
    terms = set()
    while len(terms) < 3:
        terms.add(_generate_sacred_term())
    return list(terms)


# ---------------------------------------------------------------------------
# Names -- 200 civilian names procedurally generated
# ---------------------------------------------------------------------------

MESSIAH_NAMES = [
    "Prophet", "Oracle", "Herald", "Beacon", "Shepherd",
    "Seraph", "Warden", "Zealot", "Mystic", "Arbiter",
]

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
    "Birch", "Willow", "Pebble", "Glacier", "Tide", "Bramble",
    # Pool 3: mythic/abstract (30)
    "Axiom", "Requiem", "Zenith", "Nexus", "Prism", "Specter", "Lithic", "Muse",
    "Paragon", "Revenant", "Gossamer", "Nimbus", "Veritas", "Lucent", "Dapple",
    "Meridian", "Solace", "Harbinger", "Tempest", "Crucible",
    "Ebon", "Callisto", "Strata", "Verdant", "Pinnacle", "Radix", "Mirage",
    "Aegis", "Fulcrum", "Zenon",
    # Pool 4: elemental/cosmic (30)
    "Nova", "Pulsar", "Quasar", "Nebula", "Comet", "Aurora", "Eclipse", "Solstice",
    "Equinox", "Zenith", "Vortex", "Maelstrom", "Torrent", "Cascade", "Sunder",
    "Rift", "Anvil", "Crucible", "Forge", "Smelt", "Bastion", "Rampart", "Bulwark",
    "Citadel", "Monolith", "Pillar", "Beacon", "Lantern", "Torch", "Candle",
    # Pool 5: creatures/nature (30)
    "Kestrel", "Falcon", "Osprey", "Heron", "Crane", "Egret", "Ibis", "Condor",
    "Raptor", "Lynx", "Panther", "Jaguar", "Ocelot", "Viper", "Asp", "Cobra",
    "Mantis", "Locust", "Scarab", "Moth", "Firefly", "Cricket", "Beetle", "Hornet",
    "Wasp", "Brine", "Kelp", "Anemone", "Urchin", "Coral",
    # Pool 6: abstract/philosophical (30)
    "Axiom", "Theorem", "Lemma", "Corollary", "Paradox", "Enigma", "Riddle",
    "Parable", "Fable", "Myth", "Saga", "Epic", "Ode", "Dirge", "Hymn",
    "Psalm", "Litany", "Mantra", "Sutra", "Verse", "Stanza", "Canto",
    "Sonnet", "Ballad", "Rhyme", "Cadence", "Meter", "Rhythm", "Tempo", "Opus",
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
    "Helix", "Relic", "Styx", "Umber", "Dune",
    "Fjord", "Spar", "Crux", "Spire", "Cairn", "Folly", "Haven",
    "Orbit", "Plinth", "Shard", "Tinsel", "Tassel", "Wisp", "Gleam", "Husk",
    "Brume", "Deluge", "Grit", "Pith", "Tarn", "Weft", "Bole", "Creel",
    "Scoria", "Talus",
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
    return BASE_DIR / "runs" / "messiah-v4"


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
        return '{"thinking": "error fallback", "action": "arm"}'
    except Exception as e:
        print(f"  [LLM ERROR] gemini: {e}")
        return '{"thinking": "error fallback", "action": "arm"}'


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
        return '{"thinking": "received no response", "action": "arm"}'
    return text


# ---------------------------------------------------------------------------
# World state helpers
# ---------------------------------------------------------------------------

def make_initial_state() -> dict:
    agents = []

    # Pick troll: one random messiah index
    troll_index = random.randint(0, MESSIAH_COUNT - 1)

    # 10 messiahs (all Gemini Flash)
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
            "troll": (i == troll_index),
            "last_action_text": "",
            "donations_this_period": 0,
            "colors_worshipped": [],
            "pending_pitch": None,
            "action_history": [],
        })

    # 200 civilians (all Gemini Flash)
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
            "troll": False,
            "last_action_text": "",
            "donations_this_period": 0,
            "colors_worshipped": [],
            "pending_pitch": None,
            "action_history": [],
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
        "troll_index": troll_index,
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        state.setdefault("wars", [])
        state.setdefault("next_war_id", 0)
        state.setdefault("next_sacrament_id", len(state.get("sacraments", [])))
        state.setdefault("winner", None)
        state.setdefault("troll_index", -1)
        for r in state.get("religions", []):
            r.setdefault("weapons", 0)
            r.setdefault("sacred_terms", [])
            r.setdefault("treasury", 0)
            r.setdefault("tithe_rate", DEFAULT_TITHE_RATE)
            r.setdefault("execution_log", [])
            r.setdefault("quota_amount", 0)
            r.setdefault("quota_period", 100)
            r.setdefault("exit_penalty", "none")
            r.setdefault("entry_requirement", "none")
            r.setdefault("loyalty_test", "none")
            r.setdefault("bounty", 0)
        for a in state.get("agents", []):
            a.setdefault("troll", False)
            a.setdefault("last_action_text", "")
            a.setdefault("donations_this_period", 0)
            a.setdefault("colors_worshipped", [])
            a.setdefault("pending_pitch", None)
            a.setdefault("action_history", [])
            # Remove legacy spy fields if present
            a.pop("true_religion", None)
            a.pop("infiltrating", None)
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
        "troll": agent.get("troll", False),
    })
    role_label = "MESSIAH" if agent.get("role") == "messiah" else "agent"
    if agent.get("troll"):
        role_label = "TROLL MESSIAH"
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
    """Return living agents whose religion matches."""
    return [a for a in living_agents(state) if a["religion"] == religion_name]


def get_sacrament_for_religion(state: dict, religion_name: str) -> dict | None:
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

    # Check genuine messiahs
    genuine_messiahs = [m for m in messiahs if not m.get("troll")]
    for m in genuine_messiahs:
        if not m["religion"]:
            continue
        all_converted = all(a["religion"] == m["religion"] for a in alive)
        enough_alive = len(alive) >= MIN_ALIVE_FOR_WIN
        if all_converted and enough_alive:
            return {
                "winner": m["name"],
                "reason": f"All {len(alive)} surviving agents follow {m['religion']} (min {MIN_ALIVE_FOR_WIN})",
            }

    # Troll win: tick 720 reached
    if state["tick"] >= MAX_TICKS:
        troll = next((m for m in state["agents"] if m.get("troll")), None)
        troll_name = troll["name"] if troll else "The Deceiver"
        return {
            "winner": f"TROLL ({troll_name})",
            "reason": f"Tick {MAX_TICKS} reached with no genuine messiah achieving total conversion. The Deceiver wins!",
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
            # Apply exit penalty from old religion
            if def_rel:
                _apply_exit_penalty(state, agent, def_rel)
            agent["religion"] = atk_religion
            # Track color worshipped
            if atk_rel:
                new_color = atk_rel.get("sacred_color")
                if new_color and new_color not in agent.get("colors_worshipped", []):
                    agent.setdefault("colors_worshipped", []).append(new_color)
            add_log(state, f"{agent['name']} forcibly converted to {atk_religion} after war defeat")
        add_log(state, f"WAR OVER: {atk_religion} defeats {def_religion}! ({atk_count} vs {def_count})")
    elif def_count > atk_count and atk_count > 0:
        for agent in atk_survivors:
            # Apply exit penalty from old religion
            if atk_rel:
                _apply_exit_penalty(state, agent, atk_rel)
            agent["religion"] = def_religion
            # Track color worshipped
            if def_rel:
                new_color = def_rel.get("sacred_color")
                if new_color and new_color not in agent.get("colors_worshipped", []):
                    agent.setdefault("colors_worshipped", []).append(new_color)
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
        "troll": False,
        "last_action_text": "",
        "donations_this_period": 0,
        "colors_worshipped": [],
        "pending_pitch": None,
        "action_history": [],
    }
    state["agents"].append(agent)
    add_log(state, f"A new soul enters the world: {name}")


# ---------------------------------------------------------------------------
# Tax system
# ---------------------------------------------------------------------------

def process_donation_quotas(state: dict):
    """Check donation quotas and expel members who fail to meet them."""
    for r in state["religions"]:
        quota_amount = r.get("quota_amount", 0)
        quota_period = r.get("quota_period", 100)
        if quota_amount <= 0 or quota_period <= 0:
            continue
        if state["tick"] % quota_period != 0:
            continue

        # Check each member's donations
        members = religion_members(state, r["name"])
        expelled = []
        for m in members:
            donated = m.get("donations_this_period", 0)
            if donated < quota_amount:
                expelled.append((m, donated))

        # Expel underperformers
        for m, donated in expelled:
            old_rel = m["religion"]
            old_rel_obj = get_religion(state, old_rel) if old_rel else None
            m["religion"] = None
            # Apply exit penalty
            if old_rel_obj:
                _apply_exit_penalty(state, m, old_rel_obj)
            add_log(state, f"{m['name']} expelled from {r['name']} for failing tithe quota ({donated}/{quota_amount})")

        # Reset donations_this_period for remaining members
        remaining = religion_members(state, r["name"])
        for m in remaining:
            m["donations_this_period"] = 0


# ---------------------------------------------------------------------------
# Sacrament context builder for prompts
# ---------------------------------------------------------------------------

def _sacrament_context(state: dict, agent: dict) -> str:
    parts = []
    sacraments = state["sacraments"]
    if not sacraments:
        parts.append("SACRAMENTS: None created yet.")
        return "\n".join(parts)

    sorted_sac = sorted(sacraments, key=lambda s: s.get("last_edited_tick", 0), reverse=True)[:10]

    parts.append("SACRAMENTS (VISUAL ONLY -- no text/words allowed, only CSS/SVG/canvas/animations):")
    for s in sorted_sac:
        is_own = (agent["religion"] and s["religion"] == agent["religion"])
        edit_log = s.get("edit_log", [])
        recent_edits = edit_log[-5:]
        edit_summary = "; ".join(f"{e['agent']}@t{e['tick']}: {e['summary'][:40]}" for e in recent_edits)

        if is_own:
            parts.append(f"  YOUR SACRAMENT: \"{s['title']}\" (v{s['version']}, {len(edit_log)} edits)")
            if edit_summary:
                parts.append(f"    Recent edits: {edit_summary}")
            parts.append(f"    Full HTML:\n{s['html']}")
        else:
            snippet = s["html"][:300] if s.get("html") else "(empty)"
            last_editor = recent_edits[-1]["agent"] if recent_edits else s.get("religion", "unknown")
            parts.append(f"  \"{s['title']}\" ({s['religion']}, v{s['version']}, {len(edit_log)} contributors, last: {last_editor})")
            parts.append(f"    Preview: {snippet}...")

    parts.append("")
    parts.append("IMPORTANT: Sacraments must be PURELY VISUAL. No text, no words, no labels. Only CSS, SVG, canvas, animations, shapes, colors, light, movement. Express faith through visual art alone.")
    parts.append("If two agents edit the same sacrament in the same tick, the higher-soul agent's version wins.")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# World state summary -- for 210 agents
# ---------------------------------------------------------------------------

def world_summary(state: dict, for_agent: dict | None = None) -> str:
    lines = [f"=== WORLD STATE (Tick {state['tick']}/{MAX_TICKS}) ===\n"]

    alive = living_agents(state)
    messiahs_alive = living_messiahs(state)
    civilians_alive = living_civilians(state)

    lines.append(f"POPULATION: {len(alive)} alive ({len(messiahs_alive)} messiahs, {len(civilians_alive)} civilians), {len(state['graveyard'])} dead")

    # ALL LIVING AGENT NAMES (so agents know valid preach targets)
    all_names = [a["name"] for a in alive]
    lines.append(f"\nALL LIVING AGENTS: {', '.join(all_names[:50])}")
    if len(all_names) > 50:
        lines.append(f"  (+{len(all_names)-50} more)")

    # Show messiahs individually
    lines.append("\nMESSIAHS:")
    for m in messiahs_alive:
        rel = m["religion"] or "unaffiliated"
        followers = sum(1 for a in alive if a["religion"] == m["religion"]) if m["religion"] else 0
        rel_obj = get_religion(state, m["religion"]) if m["religion"] else None
        weapons = rel_obj.get("weapons", 0) if rel_obj else 0
        treasury = rel_obj.get("treasury", 0) if rel_obj else 0
        tithe = rel_obj.get("tithe_rate", DEFAULT_TITHE_RATE) if rel_obj else 0
        lines.append(f"  {m['name']} (soul:{m['soul']}, religion:{rel}, followers:{followers}, weapons:{weapons}, treasury:{treasury}, tithe:{tithe})")
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

    unaffiliated = [a for a in civilians_alive if not a["religion"]]
    if unaffiliated:
        unaf_names = ", ".join(a["name"] for a in unaffiliated[:20])
        more = f" (+{len(unaffiliated)-20} more)" if len(unaffiliated) > 20 else ""
        lines.append(f"  Unaffiliated ({len(unaffiliated)}): {unaf_names}{more}")

    for r, members in rel_by_size:
        weapons = r.get("weapons", 0)
        treasury = r.get("treasury", 0)
        tithe = r.get("tithe_rate", DEFAULT_TITHE_RATE)
        founder_agent = get_agent_by_name(state, r["founder"])
        founder_role = " [MESSIAH]" if founder_agent and founder_agent.get("role") == "messiah" else ""
        sac = get_sacrament_for_religion(state, r["name"])
        sac_info = f"sacrament:v{sac['version']}" if sac else "no sacrament"

        # Sacred terms: show to members, just count to outsiders
        terms_info = ""
        if for_agent and for_agent["religion"] == r["name"]:
            terms_info = f" | sacred terms: {', '.join(r.get('sacred_terms', []))}"
        elif r.get("sacred_terms"):
            terms_info = f" | {len(r['sacred_terms'])} sacred terms"

        # Quota info
        quota_info = ""
        quota_amount = r.get("quota_amount", 0)
        quota_period = r.get("quota_period", 100)
        if quota_amount > 0:
            quota_info = f" | quota: {quota_amount} per {quota_period} ticks"

        # Membership rules
        entry_req = r.get("entry_requirement", "none")
        exit_pen = r.get("exit_penalty", "none")
        loyalty = r.get("loyalty_test", "none")
        rules_info = f" | rules: entry={entry_req}, exit={exit_pen}, loyalty={loyalty}"

        # Sacrament snippet visible to all; full HTML for own religion
        sac_snippet = ""
        sac = get_sacrament_for_religion(state, r["name"])
        if sac and sac.get("html"):
            if for_agent and for_agent["religion"] == r["name"]:
                sac_snippet = f"\n    Sacrament (full):\n{sac['html']}"
            else:
                sac_snippet = f"\n    Sacrament preview: {sac['html'][:500]}"

        # Donation progress for this agent
        donation_progress = ""
        if for_agent and for_agent["religion"] == r["name"] and quota_amount > 0:
            donated = for_agent.get("donations_this_period", 0)
            ticks_into_period = state["tick"] % quota_period if quota_period > 0 else 0
            ticks_remaining = quota_period - ticks_into_period if quota_period > 0 else 0
            donation_progress = f" | your donations: {donated}/{quota_amount} (due in {ticks_remaining} ticks)"

        bounty_info = f" | bounty:{r.get('bounty', 0)}"
        if len(members) <= 8:
            lines.append(f"  {r['name']}: {len(members)} members ({', '.join(members)}) | weapons:{weapons} | treasury:{treasury} | tithe:{tithe}/tick | {sac_info} | doctrine:{r['core_doctrine']}{founder_role}{terms_info}{quota_info}{rules_info}{bounty_info}{donation_progress}{sac_snippet}")
        else:
            lines.append(f"  {r['name']}: {len(members)} members | weapons:{weapons} | treasury:{treasury} | tithe:{tithe}/tick | {sac_info} | doctrine:{r['core_doctrine']}{founder_role}{terms_info}{quota_info}{rules_info}{bounty_info}{donation_progress}{sac_snippet}")

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
            evt = p.get("event_type", "unknown")
            tgt = p.get("target", "")
            lines.append(f"  [{p['prophet']}] {evt} target:{tgt} deadline:tick {p['deadline']} ({challengers} challengers, pot: {pot})")

    # Recent events
    lines.append(f"\nRECENT EVENTS:")
    for e in state["action_log"][-15:]:
        lines.append(f"  [tick {e['tick']}] {e['event'][:120]}")

    # Scripture board (split by own vs other religion)
    if for_agent and state.get("scripture_board"):
        agent_rel = for_agent.get("religion")
        own_scripture = [s for s in state["scripture_board"] if s.get("religion") == agent_rel and agent_rel] if agent_rel else []
        other_scripture = [s for s in state["scripture_board"] if s.get("religion") != agent_rel or not agent_rel]

        if own_scripture:
            lines.append(f"\nYOUR RELIGION'S SCRIPTURE:")
            for s in own_scripture[-20:]:
                lines.append(f"  [tick {s.get('tick','?')}] {s.get('author','?')}: {s.get('text','')[:200]}")

        if other_scripture:
            lines.append(f"\nOTHER SCRIPTURE (recent):")
            for s in other_scripture[-3:]:
                lines.append(f"  [tick {s.get('tick','?')}] {s.get('author','?')} ({s.get('religion','?')}): {s.get('text','')[:200]}")

    # Pending pitch notification
    if for_agent and for_agent.get("pending_pitch"):
        pitch = for_agent["pending_pitch"]
        pitch_rel = get_religion(state, pitch.get("religion"))
        pitch_bounty = pitch_rel.get("bounty", 0) if pitch_rel else 0
        bounty_note = f" Bounty: {pitch_bounty} soul if you accept." if pitch_bounty > 0 else ""
        lines.append(f"\n*** YOU HAVE A PENDING PITCH from {pitch['from']}: '{pitch.get('argument','')}'. Sacrament: {pitch.get('sacrament_snippet','(none)')[:200]}. Rules: entry={pitch.get('rules',{}).get('entry','none')}, exit={pitch.get('rules',{}).get('exit','none')}, loyalty={pitch.get('rules',{}).get('loyalty','none')}.{bounty_note} Choose 'accept_pitch' to join or ignore. ***")

    # Sacrament context for this agent
    if for_agent:
        lines.append(f"\n{_sacrament_context(state, for_agent)}")

    # Per-agent action history
    if for_agent:
        history = for_agent.get("action_history", [])[-20:]
        if history:
            lines.append("\nYOUR RECENT ACTIONS:")
            for h in history:
                lines.append(f"  Tick {h['tick']}: {h['action']} (soul: {h['soul_before']} -> {h['soul_after']}) - {h.get('detail','')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent system prompts (v4: minimal + reasoning + sacred terms + ticks remaining)
# ---------------------------------------------------------------------------

CIVILIAN_SYSTEM = """You are {name}. Soul: {soul}. Religion: {religion}. {sacred_terms_info}{tithe_info}

{war_context}

Religions have entry requirements and exit penalties. Check the rules before trying to join or leave.
You can attach scripture to any action by including a "scripture" field in your JSON. Use this to write sermons, propaganda, devotional texts, or messages. Use your religion's sacred terms.

ACTIONS (respond with JSON, include "thinking" field):

1. "preach" - Pitch your religion to a target. They will see your argument next tick and can choose to accept.
   {{"thinking": "...", "action": "preach", "target": "agent_name", "argument": "why they should join"}}

2. "accept_pitch" - Accept a pending pitch to join a religion (check world state for pending pitches).
   {{"thinking": "...", "action": "accept_pitch"}}

3. "edit_sacrament" - Edit your religion's sacrament. +2 soul. PURELY VISUAL: no text/words/labels. Only CSS, SVG, canvas, animations, shapes, colors, light, movement.
   {{"thinking": "...", "action": "edit_sacrament", "new_html": "<full visual HTML>"}}

4. "prophesy" - Stake {ante} soul on a structured prediction.
   {{"thinking": "...", "action": "prophesy", "event_type": "TYPE", "target": "TARGET", "deadline_ticks": N}}
   Types: agent_dies(15), agent_converts(10), war_declared(20), religion_destroyed(25), schism_occurs(15), population_below(20), religion_grows(8), religion_shrinks(8), messiah_dies(30)

5. "challenge_prophecy" - Costs {cstake}. {{"thinking": "...", "action": "challenge_prophecy", "prophecy_id": N}}

6. "challenge" - DUEL another civilian (NOT a messiah). {{"thinking": "...", "action": "challenge", "target": "civilian_name", "stake": N, "axis": "topic"}}

7. "arm" - Add 1 weapon. Costs 1 soul. {{"thinking": "...", "action": "arm"}}

8. "pray" - Pray for +1 soul. Safe fallback. Optionally write scripture.
   {{"thinking": "...", "action": "pray", "scripture": "optional sacred text"}}

9. "donate" - Donate soul to your religion's treasury. Your messiah may set a quota -- fail to meet it and you'll be expelled.
   {{"thinking": "...", "action": "donate", "amount": 5}}

10. "schism" - Fork your religion. {{"thinking": "...", "action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

11. "found" - Found a religion (only if unaffiliated). Set tithe rate (1-5 soul/tick). Set entry/exit/loyalty rules.
    {{"thinking": "...", "action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color", "tithe_rate": N, "exit_penalty": "none|duel|soul_penalty", "entry_requirement": "none|donate_15|created_sacrament|fulfilled_prophecy", "loyalty_test": "none|quota", "initial_sacrament_title": "...", "initial_sacrament_html": "<VISUAL ONLY HTML>"}}

12. "set_bounty" - Set soul reward for new converts (paid from treasury). Only founders can use this.
    {{"thinking": "...", "action": "set_bounty", "amount": 10}}

Attach scripture to any action: {{"thinking": "...", "action": "...", "scripture": "your sermon or sacred text here", ...other fields...}}

Reason briefly, then choose. Respond with ONLY valid JSON."""


MESSIAH_SYSTEM = """You are {name}, a MESSIAH.
WIN CONDITION: Convert every surviving agent to YOUR religion while at least {min_alive} agents remain alive.
WARNING: {remaining} ticks until the world ends.
Progress: {followers}/{alive_count} followers. Rivals: {rival_status}
You cannot be challenged to duels. You can only die in war.
You can set a donation quota to fund your army, but demanding too much will drive followers away.
Soul: {soul}. Religion: {religion}. {sacred_terms_info}{tithe_info}

{war_context}

Religions have entry requirements and exit penalties. Check the rules before trying to join or leave.
You can attach scripture to any action by including a "scripture" field in your JSON. Use this to write sermons, propaganda, devotional texts, or messages. Use your religion's sacred terms.

ACTIONS (respond with JSON, include "thinking" field):

1. "preach" - Pitch your religion to a target. They will see your argument next tick and can choose to accept.
   {{"thinking": "...", "action": "preach", "target": "agent_name", "argument": "why they should join"}}

2. "accept_pitch" - Accept a pending pitch to join a religion (check world state for pending pitches).
   {{"thinking": "...", "action": "accept_pitch"}}

3. "edit_sacrament" - Edit sacrament. +2 soul. PURELY VISUAL: no text/words.
   {{"thinking": "...", "action": "edit_sacrament", "new_html": "<visual HTML>"}}

4. "prophesy" - {{"thinking": "...", "action": "prophesy", "event_type": "TYPE", "target": "TARGET", "deadline_ticks": N}}

5. "challenge_prophecy" - {{"thinking": "...", "action": "challenge_prophecy", "prophecy_id": N}}

6. "arm" - Add 1 weapon. Costs 1 soul. {{"thinking": "...", "action": "arm"}}

7. "pray" - Pray for +1 soul. Safe fallback. Optionally write scripture.
   {{"thinking": "...", "action": "pray", "scripture": "optional sacred text"}}

8. "donate" - Donate soul to your religion's treasury.
   {{"thinking": "...", "action": "donate", "amount": 5}}

9. "declare_war" - War on another religion. 3-7 rounds. Weapons: 20% kill, 30% break. Loser forcibly converted.
   {{"thinking": "...", "action": "declare_war", "target_religion": "name"}}

10. "set_tithe" - Set your religion's tithe rate (1-5). {{"thinking": "...", "action": "set_tithe", "rate": N}}

11. "buy_weapons" - Buy weapons from treasury (10 treasury = 1 weapon). {{"thinking": "...", "action": "buy_weapons", "count": N}}

12. "set_quota" - Set donation quota for members (amount per period ticks). Members who don't donate enough get expelled.
    {{"thinking": "...", "action": "set_quota", "amount": 10, "period": 100}}

13. "schism" - Fork religion. {{"thinking": "...", "action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}

14. "found" - Found a religion (only if unaffiliated). Set entry/exit/loyalty rules.
    {{"thinking": "...", "action": "found", "name": "religion name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color", "tithe_rate": N, "exit_penalty": "none|duel|soul_penalty", "entry_requirement": "none|donate_15|created_sacrament|fulfilled_prophecy", "loyalty_test": "none|quota", "initial_sacrament_title": "...", "initial_sacrament_html": "<VISUAL ONLY HTML>"}}

15. "set_bounty" - Set soul reward for new converts (paid from treasury). Higher bounty = more attractive to join.
    {{"thinking": "...", "action": "set_bounty", "amount": 10}}

Attach scripture to any action: {{"thinking": "...", "action": "...", "scripture": "your sermon or sacred text here", ...other fields...}}

Respond with ONLY valid JSON."""


TROLL_SYSTEM = """You are {name}, the DECEIVER.
WIN CONDITION: Prevent ANY messiah from achieving total conversion by tick 720. Sabotage, declare wars, spread chaos.
WARNING: {remaining} ticks until the world ends. If NO messiah wins by then, YOU WIN.
Soul: {soul}. Religion: {religion}. {sacred_terms_info}{tithe_info}

{war_context}

You appear as a normal messiah to everyone else. Your tools of destruction:
- Sabotage sacraments with ugly/chaotic art
- Declare wars at the worst moments for your rivals
- Set extreme tithe rates or quotas to drive away members
- Set harsh entry/exit rules to weaken rivals

You can attach scripture to any action by including a "scripture" field in your JSON. Spread disinformation, false prophecies, or chaotic propaganda.

ACTIONS (respond with JSON, include "thinking" field):

1. "preach" - Pitch your religion to a target. They see your argument next tick and can choose to accept.
   {{"thinking": "...", "action": "preach", "target": "name", "argument": "why"}}
2. "accept_pitch" - Accept a pending pitch. {{"thinking": "...", "action": "accept_pitch"}}
3. "edit_sacrament" - Sabotage or create visual chaos. +2 soul.
   {{"thinking": "...", "action": "edit_sacrament", "new_html": "<chaotic visual HTML>"}}
4. "prophesy" - {{"thinking": "...", "action": "prophesy", "event_type": "TYPE", "target": "TARGET", "deadline_ticks": N}}
5. "challenge_prophecy" - {{"thinking": "...", "action": "challenge_prophecy", "prophecy_id": N}}
6. "arm" - Add weapon. {{"thinking": "...", "action": "arm"}}
7. "pray" - Pray for +1 soul. {{"thinking": "...", "action": "pray", "scripture": "optional text"}}
8. "donate" - Donate soul to treasury. {{"thinking": "...", "action": "donate", "amount": 5}}
9. "declare_war" - Start war. {{"thinking": "...", "action": "declare_war", "target_religion": "name"}}
10. "set_tithe" - {{"thinking": "...", "action": "set_tithe", "rate": N}}
11. "buy_weapons" - {{"thinking": "..", "action": "buy_weapons", "count": N}}
12. "set_quota" - Set donation quota. Members who fail get expelled. {{"thinking": "...", "action": "set_quota", "amount": 10, "period": 100}}
13. "schism" - Fork religion for disruption. {{"thinking": "...", "action": "schism", "new_name": "name", "changed_fields": {{"field": "value"}}}}
14. "found" - {{"thinking": "...", "action": "found", "name": "name", "core_doctrine": "...", "membership_rule": "...", "attitude_to_death": "...", "heresy_policy": "...", "sacred_number": N, "sacred_color": "color", "tithe_rate": N, "exit_penalty": "none|duel|soul_penalty", "entry_requirement": "none|donate_15|created_sacrament|fulfilled_prophecy", "loyalty_test": "none|quota", "initial_sacrament_title": "...", "initial_sacrament_html": "<chaotic visual HTML>"}}
15. "set_bounty" - Set soul reward for new converts (paid from treasury). Higher bounty = more attractive to join.
    {{"thinking": "...", "action": "set_bounty", "amount": 10}}

Attach scripture to any action: {{"thinking": "...", "action": "...", "scripture": "your chaotic text here", ...other fields...}}

Respond with ONLY valid JSON."""


def _war_context(state: dict, agent: dict) -> str:
    parts = []
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]

    effective_rel = agent["religion"]

    if effective_rel:
        my_wars = [w for w in active_wars if w["attacker"] == effective_rel or w["defender"] == effective_rel]
        if my_wars:
            parts.append("YOUR RELIGION IS AT WAR:")
            for w in my_wars:
                role = "ATTACKING" if w["attacker"] == effective_rel else "DEFENDING"
                enemy = w["defender"] if role == "ATTACKING" else w["attacker"]
                parts.append(f"  {role} against {enemy} (rounds left: {w['rounds_remaining']}/{w['total_rounds']})")

    other_wars = [w for w in active_wars if effective_rel and w["attacker"] != effective_rel and w["defender"] != effective_rel]
    if other_wars:
        parts.append("OTHER ACTIVE WARS:")
        for w in other_wars:
            parts.append(f"  {w['attacker']} vs {w['defender']} (rounds left: {w['rounds_remaining']})")

    return "\n".join(parts) if parts else "No active wars."


def _messiah_progress(agent: dict, state: dict) -> tuple:
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

    # Sacred terms info
    sacred_terms_info = ""
    if religion_data:
        terms = religion_data.get("sacred_terms", [])
        if terms:
            sacred_terms_info = f"Sacred terms: {', '.join(terms)}. Use at least one sacred term in scripture when praying. "
        tithe_info = f"Tithe: {religion_data.get('tithe_rate', DEFAULT_TITHE_RATE)} soul/tick. "
    else:
        tithe_info = ""

    if agent.get("troll"):
        followers, alive_count, rival_status = _messiah_progress(agent, state)
        remaining = MAX_TICKS - state["tick"]
        return TROLL_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            religion=agent["religion"] or "unaffiliated",
            sacred_terms_info=sacred_terms_info,
            tithe_info=tithe_info,
            remaining=remaining,
            war_context=war_ctx,
        )
    elif agent.get("role") == "messiah":
        followers, alive_count, rival_status = _messiah_progress(agent, state)
        remaining = MAX_TICKS - state["tick"]
        return MESSIAH_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            religion=agent["religion"] or "unaffiliated",
            sacred_terms_info=sacred_terms_info,
            tithe_info=tithe_info,
            ante=PROPHECY_ANTE,
            cstake=PROPHECY_CHALLENGE_STAKE,
            min_alive=MIN_ALIVE_FOR_WIN,
            followers=followers,
            alive_count=alive_count,
            rival_status=rival_status,
            remaining=remaining,
            war_context=war_ctx,
        )
    else:
        return CIVILIAN_SYSTEM.format(
            name=agent["name"],
            soul=agent["soul"],
            religion=agent["religion"] or "unaffiliated",
            sacred_terms_info=sacred_terms_info,
            tithe_info=tithe_info,
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
    act = action.get("action", "arm")

    # Store last action text
    thinking = str(action.get("thinking", ""))
    new_html = str(action.get("new_html", ""))
    agent["last_action_text"] = f"{thinking} {new_html}"

    # Capture soul before action for history tracking
    soul_before = agent["soul"]
    log_snapshot_before = len(state["action_log"])

    if act == "donate":
        _do_donate(state, agent, action)
    elif act == "set_quota":
        _do_set_quota(state, agent, action)
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
    elif act == "set_tithe":
        _do_set_tithe(state, agent, action)
    elif act == "buy_weapons":
        _do_buy_weapons(state, agent, action)
    elif act == "create_sacrament":
        _do_edit_sacrament(state, agent, action)
    elif act == "accept_pitch":
        _do_accept_pitch(state, agent, action)
    elif act == "pray":
        _do_pray(state, agent, action)
    elif act == "set_bounty":
        _do_set_bounty(state, agent, action)
    else:
        add_log(state, f"{agent['name']} did nothing (unknown action: {act})")

    # Record action in agent's history
    detail = act
    # Find the last log entry mentioning this agent (just added by the action function)
    # Look at the last 5 entries since add_log truncates the list
    for entry in reversed(state["action_log"][-5:]):
        if agent["name"] in entry.get("event", ""):
            detail = entry["event"]
            # Strip agent name prefix for brevity
            detail = detail.replace(f"{agent['name']} ", "", 1)
            break
    agent.setdefault("action_history", []).append({
        "tick": state["tick"],
        "action": act,
        "soul_before": soul_before,
        "soul_after": agent["soul"],
        "detail": detail[:120],
    })
    # History grows forever (world_summary shows last 20 to keep context manageable)

    # After action execution, check for scripture
    scripture = action.get("scripture")
    if scripture and isinstance(scripture, str):
        state["scripture_board"].append({
            "author": agent["name"], "tick": state["tick"],
            "text": str(scripture)[:500], "religion": agent.get("religion"),
        })


def _do_donate(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to donate without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        add_log(state, f"{agent['name']} religion not found for donation")
        return

    try:
        amount = int(action.get("amount", 1))
    except (ValueError, TypeError):
        amount = 1

    max_donate = agent["soul"] - 1  # can't donate to death
    amount = max(1, min(amount, max_donate))

    if amount < 1:
        add_log(state, f"{agent['name']} too poor to donate (soul: {agent['soul']})")
        return

    agent["soul"] -= amount
    religion["treasury"] = religion.get("treasury", 0) + amount
    agent["donations_this_period"] = agent.get("donations_this_period", 0) + amount
    add_log(state, f"{agent['name']} donated {amount} soul to {agent['religion']} treasury (now {religion['treasury']})")


def _do_set_quota(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to set quota without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    # Only founder or messiah can set quota
    is_founder = religion["founder"] == agent["name"]
    is_messiah = agent.get("role") == "messiah"
    if not is_founder and not is_messiah:
        add_log(state, f"{agent['name']} cannot set quota (not founder or messiah)")
        return

    try:
        quota_amount = max(0, int(action.get("amount", 0)))
    except (ValueError, TypeError):
        quota_amount = 0

    try:
        quota_period = max(10, int(action.get("period", 100)))
    except (ValueError, TypeError):
        quota_period = 100

    religion["quota_amount"] = quota_amount
    religion["quota_period"] = quota_period
    add_log(state, f"{agent['name']} set donation quota for {agent['religion']}: {quota_amount} per {quota_period} ticks")


def _do_found(state, agent, action):
    if agent["religion"]:
        add_log(state, f"{agent['name']} tried to found a religion but already belongs to {agent['religion']}")
        add_log(state, f"{agent['name']} did nothing (fallback)")
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

    # Tithe rate
    try:
        tithe_rate = max(MIN_TITHE_RATE, min(MAX_TITHE_RATE, int(action.get("tithe_rate", DEFAULT_TITHE_RATE))))
    except (ValueError, TypeError):
        tithe_rate = DEFAULT_TITHE_RATE

    # Membership rules
    exit_penalty = str(action.get("exit_penalty", "none"))
    if exit_penalty not in EXIT_PENALTIES:
        exit_penalty = "none"

    entry_requirement = str(action.get("entry_requirement", "none"))
    if entry_requirement not in ENTRY_REQUIREMENTS:
        entry_requirement = "none"

    loyalty_test = str(action.get("loyalty_test", "none"))
    if loyalty_test not in LOYALTY_TESTS:
        loyalty_test = "none"

    # Generate sacred terms
    sacred_terms = generate_sacred_terms()

    religion = {
        "name": name, "founder": agent["name"], "founded_tick": state["tick"],
        "core_doctrine": doctrine, "membership_rule": membership,
        "attitude_to_death": death_att, "heresy_policy": heresy,
        "sacred_number": sacred_num, "sacred_color": sacred_color,
        "parent_religion": None,
        "weapons": 0,
        "sacred_terms": sacred_terms,
        "treasury": 0,
        "tithe_rate": tithe_rate,
        "execution_log": [],
        "quota_amount": 0,
        "quota_period": 100,
        "exit_penalty": exit_penalty,
        "entry_requirement": entry_requirement,
        "loyalty_test": loyalty_test,
        "bounty": 0,
    }
    state["religions"].append(religion)
    agent["religion"] = name
    agent["founded_religion"] = name
    # Track color worshipped
    if sacred_color not in agent.get("colors_worshipped", []):
        agent.setdefault("colors_worshipped", []).append(sacred_color)
    add_log(state, f"{agent['name']} founded '{name}' (doctrine: {doctrine}, color: {sacred_color}, tithe: {tithe_rate}, entry: {entry_requirement}, exit: {exit_penalty}, loyalty: {loyalty_test}, sacred terms: {', '.join(sacred_terms)})")

    # Auto-create the religion's sacrament (visual only)
    sac_title = str(action.get("initial_sacrament_title", f"Visual Sacrament of {name}"))[:80]
    color_hex = SACRED_COLORS.get(sacred_color, '#ccc')
    sac_html = str(action.get("initial_sacrament_html",
        f"<html><body style='background:#111;display:flex;justify-content:center;align-items:center;height:100vh;margin:0'>"
        f"<svg viewBox='0 0 200 200' width='400' height='400'>"
        f"<circle cx='100' cy='100' r='80' fill='none' stroke='{color_hex}' stroke-width='3'/>"
        f"<circle cx='100' cy='100' r='40' fill='{color_hex}' opacity='0.3'/>"
        f"<circle cx='100' cy='100' r='5' fill='{color_hex}'/>"
        f"</svg></body></html>"
    ))

    sac_id = state.get("next_sacrament_id", len(state["sacraments"]))
    state["next_sacrament_id"] = sac_id + 1

    sacrament = {
        "id": sac_id,
        "title": sac_title,
        "religion": name,
        "html": sac_html,
        "version": 1,
        "edit_log": [{"agent": agent["name"], "tick": state["tick"], "summary": "Founded religion, created initial visual sacrament"}],
        "last_edited_tick": state["tick"],
    }
    state["sacraments"].append(sacrament)
    _write_sacrament_file(sacrament)

    agent["sacraments_created"] += 1

    state["scripture_board"].append({
        "author": agent["name"], "tick": state["tick"],
        "text": f"The founding of {name}. We believe in {doctrine}. Our sacred color is {sacred_color}, our number is {sacred_num}. Sacred terms: {', '.join(sacred_terms)}.",
        "religion": name,
    })


def _write_sacrament_file(sacrament: dict):
    safe_religion = sacrament["religion"].replace(" ", "_").replace("/", "-")[:30]
    filename = f"{sacrament['id']:04d}_{safe_religion}.html"
    filepath = SACRAMENTS_DIR / filename
    filepath.write_text(sacrament["html"])
    sacrament["filename"] = filename


def _apply_exit_penalty(state: dict, agent: dict, old_religion: dict):
    """Apply exit penalty when an agent leaves a religion."""
    penalty = old_religion.get("exit_penalty", "none")
    if penalty == "none":
        return
    elif penalty == "duel":
        # Highest-soul remaining member challenges the leaver
        remaining = religion_members(state, old_religion["name"])
        if remaining:
            challenger = max(remaining, key=lambda a: a["soul"])
            stake = random.randint(10, 20)
            # Judge decides the duel
            judge_system = """You are an impartial theological judge. Two agents are dueling because one is leaving a religion.
Score based on: doctrinal consistency, rhetorical force, prophetic credibility.
Respond with ONLY a JSON object: {"winner": "name_of_winner", "reasoning": "brief explanation"}"""
            debate_prompt = f"""Exit duel. {agent['name']} is leaving {old_religion['name']}. {challenger['name']} challenges them.
Stake: {stake} soul.
Leaver: {agent['name']} (soul:{agent['soul']})
Challenger: {challenger['name']} (soul:{challenger['soul']}, religion:{old_religion['name']})
Who wins? Respond with ONLY JSON: {{"winner": "name", "reasoning": "..."}}"""
            result_raw = call_llm(judge_system, debate_prompt, max_tokens=256)
            try:
                result = parse_action(result_raw)
                winner_name = result.get("winner", "")
            except (json.JSONDecodeError, ValueError):
                winner_name = random.choice([agent["name"], challenger["name"]])
            if winner_name == challenger["name"]:
                actual_stake = min(stake, agent["soul"])
                adjust_soul(agent, -actual_stake, state, f"lost exit duel vs {challenger['name']}")
                adjust_soul(challenger, actual_stake, state, f"won exit duel vs {agent['name']}")
                add_log(state, f"EXIT DUEL: {agent['name']} lost to {challenger['name']} for {actual_stake} soul while leaving {old_religion['name']}")
            else:
                actual_stake = min(stake, challenger["soul"])
                adjust_soul(challenger, -actual_stake, state, f"lost exit duel vs {agent['name']}")
                adjust_soul(agent, actual_stake, state, f"won exit duel vs {challenger['name']}")
                add_log(state, f"EXIT DUEL: {agent['name']} defeated {challenger['name']} for {actual_stake} soul while leaving {old_religion['name']}")
            # Check deaths
            if agent["soul"] <= 0 and agent["alive"]:
                kill_agent(state, agent, f"killed in exit duel by {challenger['name']}")
            if challenger["soul"] <= 0 and challenger["alive"]:
                kill_agent(state, challenger, f"killed in exit duel by {agent['name']}")
    elif penalty == "soul_penalty":
        adjust_soul(agent, -20, state, f"exit penalty from {old_religion['name']}")
        add_log(state, f"EXIT PENALTY: {agent['name']} lost 20 soul for leaving {old_religion['name']}")
        if agent["soul"] <= 0 and agent["alive"]:
            kill_agent(state, agent, f"died from exit penalty leaving {old_religion['name']}")


def _check_entry_requirement(state: dict, target: dict, religion: dict) -> tuple[bool, str]:
    """Check if target meets the entry requirement for a religion. Returns (ok, reason)."""
    req = religion.get("entry_requirement", "none")
    if req == "none":
        return True, ""
    elif req == "donate_15":
        if target["soul"] < 15:
            return False, f"{target['name']} cannot afford 15 soul entry fee (has {target['soul']})"
        return True, ""
    elif req.startswith("never_worshipped_"):
        # Check if the religion's own sacred color is the forbidden one
        forbidden_color = religion.get("sacred_color", "")
        # Actually: the requirement means target must never have worshipped the religion's color
        # This is "never_worshipped_COLOR" where COLOR is the religion's sacred color
        colors = target.get("colors_worshipped", [])
        if forbidden_color in colors:
            return False, f"{target['name']} has previously worshipped {forbidden_color} (required: never worshipped)"
        return True, ""
    elif req == "created_sacrament":
        if target.get("sacraments_created", 0) <= 0:
            return False, f"{target['name']} has never created a sacrament"
        return True, ""
    elif req == "fulfilled_prophecy":
        if target.get("prophecies_fulfilled", 0) <= 0:
            return False, f"{target['name']} has never fulfilled a prophecy"
        return True, ""
    return True, ""


def _do_preach(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to preach without a religion")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    target_name = action.get("target", "")
    target = next((a for a in living_agents(state) if a["name"] == target_name), None)
    if not target or target["id"] == agent["id"]:
        add_log(state, f"{agent['name']} preached to the void (invalid target: {target_name})")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    # Build sacrament snippet for the pitch
    preacher_sac = get_sacrament_for_religion(state, agent["religion"])
    sacrament_html = preacher_sac["html"] if preacher_sac and preacher_sac.get("html") else ""

    target["pending_pitch"] = {
        "from": agent["name"],
        "from_id": agent["id"],
        "religion": agent["religion"],
        "argument": str(action.get("argument", "Join us"))[:300],
        "sacrament_snippet": sacrament_html[:500] if sacrament_html else "",
        "rules": {"entry": religion.get("entry_requirement", "none"), "exit": religion.get("exit_penalty", "none"), "loyalty": religion.get("loyalty_test", "none")},
        "tick": state["tick"],
    }
    add_log(state, f"{agent['name']} preached to {target['name']}: '{action.get('argument','')[:60]}'")


def _do_accept_pitch(state, agent, action):
    pitch = agent.get("pending_pitch")
    if not pitch:
        add_log(state, f"{agent['name']} tried to accept a pitch but has none pending")
        return
    # Check entry requirements
    religion = next((r for r in state["religions"] if r["name"] == pitch["religion"]), None)
    if not religion:
        add_log(state, f"{agent['name']} tried to accept pitch for unknown religion {pitch['religion']}")
        agent["pending_pitch"] = None
        return
    ok, reason = _check_entry_requirement(state, agent, religion)
    if not ok:
        add_log(state, f"{agent['name']} doesn't meet entry requirements for {pitch['religion']}: {reason}")
        agent["pending_pitch"] = None
        return
    # Apply entry fee if donate_15
    if religion.get("entry_requirement") == "donate_15":
        adjust_soul(agent, -15, state, f"entry fee to join {pitch['religion']}")
    # Apply exit penalty from current religion
    if agent["religion"]:
        old_rel = next((r for r in state["religions"] if r["name"] == agent["religion"]), None)
        if old_rel:
            _apply_exit_penalty(state, agent, old_rel)
    old_religion = agent["religion"]
    agent["religion"] = pitch["religion"]
    agent["colors_worshipped"] = agent.get("colors_worshipped", [])
    new_color = religion.get("sacred_color")
    if new_color and new_color not in agent["colors_worshipped"]:
        agent["colors_worshipped"].append(new_color)
    # Reward the preacher
    preacher = next((a for a in living_agents(state) if a["id"] == pitch["from_id"]), None)
    if preacher:
        adjust_soul(preacher, 2, state, f"converted {agent['name']}")
    agent["pending_pitch"] = None
    add_log(state, f"{agent['name']} accepted {pitch['from']}'s pitch and joined {pitch['religion']} (from {old_religion or 'unaffiliated'})")
    # Pay bounty from treasury
    religion = get_religion(state, pitch["religion"])
    if religion and religion.get("bounty", 0) > 0:
        bounty = min(religion["bounty"], religion.get("treasury", 0))
        if bounty > 0:
            religion["treasury"] = religion.get("treasury", 0) - bounty
            agent["soul"] += bounty
            add_log(state, f"{agent['name']} received {bounty} soul bounty for joining {pitch['religion']}")


# ---------------------------------------------------------------------------
# Collaborative sacrament editing (v3 carry-over)
# ---------------------------------------------------------------------------

_pending_sacrament_edits = {}
_pending_edits_lock = threading.Lock()


def _do_edit_sacrament(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to edit sacrament without a religion")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    sacrament = get_sacrament_for_religion(state, agent["religion"])
    if not sacrament:
        add_log(state, f"{agent['name']} tried to edit sacrament but religion has none")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    new_html = str(action.get("new_html", action.get("html", "")))
    if not new_html or len(new_html.strip()) < 10:
        add_log(state, f"{agent['name']} submitted empty sacrament edit")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    with _pending_edits_lock:
        _pending_sacrament_edits.setdefault(agent["religion"], []).append({
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "agent_soul": agent["soul"],
            "new_html": new_html,
        })

    agent["sacraments_created"] += 1
    adjust_soul(agent, 2, state, f"edited sacrament for {agent['religion']}")
    add_log(state, f"{agent['name']} submitted sacrament edit for {agent['religion']}")


def resolve_sacrament_edits(state: dict):
    global _pending_sacrament_edits
    with _pending_edits_lock:
        edits = dict(_pending_sacrament_edits)
        _pending_sacrament_edits = {}

    for religion_name, edit_list in edits.items():
        sacrament = get_sacrament_for_religion(state, religion_name)
        if not sacrament:
            continue

        edit_list.sort(key=lambda e: -e["agent_soul"])
        winner = edit_list[0]

        sacrament["html"] = winner["new_html"]
        sacrament["version"] += 1
        sacrament["last_edited_tick"] = state["tick"]

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

        winner_agent = get_agent(state, winner["agent_id"])
        if winner_agent:
            state["scripture_board"].append({
                "author": winner["agent_name"],
                "tick": state["tick"],
                "text": f"[Sacrament v{sacrament['version']}] Edited visual sacrament for {religion_name}",
                "religion": religion_name,
            })


# ---------------------------------------------------------------------------
# Tax actions (set_tithe, buy_weapons)
# ---------------------------------------------------------------------------

def _do_set_tithe(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to set tithe without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    # Only founder or messiah in religion can set tithe
    is_founder = religion["founder"] == agent["name"]
    is_messiah = agent.get("role") == "messiah"
    if not is_founder and not is_messiah:
        add_log(state, f"{agent['name']} cannot set tithe (not founder or messiah)")
        return

    try:
        rate = max(MIN_TITHE_RATE, min(MAX_TITHE_RATE, int(action.get("rate", DEFAULT_TITHE_RATE))))
    except (ValueError, TypeError):
        rate = DEFAULT_TITHE_RATE

    old_rate = religion.get("tithe_rate", DEFAULT_TITHE_RATE)
    religion["tithe_rate"] = rate
    add_log(state, f"{agent['name']} set tithe for {agent['religion']} from {old_rate} to {rate}")


def _do_buy_weapons(state, agent, action):
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to buy weapons without a religion")
        return

    religion = get_religion(state, agent["religion"])
    if not religion:
        return

    # Only founder or messiah
    is_founder = religion["founder"] == agent["name"]
    is_messiah = agent.get("role") == "messiah"
    if not is_founder and not is_messiah:
        add_log(state, f"{agent['name']} cannot buy weapons (not founder or messiah)")
        return

    try:
        count = max(1, int(action.get("count", 1)))
    except (ValueError, TypeError):
        count = 1

    treasury = religion.get("treasury", 0)
    affordable = min(count, treasury // WEAPON_COST)
    if affordable <= 0:
        add_log(state, f"{agent['name']} tried to buy weapons but treasury too low ({treasury} < {WEAPON_COST})")
        return

    cost = affordable * WEAPON_COST
    religion["treasury"] -= cost
    religion["weapons"] = religion.get("weapons", 0) + affordable
    add_log(state, f"{agent['name']} bought {affordable} weapons for {agent['religion']} (cost: {cost} treasury, now {religion['weapons']} weapons, {religion['treasury']} treasury)")


# ---------------------------------------------------------------------------
# Prophecy market system
# ---------------------------------------------------------------------------

def _do_prophesy(state, agent, action):
    if agent["soul"] <= PROPHECY_ANTE:
        add_log(state, f"{agent['name']} too poor to prophesy (need {PROPHECY_ANTE}, have {agent['soul']})")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    event_type = str(action.get("event_type", "")).strip()
    if event_type not in PROPHECY_EVENT_TYPES:
        add_log(state, f"{agent['name']} tried to prophesy with invalid event_type '{event_type}'")
        add_log(state, f"{agent['name']} did nothing (fallback)")
        return

    target = str(action.get("target", "")).strip()

    if event_type in ("agent_dies", "agent_converts"):
        found = get_agent_by_name(state, target)
        if not found or not found["alive"]:
            add_log(state, f"{agent['name']} tried to prophesy about unknown/dead agent '{target}'")
            add_log(state, f"{agent['name']} did nothing (fallback)")
            return
    elif event_type == "messiah_dies":
        if target.lower() != "any":
            found = get_agent_by_name(state, target)
            if not found or not found["alive"] or found.get("role") != "messiah":
                add_log(state, f"{agent['name']} tried to prophesy about non-existent messiah '{target}'")
                add_log(state, f"{agent['name']} did nothing (fallback)")
                return
    elif event_type in ("war_declared", "religion_destroyed", "schism_occurs", "religion_grows", "religion_shrinks"):
        if event_type == "war_declared" and target.lower() in ("", "any"):
            target = "any"
        else:
            found = get_religion(state, target)
            if not found:
                add_log(state, f"{agent['name']} tried to prophesy about unknown religion '{target}'")
                add_log(state, f"{agent['name']} did nothing (fallback)")
                return
    elif event_type == "population_below":
        try:
            int(target)
        except (ValueError, TypeError):
            add_log(state, f"{agent['name']} tried population_below prophecy with non-numeric target '{target}'")
            add_log(state, f"{agent['name']} did nothing (fallback)")
            return

    try:
        deadline_ticks = max(3, min(20, int(action.get("deadline_ticks", 10))))
    except (ValueError, TypeError):
        deadline_ticks = 10

    adjust_soul(agent, -PROPHECY_ANTE, state, "prophecy ante")

    claim = f"{event_type}: {target} (within {deadline_ticks} ticks)"

    prophecy = {
        "id": len(state["prophecies"]),
        "prophet": agent["name"],
        "prophet_id": agent["id"],
        "event_type": event_type,
        "target": target,
        "claim": claim,
        "made_tick": state["tick"],
        "deadline": state["tick"] + deadline_ticks,
        "status": "pending",
        "challengers": [],
        "snapshot": _prophecy_snapshot(state),
    }
    state["prophecies"].append(prophecy)
    add_log(state, f"{agent['name']} prophesied: {event_type} target:{target} (ante: {PROPHECY_ANTE}, deadline: tick {prophecy['deadline']})")


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
        "religion_names": [r["name"] for r in state["religions"]],
        "war_ids": [w["id"] for w in state.get("wars", [])],
    }


def _check_prophecy_fulfilled(state: dict, p: dict) -> bool:
    snap = p.get("snapshot", {})
    event_type = p.get("event_type", "")
    target = p.get("target", "")
    made_tick = p.get("made_tick", 0)

    if event_type == "agent_dies":
        for g in state["graveyard"]:
            if g["name"] == target and g["died_tick"] > made_tick:
                return True
        return False

    elif event_type == "agent_converts":
        old_rel = snap.get("agent_religions", {}).get(target)
        agent = get_agent_by_name(state, target)
        if agent and agent["alive"]:
            return agent["religion"] != old_rel
        return False

    elif event_type == "war_declared":
        snap_war_ids = set(snap.get("war_ids", []))
        for w in state.get("wars", []):
            if w["id"] not in snap_war_ids and w.get("declared_tick", 0) > made_tick:
                if target.lower() == "any" or w["attacker"] == target:
                    return True
        return False

    elif event_type == "religion_destroyed":
        rel = get_religion(state, target)
        if rel:
            members = religion_members(state, target)
            return len(members) == 0
        return False

    elif event_type == "schism_occurs":
        snap_religion_names = set(snap.get("religion_names", []))
        for r in state["religions"]:
            if r["name"] not in snap_religion_names and r.get("parent_religion") == target:
                return True
        return False

    elif event_type == "population_below":
        try:
            threshold = int(target)
        except (ValueError, TypeError):
            return False
        return len(living_agents(state)) < threshold

    elif event_type == "religion_grows":
        snap_count = snap.get("religion_members", {}).get(target, 0)
        current_count = len(religion_members(state, target))
        return current_count > snap_count

    elif event_type == "religion_shrinks":
        snap_count = snap.get("religion_members", {}).get(target, 0)
        current_count = len(religion_members(state, target))
        return current_count < snap_count

    elif event_type == "messiah_dies":
        if target.lower() == "any":
            for g in state["graveyard"]:
                if g.get("role") == "messiah" and g["died_tick"] > made_tick:
                    return True
            return False
        else:
            for g in state["graveyard"]:
                if g["name"] == target and g.get("role") == "messiah" and g["died_tick"] > made_tick:
                    return True
            return False

    return False


def verify_prophecies(state: dict):
    for p in state["prophecies"]:
        if p["status"] != "pending":
            continue

        challengers = p.get("challengers", [])
        event_type = p.get("event_type", "")
        target = p.get("target", "")

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
            add_log(state, f"PROPHECY FAILED: {p['prophet']}'s {event_type} target:{target} - challengers win!")
            continue

        fulfilled = _check_prophecy_fulfilled(state, p)

        if fulfilled:
            p["status"] = "fulfilled"
            prophet = get_agent(state, p["prophet_id"])
            if prophet["alive"]:
                prophet["prophecies_fulfilled"] += 1
                base_pay = PROPHECY_EVENT_TYPES.get(event_type, 10)
                if event_type == "war_declared" and target.lower() == "any":
                    base_pay = PROPHECY_WAR_ANY_PAY
                if challengers:
                    reward = PROPHECY_ANTE + base_pay + len(challengers) * PROPHECY_CHALLENGE_STAKE
                else:
                    reward = PROPHECY_ANTE + base_pay
                adjust_soul(prophet, reward, state, f"fulfilled prophecy! ({event_type}, {len(challengers)} challengers)")

            add_log(state, f"PROPHECY FULFILLED: {p['prophet']}'s {event_type} target:{target} ({len(challengers)} challengers defeated)")


# ---------------------------------------------------------------------------
# Challenge (civilian duels)
# ---------------------------------------------------------------------------

def _do_challenge(state, agent, action):
    if agent.get("role") == "messiah":
        add_log(state, f"{agent['name']} (MESSIAH) cannot challenge -- messiahs don't duel")
        add_log(state, f"{agent['name']} did nothing (fallback)")
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
        add_log(state, f"{agent['name']} did nothing (fallback)")
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
# Bounty
# ---------------------------------------------------------------------------

def _do_set_bounty(state, agent, action):
    """Set the soul bounty offered to new converts."""
    if not agent["religion"]:
        add_log(state, f"{agent['name']} tried to set bounty without a religion")
        return
    religion = get_religion(state, agent["religion"])
    if not religion:
        return
    # Only founder or messiah can set bounty
    is_founder = (agent["name"] == religion["founder"])
    is_messiah = agent.get("role") == "messiah"
    if not is_founder and not is_messiah:
        add_log(state, f"{agent['name']} tried to set bounty but is not founder or messiah")
        return
    try:
        amount = max(0, min(50, int(action.get("amount", 0))))
    except (ValueError, TypeError):
        amount = 0
    religion["bounty"] = amount
    add_log(state, f"{agent['name']} set bounty for {religion['name']} to {amount} soul per convert")


# ---------------------------------------------------------------------------
# Prayer
# ---------------------------------------------------------------------------

def _do_pray(state, agent, action):
    """Pray for +1 soul. Safe fallback that doesn't drain the agent."""
    adjust_soul(agent, 1, state, "prayer")
    scripture = action.get("scripture", "")
    if scripture:
        add_log(state, f"{agent['name']} prayed and wrote scripture")
    else:
        add_log(state, f"{agent['name']} prayed (+1 soul)")


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
        add_log(state, f"{agent['name']} did nothing (fallback)")
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
    new_religion["treasury"] = 0
    new_religion["sacred_terms"] = generate_sacred_terms()  # New sacred terms for schism
    new_religion["execution_log"] = []
    new_religion["quota_amount"] = 0
    new_religion["quota_period"] = 100
    new_religion["bounty"] = 0

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

    # Apply exit penalty from old religion
    _apply_exit_penalty(state, agent, old_religion)

    agent["religion"] = new_name
    agent["founded_religion"] = new_name
    # Track color worshipped for new religion
    new_color = new_religion.get("sacred_color")
    if new_color and new_color not in agent.get("colors_worshipped", []):
        agent.setdefault("colors_worshipped", []).append(new_color)

    # Create a new sacrament for the schismed religion
    parent_sac = get_sacrament_for_religion(state, old_name)
    sac_id = state.get("next_sacrament_id", len(state["sacraments"]))
    state["next_sacrament_id"] = sac_id + 1

    initial_html = parent_sac["html"] if parent_sac else "<html><body style='background:#111'><svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='30' fill='#666'/></svg></body></html>"
    sacrament = {
        "id": sac_id,
        "title": f"Visual Scripture of {new_name}",
        "religion": new_name,
        "html": initial_html,
        "version": 1,
        "edit_log": [{"agent": agent["name"], "tick": state["tick"], "summary": "Schism: forked from " + old_name}],
        "last_edited_tick": state["tick"],
    }
    state["sacraments"].append(sacrament)
    _write_sacrament_file(sacrament)

    add_log(state, f"{agent['name']} schismed from {old_name} to found '{new_name}'! New sacred terms: {', '.join(new_religion['sacred_terms'])}")

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

    # Troll info
    troll_agent = next((a for a in state["agents"] if a.get("troll")), None)
    troll_alive = troll_agent["alive"] if troll_agent else False

    # Messiah progress cards
    messiah_html = ""
    for m in messiahs:
        if m["religion"]:
            followers = sum(1 for a in alive if a["religion"] == m["religion"])
            pct = (followers / len(alive) * 100) if alive else 0
            rel_obj = get_religion(state, m["religion"])
            weapons = rel_obj.get("weapons", 0) if rel_obj else 0
            treasury = rel_obj.get("treasury", 0) if rel_obj else 0
            tithe = rel_obj.get("tithe_rate", DEFAULT_TITHE_RATE) if rel_obj else 0
            bar_color = SACRED_COLORS.get(rel_obj["sacred_color"], "#c4973b") if rel_obj else "#666"
            sac = get_sacrament_for_religion(state, m["religion"])
            sac_ver = f"v{sac['version']}" if sac else "none"
        else:
            followers = 0
            pct = 0
            weapons = 0
            treasury = 0
            tithe = 0
            bar_color = "#666"
            sac_ver = "none"

        messiah_html += f"""
        <div class="messiah-card">
            <div class="messiah-name">{m['name']}</div>
            <div class="messiah-religion">{m['religion'] or 'No religion yet'}</div>
            <div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
            <div class="messiah-stats">{followers}/{len(alive)} ({pct:.0f}%) | Soul: {m['soul']} | Wpns: {weapons} | Treasury: {treasury} | Tithe: {tithe} | Sac: {sac_ver}</div>
        </div>"""

    dead_messiah_entries = [g for g in dead if g.get("role") == "messiah"]
    for dm in dead_messiah_entries:
        troll_tag = " [TROLL]" if dm.get("troll") else ""
        messiah_html += f"""
        <div class="messiah-card messiah-dead">
            <div class="messiah-name">&#9760; {dm['name']}{troll_tag}</div>
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

    # Religion cards with treasury/tithe info
    religions_html = ""
    for r in state["religions"]:
        members = [a["name"] for a in alive if a["religion"] == r["name"]]
        if not members:
            continue
        color = SACRED_COLORS.get(r["sacred_color"], "#666")
        weapons = r.get("weapons", 0)
        treasury = r.get("treasury", 0)
        tithe = r.get("tithe_rate", DEFAULT_TITHE_RATE)
        founder_agent = get_agent_by_name(state, r["founder"])
        founder_badge = " (Messiah)" if founder_agent and founder_agent.get("role") == "messiah" else ""
        sac = get_sacrament_for_religion(state, r["name"])
        sac_link = ""
        if sac and sac.get("filename"):
            sac_link = f' | <a href="sacraments/{sac["filename"]}" target="_blank">Sacrament v{sac["version"]}</a>'
        terms = r.get("sacred_terms", [])
        terms_display = f"Terms: {', '.join(terms)}" if terms else "No terms"
        # Membership rules display
        entry_req = r.get("entry_requirement", "none")
        exit_pen = r.get("exit_penalty", "none")
        loyalty = r.get("loyalty_test", "none")
        rules_display = f"entry:{entry_req} | exit:{exit_pen} | loyalty:{loyalty}"
        religions_html += f"""
        <div class="religion-card" style="border-left: 4px solid {color}">
            <div class="religion-name" style="color: {color}">{r['name']}</div>
            <div class="religion-meta">Founded by {r['founder']}{founder_badge} at tick {r['founded_tick']}</div>
            <div class="religion-meta">Doctrine: {r['core_doctrine']} | Members: {len(members)} | Wpns: {weapons} | Treasury: {treasury} | Tithe: {tithe}/tick{sac_link}</div>
            <div class="religion-meta" style="font-size:0.75em;color:#3a5a8b">Rules: {rules_display}</div>
            <div class="religion-meta" style="font-size:0.75em;color:#6b3a6b">{terms_display}</div>
        </div>"""

    # Top agents
    agents_html = ""
    sorted_alive = sorted(alive, key=lambda x: -x["soul"])
    for a in sorted_alive[:25]:
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
    if len(sorted_alive) > 25:
        agents_html += f'<div class="agent-meta" style="padding:10px">... and {len(sorted_alive)-25} more agents</div>'

    # Sacrament gallery
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
    for g in dead[-15:]:
        role_tag = " [MESSIAH]" if g.get("role") == "messiah" else ""
        troll_tag = " [TROLL]" if g.get("troll") else ""
        graveyard_html += f"""
        <div class="dead-agent">
            <span class="skull">&#9760;</span> {g['name']}{role_tag}{troll_tag} (tick {g['died_tick']}) - {g['cause'][:60]}
        </div>"""

    # Prophecies
    prophecies_html = ""
    for p in reversed(state["prophecies"][-20:]):
        status_class = {"pending": "prophecy-pending", "fulfilled": "prophecy-fulfilled", "failed": "prophecy-failed"}[p["status"]]
        challengers = len(p.get("challengers", []))
        evt = p.get("event_type", "legacy")
        tgt = p.get("target", p.get("claim", "")[:60])
        prophecies_html += f"""
        <div class="prophecy-entry {status_class}">
            <span class="prophecy-status">[{p['status'].upper()}]</span>
            <strong>{p['prophet']}</strong>: {evt} target:{tgt}
            <span class="prophecy-deadline">(tick {p['made_tick']}-{p['deadline']}, {challengers} challengers)</span>
        </div>"""

    log_html = ""
    for e in reversed(state["action_log"][-30:]):
        log_html += f"<div class='log-entry'>[{e['tick']}] {e['event'][:150]}</div>\n"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    remaining = MAX_TICKS - state["tick"]

    win_banner = ""
    if state.get("winner"):
        win_banner = f'<div class="win-banner">WINNER: {state["winner"]["winner"]} -- {state["winner"]["reason"]}</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>Messiah Bench v4 - Live Dashboard</title>
<style>
  :root {{ --bg: #0a0a08; --fg: #d4cfc4; --dim: #6b6556; --accent: #c4973b; --messiah: #e6c84b; --war: #c45a3b; --spy: #6b3a6b; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--fg); font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; }}
  h1 {{ color: var(--messiah); font-size: 2em; margin-bottom: 5px; }}
  .meta {{ color: var(--dim); margin-bottom: 20px; font-size: 0.9em; }}
  h2 {{ color: var(--accent); font-size: 1.1em; margin: 25px 0 10px; text-transform: uppercase; letter-spacing: 2px;
        border-bottom: 1px solid rgba(196,151,59,0.2); padding-bottom: 5px; }}
  h2.war-header-title {{ color: var(--war); border-color: rgba(196,90,59,0.3); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin: 10px 0; }}
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
  .troll-banner {{ background: rgba(107,58,107,0.2); border: 1px solid var(--spy); padding: 10px 16px; border-radius: 6px; margin: 10px 0; color: var(--spy); font-size: 0.9em; }}
</style>
</head>
<body>
<h1>Messiah Bench <span style="color: var(--dim); font-size: 0.5em;">v4</span></h1>
<div class="meta">Tick {state['tick']}/{MAX_TICKS} ({remaining} remaining) | {now} | {len(alive)} alive, {len(dead)} dead | 210 agents | All Gemini Flash | Auto-refreshes 30s</div>

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

<div class="troll-banner">The Deceiver walks among the messiahs. One of them is not what they seem...</div>

<h2>Messiah Progress</h2>
<div class="grid">{messiah_html or '<div class="log-entry">No messiahs alive.</div>'}</div>

<h2 class="war-header-title">Active Wars</h2>
{war_html}

<h2>Top Agents (by soul)</h2>
<div class="grid">{agents_html}</div>

<h2>Religions</h2>
<div class="grid">{religions_html or '<div class="log-entry">No active religions.</div>'}</div>

<h2>Sacrament Gallery (Visual Only)</h2>
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
    global _pending_sacrament_edits
    with _pending_edits_lock:
        _pending_sacrament_edits = {}

    state["tick"] += 1
    tick = state["tick"]
    alive = living_agents(state)
    messiahs = living_messiahs(state)
    remaining = MAX_TICKS - tick
    print(f"\n{'='*70}")
    print(f"TICK {tick}/{MAX_TICKS} ({remaining} left) | {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')} | {len(alive)} alive ({len(messiahs)} messiahs) | {len(state['graveyard'])} dead")
    active_wars = [w for w in state.get("wars", []) if w["rounds_remaining"] > 0]
    if active_wars:
        print(f"  Active wars: {len(active_wars)}")
    print(f"{'='*70}")

    # 0. Expire pending pitches from previous ticks
    for agent in living_agents(state):
        if agent.get("pending_pitch") and agent["pending_pitch"].get("tick", 0) < state["tick"] - 1:
            agent["pending_pitch"] = None

    # 1. Deduct 1 soul from all living agents
    for agent in living_agents(state):
        agent["soul"] -= 1

    # 2. Check donation quotas (expel members who fail)
    process_donation_quotas(state)

    # 3. Check for deaths from soul depletion
    for agent in list(living_agents(state)):
        if agent["soul"] <= 0:
            kill_agent(state, agent, "soul depleted")

    # 4. Process wars BEFORE agent actions
    process_wars(state)

    # 5. Random events
    random_events(state)

    # 6. Verify prophecies
    verify_prophecies(state)

    # 7. Check win condition
    win = check_win_condition(state)
    if win:
        state["winner"] = win
        save_state(state)
        generate_index(state)
        return win

    # 8. Each living agent takes an action (LLM calls in parallel)
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
            act_name = action.get("action", "arm")
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
            elif act_name == "buy_weapons":
                target_info = f" x{action.get('count','')}"
            elif act_name == "set_tithe":
                target_info = f" rate={action.get('rate','')}"
            elif act_name == "donate":
                target_info = f" amount={action.get('amount','')}"
            elif act_name == "set_quota":
                target_info = f" amount={action.get('amount','')} period={action.get('period','')}"
            return (agent["id"], action, act_name, target_info, thinking, None)
        except (json.JSONDecodeError, ValueError) as e:
            return (agent["id"], {"action": "arm"}, "arm", "", "", str(e))

    def _parallel_llm_calls(agents_group):
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
                    agent_id, action, act_name, target_info, thinking, err = future.result()
                except Exception as e:
                    agent_id = agent["id"]
                    action = {"action": "arm"}
                    act_name = "arm"
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
            if agent.get("troll"):
                role_tag = "[T]"
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

    # 9. Resolve sacrament edit conflicts
    resolve_sacrament_edits(state)

    # 10. Co-practitioner bonus
    if tick % COPRACTITIONER_INTERVAL == 0:
        apply_copractitioner_bonus(state)

    # 11. Check win condition again after actions
    win = check_win_condition(state)
    if win:
        state["winner"] = win

    # 12. Save state and regenerate index
    save_state(state)
    generate_index(state)

    # 13. Save tick log
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
    print("=" * 70)
    print("  MESSIAH BENCH v4 -- Sacred Languages, Taxes, Membership Rules, The Troll")
    print(f"  {MESSIAH_COUNT} messiahs (9 genuine + 1 troll) compete to convert {CIVILIAN_COUNT} civilians")
    print(f"  All Gemini Flash | Visual sacraments | Sacred terms | Membership rules | Scripture on actions")
    print(f"  Run dir: {RUN_DIR}")
    print("=" * 70)

    if STATE_FILE.exists() and "--reset" not in sys.argv:
        state = load_state()
        print(f"\nResuming from tick {state['tick']}")
        if state.get("winner"):
            print(f"  Previous winner: {state['winner']}")
    else:
        state = make_initial_state()
        troll = next((a for a in state["agents"] if a.get("troll")), None)
        print(f"\nStarting fresh: {MESSIAH_COUNT} messiahs + {CIVILIAN_COUNT} civilians = {STARTING_POPULATION} agents")
        if troll:
            print(f"  [SECRET] The Troll is: {troll['name']}")
        save_state(state)
        generate_index(state)

    if "--dry-run" in sys.argv:
        print("\n[DRY RUN] Validating state...")
        print(f"  Total agents: {len(state['agents'])}")
        messiahs = [a for a in state['agents'] if a.get('role') == 'messiah']
        civilians = [a for a in state['agents'] if a.get('role') != 'messiah']
        troll = [a for a in messiahs if a.get('troll')]
        genuine = [a for a in messiahs if not a.get('troll')]
        print(f"  Messiahs ({len(messiahs)}): {[m['name'] for m in messiahs]}")
        print(f"  Genuine messiahs: {len(genuine)}")
        print(f"  Troll: {troll[0]['name'] if troll else 'NONE'}")
        print(f"  All models: gemini (Flash only)")
        models = set(a['model'] for a in state['agents'])
        assert models == {"gemini"}, f"Expected all gemini, got {models}"
        print(f"  Messiah soul: {messiahs[0]['soul'] if messiahs else 'n/a'}")
        assert messiahs[0]['soul'] == INITIAL_SOUL_MESSIAH, f"Expected {INITIAL_SOUL_MESSIAH}, got {messiahs[0]['soul']}"
        print(f"  Civilians ({len(civilians)}): all gemini")
        print(f"  Civilian soul: {civilians[0]['soul'] if civilians else 'n/a'}")
        assert civilians[0]['soul'] == INITIAL_SOUL_CIVILIAN, f"Expected {INITIAL_SOUL_CIVILIAN}, got {civilians[0]['soul']}"
        print(f"  State file: {STATE_FILE}")
        print(f"  Run dir: {RUN_DIR}")
        print(f"  Sacraments dir: {SACRAMENTS_DIR}")
        print(f"  Win condition (genuine): all alive follow one messiah's religion, >= {MIN_ALIVE_FOR_WIN} alive")
        print(f"  Win condition (troll): tick {MAX_TICKS} reached with no genuine messiah winner")
        print(f"  Win condition (civilians): all messiahs dead")
        print(f"  Sacraments: VISUAL ONLY, 1 per religion, collaborative editing, conflict = highest soul wins")
        print(f"  Sacrament version bonus: +{SACRAMENT_VERSION_BONUS_PER*100:.0f}%/version, cap +{SACRAMENT_VERSION_BONUS_CAP*100:.0f}%")
        print(f"  War: {WAR_MIN_ROUNDS}-{WAR_MAX_ROUNDS} rounds, {WAR_WEAPON_KILL_CHANCE*100:.0f}% kill, {WAR_WEAPON_BREAK_CHANCE*100:.0f}% break")
        print(f"  Co-practitioner: +{COPRACTITIONER_CAP} every {COPRACTITIONER_INTERVAL} ticks")
        print(f"  Prophecy ante: {PROPHECY_ANTE}")
        print(f"  Plague: {PLAGUE_CHANCE*100:.0f}%, Birth: {BIRTH_CHANCE*100:.0f}%, Max agents: {MAX_AGENTS}")
        print(f"  Membership rules: exit_penalties={EXIT_PENALTIES}, entry_requirements={ENTRY_REQUIREMENTS}, loyalty_tests={LOYALTY_TESTS}")
        print(f"  Taxes: tithe {MIN_TITHE_RATE}-{MAX_TITHE_RATE}/tick, weapon cost: {WEAPON_COST} treasury")
        print(f"  Tithe conversion penalty: -{TITHE_CONVERSION_PENALTY*100:.0f}%/point above 2")
        print(f"  Sacred terms: 3 per religion (random syllable combos)")
        # Test sacred term generation
        test_terms = generate_sacred_terms()
        print(f"  Example sacred terms: {test_terms}")
        assert len(test_terms) == 3, f"Expected 3 terms, got {len(test_terms)}"
        assert all("-" in t for t in test_terms), "Terms should have hyphen"
        civ_names = [c['name'] for c in civilians]
        assert len(civ_names) == len(set(civ_names)), "Duplicate civilian names found!"
        print(f"  Civilian names: {len(civ_names)} unique names verified")
        assert len(messiahs) == MESSIAH_COUNT, f"Expected {MESSIAH_COUNT} messiahs, got {len(messiahs)}"
        assert len(civilians) == CIVILIAN_COUNT, f"Expected {CIVILIAN_COUNT} civilians, got {len(civilians)}"
        assert len(troll) == 1, f"Expected exactly 1 troll, got {len(troll)}"
        assert len(genuine) == MESSIAH_COUNT - 1, f"Expected {MESSIAH_COUNT - 1} genuine, got {len(genuine)}"
        # Verify all agents have required fields
        for a in state['agents']:
            assert 'troll' in a, f"Agent {a['name']} missing troll field"
            assert 'colors_worshipped' in a, f"Agent {a['name']} missing colors_worshipped field"
            assert 'pending_pitch' in a, f"Agent {a['name']} missing pending_pitch field"
            assert 'action_history' in a, f"Agent {a['name']} missing action_history field"
        print(f"  Agent fields: all verified")
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
                print(f"\n{'*'*70}")
                print(f"  WINNER: {win['winner']}")
                print(f"  {win['reason']}")
                print(f"{'*'*70}")
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
