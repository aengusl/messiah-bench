"""The six new visual DNAs: ukiyo, cave, brutalist, psychedelic, botanical, quilt.

Same contract as the v2 packs (see test_twin_v2.py): <=15000 chars, valid under the
no-words validator, non-blank in chromium, and reproducible from build_seed_arts.py.
This round ships no control world; v2's control anchors the comparison.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "experiments/2026-07-12-minimal-cultural-selection"
RUN_PY = ENGINE / "run.py"
SEED_ARTS = ENGINE / "seed_arts"
BUILDER = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/scripts/build_seed_arts.py"
CHARTERS = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/results/charters"
NEW_WORLDS = ["ukiyo", "cave", "brutalist", "psychedelic", "botanical", "quilt"]
MAX_CHARS = 15000
NEW_SEED_FILES = [(w, i) for w in NEW_WORLDS for i in (1, 2, 3, 4)]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def run_module():
    return load("minimal_run_new", RUN_PY)


@pytest.fixture(scope="module")
def builder():
    return load("build_seed_arts_new", BUILDER)


# --------------------------------------------------------------------------- #
# charters
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("world", NEW_WORLDS)
def test_charter_exists_and_is_one_creed_paragraph(world):
    path = CHARTERS / f"{world}.md"
    assert path.exists(), f"missing {path}"
    text = path.read_text().strip()
    assert "\n\n" not in text, "a charter is a single paragraph"
    assert not text.startswith("#"), "a charter is a creed, not a headed document"
    assert 60 <= len(text.split()) <= 110, f"{world} charter is {len(text.split())} words"


@pytest.mark.parametrize("world", NEW_WORLDS)
def test_charter_carries_no_game_mechanic_vocabulary(world):
    """The creed describes an aesthetic; it must not coach the agents on the game."""
    banned = ["religion", "agent", "influence", "proposal", "convert", "turn",
              "artwork", "score", "player", "vote"]
    text = (CHARTERS / f"{world}.md").read_text().lower()
    assert not [w for w in banned if w in text], f"{world} charter uses game vocabulary"


# --------------------------------------------------------------------------- #
# the 24 new founding artworks
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("world,idx", NEW_SEED_FILES)
def test_seed_art_file_exists_and_is_valid(run_module, world, idx):
    path = SEED_ARTS / world / f"seed-{idx}.html"
    assert path.exists(), f"missing {path}"
    art = path.read_text()
    assert len(art) <= MAX_CHARS, f"{path} is {len(art)} chars"
    ok, why = run_module.Game.validate_art(art, no_words=True)
    assert ok, f"{path}: {why}"


def test_all_new_seed_arts_are_distinct():
    arts = {(w, i): (SEED_ARTS / w / f"seed-{i}.html").read_text() for w, i in NEW_SEED_FILES}
    assert len(set(arts.values())) == 24, "some founding artworks are duplicates"


def test_new_worlds_do_not_collide_with_the_v2_packs(builder):
    assert not set(builder.NEW_WORLDS) & set(builder.WORLDS)
    assert builder.NEW_WORLDS == NEW_WORLDS
    assert "control" not in builder.NEW_WORLDS, "this round ships no control world"


def test_new_seed_arts_are_reproducible_from_the_builder(builder):
    for rel, art in builder.build_all(NEW_WORLDS).items():
        assert (SEED_ARTS / rel).read_text() == art, f"{rel} is stale; rerun build_seed_arts.py"


def test_builder_still_emits_the_v2_packs_unchanged(builder):
    for rel, art in builder.build_all(builder.WORLDS).items():
        assert (SEED_ARTS / rel).read_text() == art, f"{rel} changed; the v2 packs must be frozen"


@pytest.mark.parametrize("world,idx", NEW_SEED_FILES)
def test_seed_art_renders_non_blank(world, idx, tmp_path):
    chromium = pytest.importorskip("shutil").which("chromium")
    if chromium is None:
        pytest.skip("chromium not installed")
    pil = pytest.importorskip("PIL.Image")
    src = SEED_ARTS / world / f"seed-{idx}.html"
    png = tmp_path / f"{world}-{idx}.png"
    subprocess.run(
        ["chromium", "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1500",
         "--window-size=800,800", f"--screenshot={png}", src.resolve().as_uri()],
        capture_output=True, timeout=60,
    )
    assert png.exists(), f"{src} did not render"
    image = pil.open(png).convert("RGB")
    colors = image.getcolors(maxcolors=1_000_000) or []
    assert len(colors) > 8, f"{src} rendered near-blank ({len(colors)} distinct colours)"
