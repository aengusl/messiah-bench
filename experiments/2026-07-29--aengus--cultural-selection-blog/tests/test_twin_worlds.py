"""Twin-worlds: charter injection into the minimal engine + fleet launcher."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "experiments/2026-07-12-minimal-cultural-selection"
RUN_PY = ENGINE / "run.py"
LAUNCHER = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_twin_worlds.sh"
CHARTER_DIR = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/results/charters"
CHARTERS = ["ascetic", "baroque", "nihilist", "ancestor", "futurist"]


@pytest.fixture(scope="module")
def run_module():
    spec = importlib.util.spec_from_file_location("minimal_run", RUN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["minimal_run"] = mod
    spec.loader.exec_module(mod)
    return mod


def build_game(run_module, tmp_path, extra=()):
    """Construct a Game without touching the network: --dry-run, chromium stubbed."""
    args = run_module.parser().parse_args(
        ["--run-dir", str(tmp_path / "run"), "--dry-run", "--agents", "4", "--turns", "1", *extra]
    )
    orig = run_module.Game.render_art
    run_module.Game.render_art = lambda self, html_path, png_path: png_path.write_bytes(b"x" * 2000)
    try:
        return run_module.Game(args)
    finally:
        run_module.Game.render_art = orig


def test_charter_file_appends_to_system_prompt(run_module, tmp_path):
    charter = tmp_path / "charter.md"
    charter.write_text("  A line is enough.  \n")
    game = build_game(run_module, tmp_path, ["--charter-file", str(charter)])

    base = (ENGINE / "prompts/agent_system.md").read_text()
    assert game.system_prompt == base + "\n\n## The founding charter of this world\n\nA line is enough."
    assert game.charter == "A line is enough."
    assert game.state["charter"] == "A line is enough."


def test_no_charter_leaves_system_prompt_unchanged(run_module, tmp_path):
    game = build_game(run_module, tmp_path)
    assert game.system_prompt == (ENGINE / "prompts/agent_system.md").read_text()
    assert game.charter == ""
    assert game.state["charter"] == ""


@pytest.mark.parametrize("name", CHARTERS)
def test_real_charter_files_exist_and_are_creeds(name):
    text = (CHARTER_DIR / f"{name}.md").read_text().strip()
    assert len(text) > 200, f"{name}.md looks truncated"
    assert not text.startswith("#"), f"{name}.md should be the bare creed, no heading"
    # Charters are creeds, not instructions about the game's mechanics.
    # (Word-boundary matching: "what survives removal" is aesthetics, not survival pressure.)
    for banned in ("influence", "proposal", "proposals", "supporter", "supporters", "agent", "agents"):
        assert not re.search(rf"\b{banned}\b", text, re.I), f"{name}.md mentions game mechanic '{banned}'"


def dry_run_lines(*args):
    assert shutil.which("bash"), "bash required"
    out = subprocess.run(
        ["bash", str(LAUNCHER), "--dry-run", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    return [l for l in out.stdout.splitlines() if "run.py" in l]


def test_launcher_dry_run_emits_six_times_n_commands():
    reps = 3
    lines = dry_run_lines("--reps", str(reps), "--turns", "300")
    assert len(lines) == 6 * reps

    for c in CHARTERS + ["control"]:
        for r in range(1, reps + 1):
            tag = f"twin-{c}-r{r}]"
            match = [l for l in lines if tag in l]
            assert len(match) == 1, f"expected exactly one command for {tag}"
            assert f"--run-dir outputs/2026-08-06-twin-worlds/{c}-r{r} " in match[0]
            assert f"tee -a outputs/2026-08-06-twin-worlds/{c}-r{r}/run.log" in match[0]
            if c == "control":
                assert "--charter-file" not in match[0]
            else:
                assert f"--charter-file {CHARTER_DIR.relative_to(ROOT)}/{c}.md" in match[0]


def test_launcher_shared_params_identical_across_worlds():
    lines = dry_run_lines("--reps", "2", "--turns", "300")
    shared = ["--model gemini-2.5-flash", "--agents 24", "--turns 300", "--seed 46",
              "--initial-life 20", "--proposal-lifetime 3", "--workers 8",
              "--cost-cap 40", "PYTHONUNBUFFERED=1"]
    for line in lines:
        for token in shared:
            assert token in line, f"missing {token!r} in: {line}"


def test_launcher_rejects_unknown_charter():
    out = subprocess.run(
        ["bash", str(LAUNCHER), "--dry-run", "--charters", "nonesuch", "--reps", "1"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert out.returncode != 0
    assert "missing charter file" in out.stderr
