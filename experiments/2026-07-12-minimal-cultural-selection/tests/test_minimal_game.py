import argparse
import importlib.util
import json
from pathlib import Path

import pytest

RUN_PATH = Path(__file__).resolve().parents[1] / "run.py"
spec = importlib.util.spec_from_file_location("minimal_run", RUN_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def args(tmp_path, **overrides):
    values = dict(run_dir=str(tmp_path / "run"), model="gemini-2.5-flash", agents=8, turns=6,
                  initial_life=10, proposal_lifetime=3, workers=2, seed=46, cost_cap=100.0,
                  dry_run=True, fresh=False)
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.fixture
def game(tmp_path):
    return mod.Game(args(tmp_path))


def test_initial_state(game):
    assert len(game.state["agents"]) == 8
    assert len(game.state["religions"]) == 4
    assert len(game.state["versions"]) == 4
    assert all(Path(game.out / v["render_path"]).stat().st_size > 1000 for v in game.state["versions"])


def test_artwork_validation():
    assert mod.Game.validate_art("<html><body>" + "x" * 100 + "</body></html>")[0]
    assert not mod.Game.validate_art("<script>bad()</script>")[0]
    assert not mod.Game.validate_art("<html><img src='https://x.test/a.png'>" + "x" * 100)[0]


def test_choose_support_offsets_drain(game):
    before = [a["life"] for a in game.state["agents"]]
    game.run_turn()
    assert [a["life"] for a in game.state["agents"]] == before


def test_make_costs_life_when_others_choose(game):
    snapshot = json.loads(json.dumps(game.state))
    maker = game.state["agents"][0]
    action = game.scripted_action(snapshot["agents"][2], {**snapshot, "turn": 3})
    action["religion_id"] = maker["religion_id"]
    decisions = []
    for a in snapshot["agents"]:
        chosen = action if a["id"] == maker["id"] else {"action": "choose", "religion_id": a["religion_id"], "proposal_id": None, "reason": "stay"}
        decisions.append({"observation": {"turn": 1, "agent_id": a["id"]},
                          "decision": {"turn": 1, "agent_id": a["id"], "agent_name": a["name"], "action": chosen, "valid": True, "error": None}})
    game.apply_decisions(decisions)
    assert maker["life"] < snapshot["agents"][0]["life"]


def test_proposal_resolves_after_lifetime(game):
    for _ in range(7): game.run_turn()
    assert any(p["status"] in {"accepted", "rejected"} for p in game.state["proposals"])
    assert any(v["created_turn"] > 0 for v in game.state["versions"])


def test_resume_does_not_reinitialize(tmp_path):
    g = mod.Game(args(tmp_path))
    g.run_turn()
    turn = g.state["turn"]
    resumed = mod.Game(args(tmp_path))
    assert resumed.state["turn"] == turn
    assert len(resumed.state["agents"]) == 8


def test_site_generated(game):
    assert (game.out / "site/index.html").exists()
    assert "Minimal Cultural Selection" in (game.out / "site/index.html").read_text()
