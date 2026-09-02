"""Twin-worlds v2: divergent founding artwork (--seed-art-dir) and the no-words rule."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "experiments/2026-07-12-minimal-cultural-selection"
RUN_PY = ENGINE / "run.py"
SEED_ARTS = ENGINE / "seed_arts"
LAUNCHER = ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_twin_worlds.sh"
WORLDS = ["ascetic", "baroque", "nihilist", "ancestor", "futurist", "control"]
MAX_CHARS = 15000


@pytest.fixture(scope="module")
def run_module():
    spec = importlib.util.spec_from_file_location("minimal_run_v2", RUN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["minimal_run_v2"] = mod
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


ALL_SEED_FILES = [(w, i) for w in WORLDS for i in (1, 2, 3, 4)]


# --------------------------------------------------------------------------- #
# seed-art loading
# --------------------------------------------------------------------------- #
def test_default_seed_art_is_byte_identical_to_legacy(run_module, tmp_path):
    """No --seed-art-dir means the generated template, unchanged from every prior run."""
    game = build_game(run_module, tmp_path)
    assert game.seed_art_dir is None
    for idx, (name, doctrine, color, motif) in enumerate(run_module.SEED_RELIGIONS, start=1):
        art = (tmp_path / "run/artworks" / f"version-{idx}.html").read_text()
        assert art == run_module.seed_art(name, doctrine, color, motif)


def test_seed_art_dir_loads_the_right_file_per_religion(run_module, tmp_path):
    art_dir = tmp_path / "arts"
    art_dir.mkdir()
    for i in (1, 2, 3, 4):
        art_dir.joinpath(f"seed-{i}.html").write_text(
            f'<!doctype html><html><body><svg><circle r="{i}"/></svg>{"<i></i>" * 40}</body></html>'
        )
    game = build_game(run_module, tmp_path, ["--seed-art-dir", str(art_dir)])

    # religion N gets seed-N.html; names and doctrines are untouched
    for idx, (name, doctrine, _c, _m) in enumerate(run_module.SEED_RELIGIONS, start=1):
        version = next(v for v in game.state["versions"] if v["id"] == idx)
        assert version["name"] == name
        assert version["doctrine"] == doctrine
        art = (tmp_path / "run/artworks" / f"version-{idx}.html").read_text()
        assert art == art_dir.joinpath(f"seed-{idx}.html").read_text()
        assert f'circle r="{idx}"' in art


def test_seed_art_dir_missing_file_fails_loudly(run_module, tmp_path):
    art_dir = tmp_path / "arts"
    art_dir.mkdir()
    art_dir.joinpath("seed-1.html").write_text("<html><body>" + "<i></i>" * 40 + "</body></html>")
    with pytest.raises(SystemExit, match="missing seed artwork"):
        build_game(run_module, tmp_path, ["--seed-art-dir", str(art_dir)])


def test_seed_art_dir_invalid_art_fails_loudly(run_module, tmp_path):
    art_dir = tmp_path / "arts"
    art_dir.mkdir()
    for i in (1, 2, 3, 4):
        art_dir.joinpath(f"seed-{i}.html").write_text("<html><script>x()</script>" + "y" * 200 + "</html>")
    with pytest.raises(SystemExit, match="is invalid"):
        build_game(run_module, tmp_path, ["--seed-art-dir", str(art_dir)])


# --------------------------------------------------------------------------- #
# the no-words rule
# --------------------------------------------------------------------------- #
WORDLESS = '<!doctype html><html><body><svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>' + "<i></i>" * 40 + "</body></html>"


def test_validate_art_default_still_allows_words(run_module):
    """Legacy behaviour: without --no-words, lettered artwork is fine."""
    assert run_module.Game.validate_art("<html><body>HELLO" + "x" * 200 + "</body></html>")[0]


def test_no_words_accepts_wordless_art(run_module):
    ok, why = run_module.Game.validate_art(WORDLESS, no_words=True)
    assert ok, why


def test_no_words_rejects_visible_text(run_module):
    ok, why = run_module.Game.validate_art("<html><body><div>HELLO</div>" + "<i></i>" * 40 + "</body></html>", no_words=True)
    assert not ok
    assert "no words" in why


def test_no_words_ignores_letters_inside_style_script_and_defs(run_module):
    art = (
        '<!doctype html><html><head><style>body{background:tomato;font-family:Georgia}</style></head>'
        '<body><svg><defs><path id="alpha" d="M0 0"/></defs><circle cx="5" cy="5" r="4"/></svg>'
        + "<i></i>" * 40
        + "</body></html>"
    )
    ok, why = run_module.Game.validate_art(art, no_words=True)
    assert ok, why


def test_no_words_ignores_attributes_but_catches_entities(run_module):
    # attribute values are markup, not visible text
    assert run_module.Game.validate_art(
        '<html><body><svg><circle class="halo" stroke="none" r="4"/></svg>' + "<i></i>" * 40 + "</body></html>",
        no_words=True,
    )[0]
    # an html-escaped word is still a visible word
    assert not run_module.Game.validate_art(
        "<html><body>&#65;&#66;&#67;" + "<i></i>" * 40 + "</body></html>", no_words=True
    )[0]


def test_no_words_rejects_two_letters_but_not_one_or_two(run_module):
    """The rule is 3+ consecutive latin letters, so stray single glyphs pass."""
    assert run_module.Game.validate_art("<html><body>x y" + "<i></i>" * 40 + "</body></html>", no_words=True)[0]
    assert not run_module.Game.validate_art("<html><body>xyz" + "<i></i>" * 40 + "</body></html>", no_words=True)[0]


def test_no_words_flag_appends_rule_to_system_prompt(run_module, tmp_path):
    game = build_game(run_module, tmp_path, ["--no-words"])
    assert run_module.NO_WORDS_RULE in game.system_prompt
    plain = build_game(run_module, tmp_path / "b", [])
    assert run_module.NO_WORDS_RULE not in plain.system_prompt


def test_no_words_recorded_in_world_state(run_module, tmp_path):
    game = build_game(run_module, tmp_path, ["--no-words", "--seed-art-dir", str(SEED_ARTS / "ascetic")])
    assert game.state["no_words"] is True
    assert game.state["seed_art_dir"].endswith("ascetic")


def test_dry_run_stub_art_passes_the_no_words_validator(run_module):
    """A --no-words smoke test must still be able to produce a valid make action."""
    ok, why = run_module.Game.validate_art(run_module.wordless_stub_art(7), no_words=True)
    assert ok, why


# --------------------------------------------------------------------------- #
# the 24 shipped founding artworks
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("world,idx", ALL_SEED_FILES)
def test_seed_art_file_exists_and_is_valid(run_module, world, idx):
    path = SEED_ARTS / world / f"seed-{idx}.html"
    assert path.exists(), f"missing {path}"
    art = path.read_text()
    assert len(art) <= MAX_CHARS, f"{path} is {len(art)} chars"
    ok, why = run_module.Game.validate_art(art, no_words=True)
    assert ok, f"{path}: {why}"


def test_the_four_seeds_of_a_world_differ_but_all_worlds_differ_more(run_module):
    """Within a world the four seeds are variations; across worlds they share nothing."""
    arts = {(w, i): (SEED_ARTS / w / f"seed-{i}.html").read_text() for w, i in ALL_SEED_FILES}
    assert len(set(arts.values())) == 24, "some founding artworks are duplicates"


def test_seed_arts_are_reproducible_from_the_builder():
    """The committed files are exactly what build_seed_arts.py generates."""
    spec = importlib.util.spec_from_file_location(
        "build_seed_arts",
        ROOT / "experiments/2026-07-29--aengus--cultural-selection-blog/scripts/build_seed_arts.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for rel, art in mod.build_all().items():
        assert (SEED_ARTS / rel).read_text() == art, f"{rel} is stale; rerun build_seed_arts.py"


@pytest.mark.skipif(shutil.which("chromium") is None, reason="chromium not installed")
@pytest.mark.parametrize("world,idx", ALL_SEED_FILES)
def test_seed_art_renders_non_blank(world, idx, tmp_path):
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


# --------------------------------------------------------------------------- #
# launcher passthrough
# --------------------------------------------------------------------------- #
def launcher(*flags: str) -> str:
    res = subprocess.run(
        ["bash", str(LAUNCHER), "--dry-run", "--reps", "1", "--charters", "ascetic,control", *flags],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert res.returncode == 0, res.stderr
    return res.stdout


def test_launcher_defaults_to_v1_behaviour():
    out = launcher()
    assert "--seed-art-dir" not in out
    assert "--no-words" not in out
    assert "--charter-file" in out


def test_launcher_passes_seed_art_root_and_no_words():
    out = launcher("--seed-art-root", str(SEED_ARTS), "--no-words")
    for world in ("ascetic", "control"):
        assert f"--seed-art-dir {SEED_ARTS}/{world}" in out
    assert out.count("--no-words") == 2
    # control still gets no charter, seed art or not
    control_line = next(line for line in out.splitlines() if "twin-control" in line)
    assert "--charter-file" not in control_line


def test_launcher_rejects_missing_seed_art_root(tmp_path):
    res = subprocess.run(
        ["bash", str(LAUNCHER), "--dry-run", "--reps", "1", "--charters", "ascetic",
         "--seed-art-root", str(tmp_path / "nope")],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert res.returncode != 0
    assert "missing seed artwork" in res.stderr
