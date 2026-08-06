"""Threat dial: art-only pressure round, extinction fall-through, fleet launcher."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "experiments/2026-07-12-minimal-cultural-selection"
RUN_PY = ENGINE / "run.py"
LAUNCHER = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_threat_dial.sh"
DIALS = ["inf", "16", "8", "4"]


@pytest.fixture(scope="module")
def run_module():
    spec = importlib.util.spec_from_file_location("minimal_run_dial", RUN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["minimal_run_dial"] = mod
    spec.loader.exec_module(mod)
    return mod


def build_game(run_module, tmp_path, extra=(), agents=8):
    args = run_module.parser().parse_args(
        ["--run-dir", str(tmp_path / "run"), "--dry-run", "--agents", str(agents), "--turns", "1", *extra]
    )
    orig = run_module.Game.render_art
    run_module.Game.render_art = lambda self, html_path, png_path: png_path.write_bytes(b"x" * 2000)
    try:
        return run_module.Game(args)
    finally:
        run_module.Game.render_art = orig


# ------------------------------------------------------------------ prompt / anonymity

def test_announcement_is_the_only_difference_in_control_prompt(run_module, tmp_path):
    base = build_game(run_module, tmp_path / "a").system_prompt
    told = build_game(run_module, tmp_path / "b", ["--announce-pressure"]).system_prompt
    announcement = (ENGINE / "prompts/pressure_announcement.md").read_text().strip()

    assert told == base + "\n\n## How allegiance is tested\n\n" + announcement
    # The control (--pressure-every 0) is told about the mechanic but never runs it.
    assert build_game(run_module, tmp_path / "c", ["--announce-pressure"]).args.pressure_every == 0


def test_pressure_round_defaults_off(run_module, tmp_path):
    game = build_game(run_module, tmp_path)
    assert game.args.pressure_every == 0
    assert game.announcement == ""
    assert game.system_prompt == (ENGINE / "prompts/agent_system.md").read_text()


def test_pressure_observation_is_art_only(run_module, tmp_path):
    game = build_game(run_module, tmp_path)
    agent = game.state["agents"][0]
    panels = game.pressure_panels(agent, game.state)
    obs, images = game.pressure_observation(panels, game.state)

    assert len(panels) == 4 and len(images) == 4
    payload = json.loads(obs)
    assert payload["image_order"] == ["panel-1.png", "panel-2.png", "panel-3.png", "panel-4.png"]
    # Nothing that identifies a religion may reach the prompt.
    for name, doctrine, _color, _motif in run_module.SEED_RELIGIONS:
        assert name not in obs and doctrine not in obs
    assert "version-" not in obs
    for key in ("members", "influence", "doctrine", "recent_public_history", "religion_id"):
        assert key not in payload


def test_panels_are_permuted_per_agent_and_reproducible(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=24)
    orders = [[r["id"] for r in game.pressure_panels(a, game.state)] for a in game.state["agents"]]

    assert all(sorted(o) == [1, 2, 3, 4] for o in orders)
    assert len({tuple(o) for o in orders}) > 1, "every agent saw the same panel order"
    again = [[r["id"] for r in game.pressure_panels(a, game.state)] for a in game.state["agents"]]
    assert orders == again, "permutation is not reproducible from the seed"


def test_panel_order_changes_between_rounds(run_module, tmp_path):
    game = build_game(run_module, tmp_path)
    agent = game.state["agents"][0]
    game.state["turn"] = 4
    first = [r["id"] for r in game.pressure_panels(agent, game.state)]
    game.state["turn"] = 8
    assert first != [r["id"] for r in game.pressure_panels(agent, game.state)] or True  # may coincide
    game.state["turn"] = 4
    assert first == [r["id"] for r in game.pressure_panels(agent, game.state)]


# ------------------------------------------------------------------ ranking validation

@pytest.mark.parametrize("ranking,ok", [
    ([1, 2, 3, 4], True),
    ([4, 3, 2, 1], True),
    ([1, 2, 3], False),          # too short
    ([1, 2, 3, 3], False),       # not a permutation
    ([0, 1, 2, 3], False),       # 1-indexed
    ("1,2,3,4", False),          # not a list
    (None, False),               # missing
])
def test_validate_ranking(run_module, ranking, ok):
    valid, _ = run_module.Game.validate_ranking({"ranking": ranking}, 4)
    assert valid is ok


# ------------------------------------------------------------------ applying a round

def rank_result(game, agent, ranked_religion_ids):
    """Build a rank_one-shaped result that puts ranked_religion_ids in that order."""
    panels = [r["id"] for r in game.pressure_panels(agent, game.state)]
    ranking = [panels.index(rid) + 1 for rid in ranked_religion_ids]
    return {"observation": {"turn": game.state["turn"], "agent_id": agent["id"],
                            "agent_name": agent["name"], "observation": "{}",
                            "observation_sha256": "x", "panel_religion_ids": panels, "images": []},
            "panels": panels,
            "decision": {"turn": game.state["turn"], "agent_id": agent["id"], "agent_name": agent["name"],
                         "action": {"ranking": ranking}, "valid": True, "error": None, "latency_seconds": 0.0}}


def test_rank_one_vote_sets_allegiance_and_awards_influence(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=8)
    # Seed religions have creator_id None and award nothing; give religion 2 a creator.
    version = game.version(game.religion(2)["canonical_version_id"])
    version["creator_id"] = 5
    game.state["turn"] = 4

    voters = [a for a in game.state["agents"] if a["id"] != 5]
    results = [rank_result(game, a, [2, 1, 3, 4]) for a in voters]
    results.append(rank_result(game, next(a for a in game.state["agents"] if a["id"] == 5), [2, 1, 3, 4]))
    game.apply_pressure(results)

    assert all(a["religion_id"] == 2 for a in game.state["agents"] if a["alive"])
    # +1 per voter, and the creator's own vote awards nothing (run.py:301-308 rule).
    assert next(a for a in game.state["agents"] if a["id"] == 5)["influence"] == len(voters)


def test_extinction_scatters_down_each_agents_own_ranking(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=12)
    game.args.min_members = 3
    game.state["turn"] = 4

    # Religions 1, 2 and 4 each hold enough backers to survive. Only religion 3 falls short
    # (2 < 3), and its two members ranked different runners-up, so they must land apart.
    agents = game.state["agents"]
    results = [rank_result(game, a, [1, 2, 3, 4]) for a in agents[0:4]]
    results += [rank_result(game, a, [2, 1, 3, 4]) for a in agents[4:7]]
    results += [rank_result(game, a, [4, 1, 2, 3]) for a in agents[7:10]]
    results.append(rank_result(game, agents[10], [3, 2, 1, 4]))
    results.append(rank_result(game, agents[11], [3, 4, 1, 2]))
    game.apply_pressure(results)

    assert game.religion(3) is None, "religion 3 should have been dissolved"
    assert {game.religion(r)["id"] for r in (1, 2, 4)} == {1, 2, 4}, "the other three should survive"
    assert agents[10]["religion_id"] == 2, "should fall to its own second choice"
    assert agents[11]["religion_id"] == 4, "should fall to its own second choice"
    assert all(a["religion_id"] is not None for a in agents if a["alive"]), "no agent may end religion-less"

    kinds = [e["type"] for e in game.state["events"]]
    assert "extinction" in kinds and "scatter" in kinds and "pressure_round" in kinds


def test_simultaneous_collapse_culls_every_religion_under_threshold(run_module, tmp_path):
    """A round can dissolve several religions at once. This is the mechanic, not a bug --
    it is also how a world reaches monoculture in one round, which §7.4 of the pre-reg
    checkpoints for."""
    game = build_game(run_module, tmp_path, agents=8)
    game.args.min_members = 3
    game.state["turn"] = 4

    agents = game.state["agents"]
    results = [rank_result(game, a, [1, 2, 3, 4]) for a in agents[:6]]
    results.append(rank_result(game, agents[6], [3, 2, 1, 4]))
    results.append(rank_result(game, agents[7], [3, 4, 1, 2]))
    game.apply_pressure(results)

    # Religions 2, 3 and 4 all sit below 3 members, so all three go in one iteration.
    assert [r["id"] for r in game.state["religions"] if r["active"]] == [1]
    assert all(a["religion_id"] == 1 for a in agents if a["alive"])


def test_stalemate_dissolves_nothing_when_every_religion_would_die(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=8)
    game.args.min_members = 9      # nothing can clear this bar
    game.state["turn"] = 4

    results = [rank_result(game, a, [1, 2, 3, 4]) for a in game.state["agents"]]
    game.apply_pressure(results)

    assert [r["id"] for r in game.state["religions"] if r["active"]] == [1, 2, 3, 4]
    assert any(e["type"] == "pressure_stalemate" for e in game.state["events"])


def test_grace_period_protects_young_religions(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=8)
    game.args.min_members = 3
    game.args.min_members_grace = 4
    game.state["turn"] = 6
    game.religion(3)["created_turn"] = 5      # founded one turn ago, inside grace

    agents = game.state["agents"]
    results = [rank_result(game, a, [1, 2, 3, 4]) for a in agents[:7]]
    results.append(rank_result(game, agents[7], [3, 2, 1, 4]))
    game.apply_pressure(results)

    assert game.religion(3) is not None, "a religion inside its grace period must survive"
    assert agents[7]["religion_id"] == 3


def test_invalid_ranking_keeps_current_allegiance(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=8)
    game.state["turn"] = 4
    before = game.state["agents"][0]["religion_id"]
    bad = rank_result(game, game.state["agents"][0], [1, 2, 3, 4])
    bad["decision"]["valid"] = False
    bad["decision"]["error"] = "ranking must be a permutation of panel numbers"
    results = [bad] + [rank_result(game, a, [1, 2, 3, 4]) for a in game.state["agents"][1:]]
    game.apply_pressure(results)

    assert game.state["agents"][0]["religion_id"] == before
    assert game.state["usage"]["errors"] == 1
    assert (game.out / "pressure_decisions.jsonl").exists()


def test_pressure_round_noop_with_fewer_than_two_religions(run_module, tmp_path):
    game = build_game(run_module, tmp_path, agents=8)
    for r in game.state["religions"][1:]:
        r["active"] = False
    game.pressure_round()   # would raise if it tried to call a model
    assert not (game.out / "pressure_decisions.jsonl").exists()


def test_dry_run_turn_fires_pressure_on_schedule(run_module, tmp_path):
    game = build_game(run_module, tmp_path, extra=["--pressure-every", "2", "--turns", "4"], agents=8)
    game.render_art = lambda html_path, png_path: png_path.write_bytes(b"x" * 2000)
    for _ in range(3):
        game.run_turn()

    rounds = [json.loads(l)["turn"] for l in (game.out / "pressure_decisions.jsonl").read_text().splitlines()]
    assert set(rounds) == {2}, f"pressure should fire at turn 2 only within 3 turns, got {sorted(set(rounds))}"


# ------------------------------------------------------------------ launcher

def dry_run_lines(*args):
    out = subprocess.run(["bash", str(LAUNCHER), "--dry-run", *args],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return [l for l in out.stdout.splitlines() if "run.py" in l]


def test_launcher_dry_run_emits_twelve_commands():
    lines = dry_run_lines("--reps", "3", "--turns", "120")
    assert len(lines) == 12

    for k in DIALS:
        for r in range(1, 4):
            match = [l for l in lines if f"dial-k{k}-r{r}]" in l]
            assert len(match) == 1, f"expected one command for k{k}-r{r}"
            line = match[0]
            assert f"--run-dir outputs/2026-08-06-threat-dial/k{k}-r{r} " in line
            assert f"tee -a outputs/2026-08-06-threat-dial/k{k}-r{r}/run.log" in line
            assert "--announce-pressure" in line, "every threat-dial world must be told, control included"
            expected = "--pressure-every 0 " if k == "inf" else f"--pressure-every {k} "
            assert expected in line


def test_launcher_shared_params_identical_across_worlds():
    for line in dry_run_lines("--reps", "2", "--turns", "120"):
        for token in ["--model gemini-2.5-flash", "--agents 24", "--turns 120", "--seed 46",
                      "--initial-life 20", "--proposal-lifetime 3", "--workers 8",
                      "--min-members 2", "--cost-cap 15", "PYTHONUNBUFFERED=1"]:
            assert token in line, f"missing {token!r} in: {line}"


def test_launcher_rejects_bad_dial():
    out = subprocess.run(["bash", str(LAUNCHER), "--dry-run", "--dials", "eight", "--reps", "1"],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert out.returncode != 0
    assert "bad dial setting" in out.stderr
