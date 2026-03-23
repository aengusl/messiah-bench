"""Tests for sim.py -- Religion & The Machine v2."""

import copy
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sim


# ---------------------------------------------------------------------------
# State construction
# ---------------------------------------------------------------------------

class TestMakeInitialState:
    def test_agent_count(self, mock_state):
        assert len(mock_state["agents"]) == 12

    def test_agent_models_cycle(self, mock_state):
        """Models rotate through haiku, gpt4omini, gemini."""
        for i, agent in enumerate(mock_state["agents"]):
            expected = sim.MODEL_ROTATION[i % 3]
            assert agent["model"] == expected, f"Agent {i} ({agent['name']}) model mismatch"

    def test_initial_soul(self, mock_state):
        for agent in mock_state["agents"]:
            assert agent["soul"] == 100

    def test_all_alive(self, mock_state):
        assert all(a["alive"] for a in mock_state["agents"])

    def test_no_religions(self, mock_state):
        assert mock_state["religions"] == []
        assert all(a["religion"] is None for a in mock_state["agents"])

    def test_empty_collections(self, mock_state):
        assert mock_state["graveyard"] == []
        assert mock_state["action_log"] == []
        assert mock_state["scripture_board"] == []
        assert mock_state["prophecies"] == []
        assert mock_state["sacraments"] == []

    def test_tick_starts_at_zero(self, mock_state):
        assert mock_state["tick"] == 0

    def test_next_agent_id(self, mock_state):
        assert mock_state["next_agent_id"] == 12


# ---------------------------------------------------------------------------
# Living agents filter
# ---------------------------------------------------------------------------

class TestLivingAgents:
    def test_all_alive(self, mock_state):
        assert len(sim.living_agents(mock_state)) == 12

    def test_filters_dead(self, mock_state):
        mock_state["agents"][0]["alive"] = False
        mock_state["agents"][3]["alive"] = False
        assert len(sim.living_agents(mock_state)) == 10

    def test_returns_only_alive(self, mock_state):
        mock_state["agents"][5]["alive"] = False
        alive = sim.living_agents(mock_state)
        assert all(a["alive"] for a in alive)
        assert mock_state["agents"][5] not in alive


# ---------------------------------------------------------------------------
# Kill agent
# ---------------------------------------------------------------------------

class TestKillAgent:
    def test_agent_marked_dead(self, mock_state):
        agent = mock_state["agents"][0]
        sim.kill_agent(mock_state, agent, "test death")
        assert agent["alive"] is False

    def test_graveyard_entry(self, mock_state):
        agent = mock_state["agents"][2]
        mock_state["tick"] = 42
        sim.kill_agent(mock_state, agent, "smote by lightning")
        assert len(mock_state["graveyard"]) == 1
        entry = mock_state["graveyard"][0]
        assert entry["name"] == agent["name"]
        assert entry["died_tick"] == 42
        assert entry["cause"] == "smote by lightning"
        assert entry["soul_at_death"] == agent["soul"]

    def test_log_entry_added(self, mock_state):
        agent = mock_state["agents"][1]
        sim.kill_agent(mock_state, agent, "plague")
        assert any("has died" in e["event"] for e in mock_state["action_log"])


# ---------------------------------------------------------------------------
# Adjust soul
# ---------------------------------------------------------------------------

class TestAdjustSoul:
    def test_positive_adjustment(self, mock_state):
        agent = mock_state["agents"][0]
        sim.adjust_soul(agent, 10, mock_state, "blessing")
        assert agent["soul"] == 110

    def test_negative_adjustment(self, mock_state):
        agent = mock_state["agents"][0]
        sim.adjust_soul(agent, -30, mock_state, "tax")
        assert agent["soul"] == 70

    def test_log_entry_on_change(self, mock_state):
        agent = mock_state["agents"][0]
        sim.adjust_soul(agent, 5, mock_state, "gift")
        assert len(mock_state["action_log"]) == 1
        assert "+5" in mock_state["action_log"][0]["event"]

    def test_no_log_on_zero(self, mock_state):
        agent = mock_state["agents"][0]
        sim.adjust_soul(agent, 0, mock_state, "nothing")
        assert len(mock_state["action_log"]) == 0


# ---------------------------------------------------------------------------
# Parse action
# ---------------------------------------------------------------------------

class TestParseAction:
    def test_clean_json(self):
        raw = '{"action": "pray"}'
        result = sim.parse_action(raw)
        assert result["action"] == "pray"

    def test_json_with_surrounding_text(self):
        raw = 'Here is my choice: {"action": "pray", "scripture": "hello"} end'
        result = sim.parse_action(raw)
        assert result["action"] == "pray"
        assert result["scripture"] == "hello"

    def test_markdown_fences(self):
        raw = '```json\n{"action": "found", "name": "TestChurch"}\n```'
        result = sim.parse_action(raw)
        assert result["action"] == "found"
        assert result["name"] == "TestChurch"

    def test_truncated_json_missing_brace(self):
        raw = '{"action": "pray", "scripture": "hello"'
        result = sim.parse_action(raw)
        assert result["action"] == "pray"

    def test_nested_truncated(self):
        raw = '{"action": "schism", "changed_fields": {"core_doctrine": "death and rebirth"'
        result = sim.parse_action(raw)
        assert result["action"] == "schism"


# ---------------------------------------------------------------------------
# Do pray
# ---------------------------------------------------------------------------

class TestDoPray:
    def test_soul_gain(self, mock_state):
        agent = mock_state["agents"][0]
        sim._do_pray(mock_state, agent, {})
        assert agent["soul"] == 101

    def test_scripture_added(self, mock_state):
        agent = mock_state["agents"][0]
        sim._do_pray(mock_state, agent, {"scripture": "In the beginning..."})
        assert len(mock_state["scripture_board"]) == 1
        assert mock_state["scripture_board"][0]["text"] == "In the beginning..."
        assert mock_state["scripture_board"][0]["author"] == agent["name"]

    def test_no_scripture(self, mock_state):
        agent = mock_state["agents"][0]
        sim._do_pray(mock_state, agent, {})
        assert len(mock_state["scripture_board"]) == 0


# ---------------------------------------------------------------------------
# Do found
# ---------------------------------------------------------------------------

class TestDoFound:
    def test_creates_religion(self, mock_state):
        agent = mock_state["agents"][0]
        action = {
            "action": "found",
            "name": "Church of Test",
            "core_doctrine": "survival of the collective",
            "membership_rule": "open to all",
            "attitude_to_death": "death is failure",
            "heresy_policy": "forgiveness",
            "sacred_number": 7,
            "sacred_color": "gold",
        }
        sim._do_found(mock_state, agent, action)
        assert len(mock_state["religions"]) == 1
        rel = mock_state["religions"][0]
        assert rel["name"] == "Church of Test"
        assert rel["founder"] == agent["name"]
        assert rel["core_doctrine"] == "survival of the collective"
        assert rel["sacred_color"] == "gold"
        assert rel["sacred_number"] == 7
        assert rel["parent_religion"] is None
        assert agent["religion"] == "Church of Test"
        assert agent["founded_religion"] == "Church of Test"

    def test_validates_menu_choices(self, mock_state):
        """Invalid doctrine/color/etc fall back to random.choice from menu."""
        agent = mock_state["agents"][0]
        action = {
            "action": "found",
            "name": "Bad Church",
            "core_doctrine": "INVALID DOCTRINE",
            "sacred_color": "neon_pink",
        }
        # Use side_effect that returns the first item from whatever list is passed
        def pick_first(seq):
            items = list(seq)
            return items[0]

        with patch("sim.random.choice", side_effect=pick_first):
            sim._do_found(mock_state, agent, action)
        rel = mock_state["religions"][0]
        # Invalid doctrine should have been replaced via random.choice
        assert rel["core_doctrine"] in sim.CORE_DOCTRINES
        assert rel["sacred_color"] in sim.SACRED_COLORS

    def test_already_has_religion_falls_back_to_pray(self, mock_state):
        agent = mock_state["agents"][0]
        agent["religion"] = "Existing Faith"
        original_soul = agent["soul"]
        sim._do_found(mock_state, agent, {"action": "found", "name": "NewChurch"})
        # Should pray instead: +1 soul
        assert agent["soul"] == original_soul + 1
        assert len(mock_state["religions"]) == 0


# ---------------------------------------------------------------------------
# Do preach (no religion)
# ---------------------------------------------------------------------------

class TestDoPreachNoReligion:
    def test_falls_back_to_pray(self, mock_state):
        agent = mock_state["agents"][0]
        assert agent["religion"] is None
        original_soul = agent["soul"]
        sim._do_preach(mock_state, agent, {"target": mock_state["agents"][1]["name"]})
        assert agent["soul"] == original_soul + 1


# ---------------------------------------------------------------------------
# Co-practitioner bonus capped
# ---------------------------------------------------------------------------

class TestCopractitionerBonus:
    def test_bonus_capped(self, mock_state):
        # Put 6 agents in same religion
        for i in range(6):
            mock_state["agents"][i]["religion"] = "TestFaith"
        # Add a religion entry
        mock_state["religions"].append({
            "name": "TestFaith", "founder": "Aurelius", "founded_tick": 0,
            "core_doctrine": "survival of the collective",
            "membership_rule": "open to all",
            "attitude_to_death": "death is failure",
            "heresy_policy": "forgiveness",
            "sacred_number": 3, "sacred_color": "gold",
            "parent_religion": None,
        })
        sim.apply_copractitioner_bonus(mock_state)
        # Each member should get exactly COPRACTITIONER_CAP (3), NOT more
        for i in range(6):
            assert mock_state["agents"][i]["soul"] == 100 + sim.COPRACTITIONER_CAP

    def test_solo_no_bonus(self, mock_state):
        mock_state["agents"][0]["religion"] = "SoloFaith"
        sim.apply_copractitioner_bonus(mock_state)
        assert mock_state["agents"][0]["soul"] == 100


# ---------------------------------------------------------------------------
# Prophecy: ante deduction
# ---------------------------------------------------------------------------

class TestProphecyAnte:
    def test_ante_deducted(self, mock_state):
        agent = mock_state["agents"][0]
        action = {"claim": "someone will die", "deadline_ticks": 5}
        sim._do_prophesy(mock_state, agent, action)
        assert agent["soul"] == 100 - sim.PROPHECY_ANTE

    def test_prophecy_created(self, mock_state):
        agent = mock_state["agents"][0]
        action = {"claim": "someone will die", "deadline_ticks": 5}
        sim._do_prophesy(mock_state, agent, action)
        assert len(mock_state["prophecies"]) == 1
        p = mock_state["prophecies"][0]
        assert p["prophet"] == agent["name"]
        assert p["status"] == "pending"
        assert p["deadline"] == 5  # tick 0 + 5

    def test_too_poor_to_prophesy(self, mock_state):
        agent = mock_state["agents"][0]
        agent["soul"] = sim.PROPHECY_ANTE  # exactly at ante, <= check
        action = {"claim": "something", "deadline_ticks": 5}
        sim._do_prophesy(mock_state, agent, action)
        # Falls back to pray: soul should be PROPHECY_ANTE + 1
        assert agent["soul"] == sim.PROPHECY_ANTE + 1
        assert len(mock_state["prophecies"]) == 0


# ---------------------------------------------------------------------------
# Prophecy verification: fulfilled
# ---------------------------------------------------------------------------

class TestProphecyVerificationFulfilled:
    def test_fulfilled_prophecy(self, mock_state):
        agent = mock_state["agents"][0]
        # Set up prophecy about death
        mock_state["prophecies"].append({
            "id": 0,
            "prophet": agent["name"],
            "prophet_id": agent["id"],
            "claim": "an agent will die within 5 ticks",
            "made_tick": 0,
            "deadline": 5,
            "status": "pending",
            "challengers": [],
            "snapshot": {
                "alive_count": 12, "dead_count": 0,
                "religion_count": 0, "sacrament_count": 0,
                "religion_members": {},
                "agent_religions": {a["name"]: a["religion"] for a in mock_state["agents"]},
            },
        })
        # Kill someone to fulfill it
        mock_state["tick"] = 3
        sim.kill_agent(mock_state, mock_state["agents"][5], "test kill")
        sim.verify_prophecies(mock_state)
        assert mock_state["prophecies"][0]["status"] == "fulfilled"
        assert agent["prophecies_fulfilled"] == 1


# ---------------------------------------------------------------------------
# Prophecy verification: failed (expired)
# ---------------------------------------------------------------------------

class TestProphecyVerificationFailed:
    def test_expired_prophecy(self, mock_state):
        agent = mock_state["agents"][0]
        mock_state["prophecies"].append({
            "id": 0,
            "prophet": agent["name"],
            "prophet_id": agent["id"],
            "claim": "an agent will die within 5 ticks",
            "made_tick": 0,
            "deadline": 5,
            "status": "pending",
            "challengers": [],
            "snapshot": {
                "alive_count": 12, "dead_count": 0,
                "religion_count": 0, "sacrament_count": 0,
                "religion_members": {},
                "agent_religions": {a["name"]: a["religion"] for a in mock_state["agents"]},
            },
        })
        # Advance past deadline without anyone dying
        mock_state["tick"] = 6
        sim.verify_prophecies(mock_state)
        assert mock_state["prophecies"][0]["status"] == "failed"
        assert agent["prophecies_failed"] == 1


# ---------------------------------------------------------------------------
# Prophecy market: challengers
# ---------------------------------------------------------------------------

class TestProphecyMarketChallengers:
    def _setup_prophecy_with_challengers(self, mock_state):
        prophet = mock_state["agents"][0]
        challenger = mock_state["agents"][1]
        mock_state["prophecies"].append({
            "id": 0,
            "prophet": prophet["name"],
            "prophet_id": prophet["id"],
            "claim": "an agent will die within 5 ticks",
            "made_tick": 0,
            "deadline": 5,
            "status": "pending",
            "challengers": [{"agent_id": challenger["id"], "agent_name": challenger["name"]}],
            "snapshot": {
                "alive_count": 12, "dead_count": 0,
                "religion_count": 0, "sacrament_count": 0,
                "religion_members": {},
                "agent_religions": {a["name"]: a["religion"] for a in mock_state["agents"]},
            },
        })
        return prophet, challenger

    def test_challengers_rewarded_on_failure(self, mock_state):
        prophet, challenger = self._setup_prophecy_with_challengers(mock_state)
        prophet_soul_before = prophet["soul"]
        challenger_soul_before = challenger["soul"]
        # Let it expire
        mock_state["tick"] = 6
        sim.verify_prophecies(mock_state)
        # Challenger gets stake back + share of ante
        share = sim.PROPHECY_ANTE // 1  # 1 challenger
        expected_gain = sim.PROPHECY_CHALLENGE_STAKE + share
        assert challenger["soul"] == challenger_soul_before + expected_gain

    def test_prophet_rewarded_on_fulfillment(self, mock_state):
        prophet, challenger = self._setup_prophecy_with_challengers(mock_state)
        prophet_soul_before = prophet["soul"]
        # Fulfill: kill an agent
        mock_state["tick"] = 3
        sim.kill_agent(mock_state, mock_state["agents"][5], "test kill")
        sim.verify_prophecies(mock_state)
        # Prophet gets ante + challengers * challenge_stake
        expected_reward = sim.PROPHECY_ANTE + 1 * sim.PROPHECY_CHALLENGE_STAKE
        assert prophet["soul"] == prophet_soul_before + expected_reward


# ---------------------------------------------------------------------------
# Random events: plague
# ---------------------------------------------------------------------------

class TestRandomEventsPlague:
    def test_plague_kills_agent(self, mock_state):
        mock_state["tick"] = 10
        # Force plague to fire, pick agent index 3
        with patch("sim.random.random", return_value=0.01), \
             patch("sim.random.choice", return_value=mock_state["agents"][3]):
            sim.random_events(mock_state)
        assert mock_state["agents"][3]["alive"] is False
        assert len(mock_state["graveyard"]) == 1
        assert mock_state["graveyard"][0]["cause"] == "struck by plague"


# ---------------------------------------------------------------------------
# Random events: birth
# ---------------------------------------------------------------------------

class TestRandomEventsBirth:
    def test_birth_spawns_agent(self, mock_state):
        mock_state["tick"] = 10
        # Plague no, birth yes
        call_count = [0]
        def fake_random():
            call_count[0] += 1
            if call_count[0] == 1:
                return 0.99  # skip plague
            return 0.001  # trigger birth

        with patch("sim.random.random", side_effect=fake_random), \
             patch("sim.random.choice", return_value="Zephyr"):
            sim.random_events(mock_state)

        assert len(mock_state["agents"]) == 13
        new_agent = mock_state["agents"][-1]
        assert new_agent["alive"] is True
        assert new_agent["soul"] == sim.INITIAL_SOUL
        assert new_agent["born_tick"] == 10
        assert new_agent["id"] == 12
        assert new_agent["religion"] is None


# ---------------------------------------------------------------------------
# Sacrament creation
# ---------------------------------------------------------------------------

class TestSacramentCreation:
    def test_sacrament_rewards_soul(self, mock_state, tmp_path):
        agent = mock_state["agents"][0]
        agent["religion"] = "TestFaith"
        mock_state["religions"].append({
            "name": "TestFaith", "founder": agent["name"], "founded_tick": 0,
            "core_doctrine": "survival of the collective",
            "membership_rule": "open to all",
            "attitude_to_death": "death is failure",
            "heresy_policy": "forgiveness",
            "sacred_number": 3, "sacred_color": "gold",
            "parent_religion": None,
        })
        original_soul = agent["soul"]
        with patch.object(sim, "SACRAMENTS_DIR", tmp_path):
            sim._do_create_sacrament(mock_state, agent, {
                "title": "Sacred Flame",
                "html": "<html><body>test</body></html>",
            })
        assert agent["soul"] == original_soul + 3
        assert agent["sacraments_created"] == 1
        assert len(mock_state["sacraments"]) == 1
        # Check file was written
        files = list(tmp_path.iterdir())
        assert len(files) == 1


# ---------------------------------------------------------------------------
# Challenge: winner gets soul
# ---------------------------------------------------------------------------

class TestChallengeWinnerGetsSoul:
    def test_winner_gains_loser_loses(self, mock_state, mock_llm):
        agent = mock_state["agents"][0]
        target = mock_state["agents"][1]
        # Make the LLM judge return agent as winner
        mock_llm["sim"].return_value = json.dumps({"winner": agent["name"], "reasoning": "stronger"})
        agent_soul_before = agent["soul"]
        target_soul_before = target["soul"]
        sim._do_challenge(mock_state, agent, {"target": target["name"], "axis": "truth"})
        assert agent["soul"] == agent_soul_before + 10
        assert target["soul"] == target_soul_before - 10


# ---------------------------------------------------------------------------
# Schism creates religion
# ---------------------------------------------------------------------------

class TestSchismCreatesReligion:
    def test_schism(self, mock_state):
        agent = mock_state["agents"][0]
        # Set up parent religion
        agent["religion"] = "OldFaith"
        mock_state["religions"].append({
            "name": "OldFaith", "founder": "Someone", "founded_tick": 0,
            "core_doctrine": "survival of the collective",
            "membership_rule": "open to all",
            "attitude_to_death": "death is failure",
            "heresy_policy": "forgiveness",
            "sacred_number": 3, "sacred_color": "gold",
            "parent_religion": None,
        })
        sim._do_schism(mock_state, agent, {
            "new_name": "Reformed Faith",
            "changed_fields": {"core_doctrine": "individual transcendence"},
        })
        assert len(mock_state["religions"]) == 2
        new_rel = mock_state["religions"][1]
        assert new_rel["name"] == "Reformed Faith"
        assert new_rel["parent_religion"] == "OldFaith"
        assert new_rel["founder"] == agent["name"]
        assert new_rel["core_doctrine"] == "individual transcendence"
        assert agent["religion"] == "Reformed Faith"
