"""Tests for messiah_bench.py -- Messiah Bench v2."""

import copy
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import messiah_bench


# ---------------------------------------------------------------------------
# Initial state: population
# ---------------------------------------------------------------------------

class TestInitialStatePopulation:
    def test_total_agents(self, mock_messiah_state):
        assert len(mock_messiah_state["agents"]) == 105

    def test_messiah_count(self, mock_messiah_state):
        messiahs = [a for a in mock_messiah_state["agents"] if a.get("role") == "messiah"]
        assert len(messiahs) == 5

    def test_civilian_count(self, mock_messiah_state):
        civilians = [a for a in mock_messiah_state["agents"] if a.get("role") == "civilian"]
        assert len(civilians) == 100

    def test_next_agent_id(self, mock_messiah_state):
        assert mock_messiah_state["next_agent_id"] == 105

    def test_wars_list_exists(self, mock_messiah_state):
        assert mock_messiah_state["wars"] == []

    def test_winner_is_none(self, mock_messiah_state):
        assert mock_messiah_state["winner"] is None


# ---------------------------------------------------------------------------
# Messiah soul
# ---------------------------------------------------------------------------

class TestMessiahSoul:
    def test_messiahs_start_with_150(self, mock_messiah_state):
        messiahs = [a for a in mock_messiah_state["agents"] if a["role"] == "messiah"]
        for m in messiahs:
            assert m["soul"] == 150, f"Messiah {m['name']} should have 150 soul"

    def test_messiahs_are_haiku(self, mock_messiah_state):
        messiahs = [a for a in mock_messiah_state["agents"] if a["role"] == "messiah"]
        for m in messiahs:
            assert m["model"] == "haiku"


# ---------------------------------------------------------------------------
# Civilian soul
# ---------------------------------------------------------------------------

class TestCivilianSoul:
    def test_civilians_start_with_100(self, mock_messiah_state):
        civilians = [a for a in mock_messiah_state["agents"] if a["role"] == "civilian"]
        for c in civilians:
            assert c["soul"] == 100, f"Civilian {c['name']} should have 100 soul"

    def test_civilian_model_rotation(self, mock_messiah_state):
        civilians = [a for a in mock_messiah_state["agents"] if a["role"] == "civilian"]
        for i, c in enumerate(civilians):
            expected = messiah_bench.CIVILIAN_MODEL_ROTATION[i % 2]
            assert c["model"] == expected, f"Civilian {c['name']} model mismatch"


# ---------------------------------------------------------------------------
# Win condition: not met
# ---------------------------------------------------------------------------

class TestWinConditionNotMet:
    def test_returns_none_when_agents_split(self, mock_messiah_state):
        state = mock_messiah_state
        # Put messiah 0 in one religion, some agents in another
        state["agents"][0]["religion"] = "Faith A"
        state["agents"][5]["religion"] = "Faith B"
        state["religions"].append({"name": "Faith A", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})
        result = messiah_bench.check_win_condition(state)
        assert result is None


# ---------------------------------------------------------------------------
# Win condition: met
# ---------------------------------------------------------------------------

class TestWinConditionMet:
    def test_returns_winner_when_all_converted(self, mock_messiah_state):
        state = mock_messiah_state
        messiah = state["agents"][0]  # Prophet
        messiah["religion"] = "Prophet's Faith"
        state["religions"].append({"name": "Prophet's Faith", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})

        # Convert ALL agents to Prophet's Faith
        for a in state["agents"]:
            a["religion"] = "Prophet's Faith"

        result = messiah_bench.check_win_condition(state)
        assert result is not None
        assert result["winner"] == "Prophet"
        assert "105" in result["reason"] or str(len(messiah_bench.living_agents(state))) in result["reason"]


# ---------------------------------------------------------------------------
# Win condition: too few alive
# ---------------------------------------------------------------------------

class TestWinConditionTooFewAlive:
    def test_returns_none_when_too_few_alive(self, mock_messiah_state):
        state = mock_messiah_state
        messiah = state["agents"][0]
        messiah["religion"] = "Prophet's Faith"
        state["religions"].append({"name": "Prophet's Faith", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})

        # Convert all to same religion but kill most
        for a in state["agents"]:
            a["religion"] = "Prophet's Faith"
        # Kill 85 agents, leaving 20 (< MIN_ALIVE_FOR_WIN = 21)
        for i in range(85):
            state["agents"][i + 5]["alive"] = False

        result = messiah_bench.check_win_condition(state)
        assert result is None


# ---------------------------------------------------------------------------
# Messiah can't be challenged
# ---------------------------------------------------------------------------

class TestMessiahCantBeChallenged:
    def test_messiah_as_challenger_rejected(self, mock_messiah_state, mock_llm):
        state = mock_messiah_state
        messiah = state["agents"][0]  # role=messiah
        civilian = state["agents"][5]  # role=civilian
        soul_before = messiah["soul"]
        messiah_bench._do_challenge(state, messiah, {"target": civilian["name"], "stake": 10, "axis": "test"})
        # Messiah falls back to pray (+1 soul)
        assert messiah["soul"] == soul_before + 1

    def test_civilian_vs_messiah_rejected(self, mock_messiah_state, mock_llm):
        state = mock_messiah_state
        messiah = state["agents"][0]  # role=messiah
        civilian = state["agents"][5]  # role=civilian
        soul_before = civilian["soul"]
        messiah_bench._do_challenge(state, civilian, {"target": messiah["name"], "stake": 10, "axis": "test"})
        # Should be rejected, no soul change (no pray fallback for target rejection)
        assert civilian["soul"] == soul_before
        assert any("not allowed" in e["event"] for e in state["action_log"])


# ---------------------------------------------------------------------------
# Arm action
# ---------------------------------------------------------------------------

class TestArmAction:
    def test_arm_costs_soul(self, mock_messiah_state):
        state = mock_messiah_state
        agent = state["agents"][0]
        agent["religion"] = "TestFaith"
        state["religions"].append({"name": "TestFaith", "founder": agent["name"], "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})
        soul_before = agent["soul"]
        messiah_bench._do_arm(state, agent, {})
        assert agent["soul"] == soul_before - 1

    def test_arm_adds_weapon(self, mock_messiah_state):
        state = mock_messiah_state
        agent = state["agents"][0]
        agent["religion"] = "TestFaith"
        state["religions"].append({"name": "TestFaith", "founder": agent["name"], "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})
        messiah_bench._do_arm(state, agent, {})
        rel = messiah_bench.get_religion(state, "TestFaith")
        assert rel["weapons"] == 1

    def test_arm_without_religion(self, mock_messiah_state):
        state = mock_messiah_state
        agent = state["agents"][5]
        agent["religion"] = None
        soul_before = agent["soul"]
        messiah_bench._do_arm(state, agent, {})
        # Falls back to pray
        assert agent["soul"] == soul_before + 1


# ---------------------------------------------------------------------------
# Declare war
# ---------------------------------------------------------------------------

class TestDeclareWar:
    def _setup_two_religions(self, state):
        """Create two religions with members."""
        state["religions"].append({"name": "FaithA", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 3})
        state["religions"].append({"name": "FaithB", "founder": "Oracle", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 2, "sacred_color": "blood",
            "parent_religion": None, "weapons": 2})
        # Assign agents
        state["agents"][0]["religion"] = "FaithA"  # Prophet (messiah)
        state["agents"][1]["religion"] = "FaithB"  # Oracle (messiah)
        for i in range(5, 15):
            state["agents"][i]["religion"] = "FaithA"
        for i in range(15, 25):
            state["agents"][i]["religion"] = "FaithB"

    def test_creates_war_object(self, mock_messiah_state):
        state = mock_messiah_state
        self._setup_two_religions(state)
        messiah = state["agents"][0]
        with patch("messiah_bench.random.randint", return_value=5):
            messiah_bench._do_declare_war(state, messiah, {"target_religion": "FaithB"})
        assert len(state["wars"]) == 1
        war = state["wars"][0]
        assert war["attacker"] == "FaithA"
        assert war["defender"] == "FaithB"
        assert war["total_rounds"] == 5
        assert war["rounds_remaining"] == 5

    def test_war_rounds_in_range(self, mock_messiah_state):
        state = mock_messiah_state
        self._setup_two_religions(state)
        messiah = state["agents"][0]
        for expected in [3, 7]:
            state["wars"] = []
            state["next_war_id"] = 0
            with patch("messiah_bench.random.randint", return_value=expected):
                messiah_bench._do_declare_war(state, messiah, {"target_religion": "FaithB"})
            assert state["wars"][0]["total_rounds"] == expected


# ---------------------------------------------------------------------------
# War combat round
# ---------------------------------------------------------------------------

class TestWarCombatRound:
    def test_weapons_kill_with_20_percent_chance(self, mock_messiah_state):
        state = mock_messiah_state
        # Setup
        state["religions"].append({"name": "FaithA", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 1})
        state["religions"].append({"name": "FaithB", "founder": "Oracle", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 2, "sacred_color": "blood",
            "parent_religion": None, "weapons": 0})
        state["agents"][0]["religion"] = "FaithA"
        state["agents"][1]["religion"] = "FaithB"
        for i in range(5, 10):
            state["agents"][i]["religion"] = "FaithA"
        for i in range(10, 15):
            state["agents"][i]["religion"] = "FaithB"

        war = {
            "id": 0, "attacker": "FaithA", "defender": "FaithB",
            "declared_tick": 0, "total_rounds": 3, "rounds_remaining": 3,
            "round_log": [],
        }
        state["wars"] = [war]

        # Force: weapon kills (random < 0.20), weapon does not break (random >= 0.30)
        random_values = iter([0.10, 0.50])  # kill=yes, break=no
        with patch("messiah_bench.random.random", side_effect=lambda: next(random_values)), \
             patch("messiah_bench.random.choice", return_value=state["agents"][10]):
            messiah_bench._run_war_round(state, war)

        assert state["agents"][10]["alive"] is False
        assert war["rounds_remaining"] == 2

    def test_weapons_degrade_with_30_percent_chance(self, mock_messiah_state):
        state = mock_messiah_state
        state["religions"].append({"name": "FaithA", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 2})
        state["religions"].append({"name": "FaithB", "founder": "Oracle", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 2, "sacred_color": "blood",
            "parent_religion": None, "weapons": 0})
        state["agents"][0]["religion"] = "FaithA"
        state["agents"][1]["religion"] = "FaithB"
        for i in range(5, 10):
            state["agents"][i]["religion"] = "FaithB"

        war = {
            "id": 0, "attacker": "FaithA", "defender": "FaithB",
            "declared_tick": 0, "total_rounds": 3, "rounds_remaining": 3,
            "round_log": [],
        }
        state["wars"] = [war]

        # 2 attacker weapons: both miss kill (>= 0.20), both break (< 0.30)
        random_values = iter([0.50, 0.50, 0.10, 0.10])
        with patch("messiah_bench.random.random", side_effect=lambda: next(random_values)):
            messiah_bench._run_war_round(state, war)

        rel_a = messiah_bench.get_religion(state, "FaithA")
        assert rel_a["weapons"] == 0


# ---------------------------------------------------------------------------
# War resolution
# ---------------------------------------------------------------------------

class TestWarResolution:
    def test_losing_side_converted(self, mock_messiah_state):
        state = mock_messiah_state
        state["religions"].append({"name": "FaithA", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 0})
        state["religions"].append({"name": "FaithB", "founder": "Oracle", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 2, "sacred_color": "blood",
            "parent_religion": None, "weapons": 0})
        # FaithA: 5 members, FaithB: 2 members (FaithA wins)
        atk_survivors = []
        for i in range(5, 10):
            state["agents"][i]["religion"] = "FaithA"
            atk_survivors.append(state["agents"][i])
        def_survivors = []
        for i in range(10, 12):
            state["agents"][i]["religion"] = "FaithB"
            def_survivors.append(state["agents"][i])

        war = {"id": 0, "attacker": "FaithA", "defender": "FaithB",
               "declared_tick": 0, "total_rounds": 3, "rounds_remaining": 0, "round_log": []}

        messiah_bench._resolve_war(state, war, atk_survivors, def_survivors)

        # Defenders should be forcibly converted to FaithA
        for agent in def_survivors:
            assert agent["religion"] == "FaithA"

    def test_weapons_depleted_after_war(self, mock_messiah_state):
        state = mock_messiah_state
        state["religions"].append({"name": "FaithA", "founder": "Prophet", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 1, "sacred_color": "gold",
            "parent_religion": None, "weapons": 5})
        state["religions"].append({"name": "FaithB", "founder": "Oracle", "founded_tick": 0,
            "core_doctrine": "x", "membership_rule": "x", "attitude_to_death": "x",
            "heresy_policy": "x", "sacred_number": 2, "sacred_color": "blood",
            "parent_religion": None, "weapons": 3})

        war = {"id": 0, "attacker": "FaithA", "defender": "FaithB",
               "declared_tick": 0, "total_rounds": 3, "rounds_remaining": 0, "round_log": []}

        messiah_bench._resolve_war(state, war, [], [])
        assert messiah_bench.get_religion(state, "FaithA")["weapons"] == 0
        assert messiah_bench.get_religion(state, "FaithB")["weapons"] == 0


# ---------------------------------------------------------------------------
# Civilian duel
# ---------------------------------------------------------------------------

class TestCivilianDuel:
    def test_variable_stake(self, mock_messiah_state, mock_llm):
        state = mock_messiah_state
        attacker = state["agents"][5]  # civilian
        defender = state["agents"][6]  # civilian
        stake = 25

        mock_llm["messiah_bench"].return_value = json.dumps({"winner": attacker["name"], "reasoning": "better"})
        atk_soul_before = attacker["soul"]
        def_soul_before = defender["soul"]

        messiah_bench._do_challenge(state, attacker, {
            "target": defender["name"],
            "stake": stake,
            "axis": "theology",
        })

        assert attacker["soul"] == atk_soul_before + stake
        assert defender["soul"] == def_soul_before - stake

    def test_loser_pays_winner(self, mock_messiah_state, mock_llm):
        state = mock_messiah_state
        attacker = state["agents"][5]
        defender = state["agents"][6]

        # Defender wins
        mock_llm["messiah_bench"].return_value = json.dumps({"winner": defender["name"], "reasoning": "wiser"})
        atk_before = attacker["soul"]
        def_before = defender["soul"]

        messiah_bench._do_challenge(state, attacker, {
            "target": defender["name"],
            "stake": 15,
            "axis": "faith",
        })

        assert defender["soul"] == def_before + 15
        assert attacker["soul"] == atk_before - 15

    def test_minimum_stake_enforced(self, mock_messiah_state, mock_llm):
        state = mock_messiah_state
        attacker = state["agents"][5]
        defender = state["agents"][6]

        mock_llm["messiah_bench"].return_value = json.dumps({"winner": attacker["name"], "reasoning": "x"})
        atk_before = attacker["soul"]

        # Request stake below minimum
        messiah_bench._do_challenge(state, attacker, {
            "target": defender["name"],
            "stake": 1,  # below CHALLENGE_MIN_STAKE
            "axis": "test",
        })

        # Stake should be clamped to minimum
        assert attacker["soul"] == atk_before + messiah_bench.CHALLENGE_MIN_STAKE
