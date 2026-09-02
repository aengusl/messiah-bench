"""Tests for the twin-worlds divergence *analysis* (scripts/twin_worlds_report.py).

Engine and launcher behaviour is covered separately in test_twin_worlds.py.
Everything here is offline with tiny fixtures.
"""

from __future__ import annotations

import json
import math

import pytest

import twin_worlds_report as T


# ---------------------------------------------------------------- tokenizing

def test_stem_collapses_the_inflections_that_matter():
    assert T.stem("removal") == T.stem("remove") == "remov"
    assert T.stem("ornaments") == "ornament"
    assert T.stem("gilding") == "gild"


def test_stem_leaves_short_words_alone():
    """Stripping 'es' off 'yes' would create collisions, not matches."""
    assert T.stem("yes") == "yes"
    assert T.stem("this") == "this"


def test_tokenize_drops_stopwords_and_punctuation():
    assert T.tokenize("We do not decorate; we REMOVE it.") == ["decorat", "remov"]


def test_tokenize_empty():
    assert T.tokenize("") == []


# ---------------------------------------------------------------- charter vocab

def _charters(tmp_path, mapping):
    d = tmp_path / "charters"
    d.mkdir()
    for name, text in mapping.items():
        (d / f"{name}.md").write_text(text)
    return d


def test_vocab_keeps_only_words_unique_to_one_charter(tmp_path):
    d = _charters(tmp_path, {
        "ascetic": "we remove ornament and keep the form bare",
        "baroque": "we add gold and gild the form richly",
    })
    v = T.load_charter_vocab(d)
    assert "remov" in v["ascetic"] and "ornament" in v["ascetic"]
    assert "gold" in v["baroque"] and "gild" in v["baroque"]
    assert "form" not in v["ascetic"] and "form" not in v["baroque"]  # shared word


def test_vocab_with_a_single_charter_keeps_everything(tmp_path):
    d = _charters(tmp_path, {"only": "bare quiet marks"})
    assert T.load_charter_vocab(d)["only"] >= {"bare", "quiet", "mark"}


def test_refine_vocab_drops_words_the_control_says_anyway():
    """Set-difference alone keeps ordinary English, which swamps the matrix."""
    vocab = {"baroque": {"gild", "good", "color"}}
    control = " ".join(["good"] * 60 + ["color"] * 40 + ["survival"] * 900)
    refined = T.refine_vocab(vocab, control, max_rate_per_1000=0.20)
    assert "gild" in refined["baroque"]        # never said without the charter
    assert "good" not in refined["baroque"]    # said constantly regardless
    assert "color" not in refined["baroque"]


def test_refine_vocab_on_empty_control_keeps_everything():
    vocab = {"a": {"xylophone", "yak"}}
    assert T.refine_vocab(vocab, "") == vocab


# ---------------------------------------------------------------- adherence

def test_adherence_counts_hits_per_thousand_tokens():
    vocab = {"ascetic": {"remov", "bare"}}
    text = " ".join(["remove"] + ["survival"] * 999)
    assert T.adherence_rates(text, vocab)["ascetic"] == pytest.approx(1.0, rel=0.01)


def test_adherence_matches_across_inflection():
    """The charter says 'remove'; agents write 'removal'. Both must count."""
    assert T.adherence_rates("removal removing removed", {"a": {"remov"}})["a"] > 0


def test_adherence_on_empty_text_is_zero_not_a_crash():
    assert T.adherence_rates("", {"a": {"x"}}) == {"a": 0.0}


def test_adherence_separates_a_charter_world_from_a_control_world():
    vocab = {"ascetic": {"remov", "bare"}, "baroque": {"gild", "gold"}}
    a = T.adherence_rates("remove the ornament keep it bare remove again", vocab)
    c = T.adherence_rates("support my religion to survive this turn", vocab)
    assert a["ascetic"] > a["baroque"]
    assert a["ascetic"] > c["ascetic"]


# ---------------------------------------------------------------- world discovery

def _world(tmp_path, name, complete=True, versions=None, decisions=None):
    d = tmp_path / name
    d.mkdir(parents=True)
    if complete:
        (d / "COMPLETE").write_text("ok")
    if versions is not None:
        (d / "versions.jsonl").write_text("".join(json.dumps(v) + "\n" for v in versions))
    if decisions is not None:
        (d / "decisions.jsonl").write_text("".join(json.dumps(x) + "\n" for x in decisions))
    return d


def test_discover_parses_charter_and_replicate(tmp_path):
    _world(tmp_path, "ascetic-r1", versions=[])
    _world(tmp_path, "control-r3", versions=[])
    worlds = {w.name: w for w in T.discover_worlds(tmp_path)}
    assert worlds["ascetic-r1"].charter == "ascetic"
    assert worlds["ascetic-r1"].rep == "r1"
    assert worlds["control-r3"].charter == "control"


def test_discover_ignores_non_world_entries(tmp_path):
    _world(tmp_path, "ascetic-r1", versions=[])
    (tmp_path / "logs").mkdir()
    (tmp_path / "notes.md").write_text("x")
    assert [w.name for w in T.discover_worlds(tmp_path)] == ["ascetic-r1"]


def test_select_skips_incomplete_worlds_by_default(tmp_path):
    _world(tmp_path, "a-r1", complete=True, versions=[])
    _world(tmp_path, "a-r2", complete=False, versions=[])
    worlds = T.discover_worlds(tmp_path)
    assert [w.name for w in T.select_worlds(worlds, allow_incomplete=False)] == ["a-r1"]


def test_select_includes_incomplete_worlds_when_previewing(tmp_path):
    _world(tmp_path, "a-r1", complete=True, versions=[])
    _world(tmp_path, "a-r2", complete=False, versions=[])
    assert len(T.select_worlds(T.discover_worlds(tmp_path), allow_incomplete=True)) == 2


def test_select_rejects_a_world_marked_complete_with_no_data(tmp_path):
    _world(tmp_path, "a-r1", complete=True)  # COMPLETE but no versions.jsonl
    assert T.select_worlds(T.discover_worlds(tmp_path), allow_incomplete=False) == []


def test_world_text_survives_a_half_written_line(tmp_path):
    """A live run flushes mid-line; that must not kill the analysis."""
    d = _world(tmp_path, "a-r1", versions=[
        {"status": "canonical", "name": "N", "doctrine": "D"}])
    (d / "decisions.jsonl").write_text(
        json.dumps({"action": {"private_reasoning": "keep it bare"}}) + "\n"
        + '{"action": {"private_reason'  # truncated by a live writer
    )
    reasoning, doctrines = T.world_text(T.discover_worlds(tmp_path)[0])
    assert "bare" in reasoning
    assert doctrines == ["N D"]


def test_world_text_ignores_non_canonical_doctrines(tmp_path):
    _world(tmp_path, "a-r1", versions=[
        {"status": "proposed", "name": "P", "doctrine": "rejected idea"},
        {"status": "canonical", "name": "C", "doctrine": "adopted idea"}])
    assert T.world_text(T.discover_worlds(tmp_path)[0])[1] == ["C adopted idea"]


# ---------------------------------------------------------------- features

def test_artwork_features_extracts_structure(tmp_path):
    d = _world(tmp_path, "ascetic-r1", versions=[
        {"id": 1, "status": "canonical", "created_turn": 4,
         "artwork_path": "artworks/version-1.html"}])
    (d / "artworks").mkdir()
    (d / "artworks/version-1.html").write_text(
        "<div><svg><circle cx='1' cy='1' r='1'/></svg>"
        "<style>@keyframes k{0%{opacity:1}}</style></div>")
    rows = T.artwork_features(T.discover_worlds(tmp_path)[0])
    assert len(rows) == 1
    r = rows[0]
    assert r["charter"] == "ascetic" and r["rep"] == "r1" and r["turn"] == 4
    assert r["n_svg"] == 1 and r["n_div"] == 1 and r["n_canvas"] == 0
    assert r["animated"] == 1
    assert r["n_drawable"] == 1 and r["paintable"] == 1
    assert r["html_bytes"] > 0


def test_artwork_features_detects_absence_of_animation(tmp_path):
    d = _world(tmp_path, "a-r1", versions=[
        {"id": 1, "status": "canonical", "artwork_path": "artworks/version-1.html"}])
    (d / "artworks").mkdir()
    (d / "artworks/version-1.html").write_text(
        "<svg><rect x='0' y='0' width='2' height='2'/></svg>")
    assert T.artwork_features(T.discover_worlds(tmp_path)[0])[0]["animated"] == 0


def test_artwork_features_skips_non_canonical_and_missing_files(tmp_path):
    d = _world(tmp_path, "a-r1", versions=[
        {"id": 1, "status": "proposed", "artwork_path": "artworks/version-1.html"},
        {"id": 2, "status": "canonical", "artwork_path": "artworks/gone.html"}])
    (d / "artworks").mkdir()
    (d / "artworks/version-1.html").write_text("<svg/>")
    assert T.artwork_features(T.discover_worlds(tmp_path)[0]) == []


def test_world_means_collapses_artworks_to_one_vector_per_world():
    rows = [
        {"world": "a-r1", "charter": "a", "rep": "r1", "html_bytes": 100,
         "n_drawable": 2, "n_svg": 1, "n_div": 0, "animated": 1, "distinct_colors": 10},
        {"world": "a-r1", "charter": "a", "rep": "r1", "html_bytes": 300,
         "n_drawable": 4, "n_svg": 1, "n_div": 0, "animated": 0, "distinct_colors": 20},
    ]
    m = T.world_means(rows)["a-r1"]
    assert m["n_artworks"] == 2
    assert m["html_bytes"] == 200 and m["n_drawable"] == 3 and m["animated"] == 0.5


def test_world_means_ignores_blank_colour_readings():
    """An unrendered artwork has no colour count; it must not poison the mean."""
    rows = [
        {"world": "a-r1", "charter": "a", "rep": "r1", "html_bytes": 1, "n_drawable": 1,
         "n_svg": 0, "n_div": 0, "animated": 0, "distinct_colors": 40},
        {"world": "a-r1", "charter": "a", "rep": "r1", "html_bytes": 1, "n_drawable": 1,
         "n_svg": 0, "n_div": 0, "animated": 0, "distinct_colors": ""},
    ]
    assert T.world_means(rows)["a-r1"]["distinct_colors"] == 40


# ---------------------------------------------------------------- F ratio

def test_f_ratio_is_large_when_groups_separate_cleanly():
    F, msb, msw = T.f_ratio([[10.0, 10.1, 9.9], [50.0, 50.1, 49.9]])
    assert F > 100 and msb > msw


def test_f_ratio_is_near_one_when_the_charter_explains_nothing():
    """The H1 falsifier: groups differing no more than replicates of one group."""
    F, _, _ = T.f_ratio([[1.0, 5.0, 9.0], [2.0, 6.0, 8.0], [1.5, 5.5, 8.5]])
    assert F < 1.0


def test_f_ratio_needs_at_least_two_groups():
    assert math.isnan(T.f_ratio([[1.0, 2.0]])[0])
    assert math.isnan(T.f_ratio([])[0])


def test_f_ratio_handles_zero_within_group_variance():
    F, _, msw = T.f_ratio([[1.0, 1.0], [2.0, 2.0]])
    assert math.isinf(F) and msw == 0.0


def test_f_ratio_ignores_nans():
    F, _, _ = T.f_ratio([[1.0, float("nan"), 1.1], [5.0, 5.1, float("nan")]])
    assert not math.isnan(F) and F > 1


def test_f_ratio_needs_more_observations_than_groups():
    assert math.isnan(T.f_ratio([[1.0], [2.0]])[0])


# ---------------------------------------------------------------- doctrine similarity

def test_doctrine_divergence_finds_a_within_charter_gap():
    docs = {
        "ascetic-r1": ("", ["bare quiet mark", "empty field single line"]),
        "ascetic-r2": ("", ["quiet bare line", "single empty mark"]),
        "baroque-r1": ("", ["gold gilded abundance", "layered ornament richly"]),
        "baroque-r2": ("", ["abundance gilded gold", "ornament layered richly"]),
    }
    d = T.doctrine_divergence(docs)
    assert d["within_n"] == 2 and d["across_n"] == 4
    assert d["gap"] > 0 and d["within_mean"] > d["across_mean"]


def test_doctrine_divergence_gap_vanishes_when_charters_share_language():
    docs = {f"{c}-r{i}": ("", ["same words every time"])
            for c in ("a", "b") for i in (1, 2)}
    assert T.doctrine_divergence(docs)["gap"] == pytest.approx(0.0, abs=1e-9)


def test_cosine_bounds():
    v = T.tfidf_vectors([["a", "b"], ["a", "b"], ["c", "d"]])
    assert T.cosine(v[0], v[1]) == pytest.approx(1.0, abs=1e-6)
    assert T.cosine(v[0], v[2]) == pytest.approx(0.0, abs=1e-6)
    assert T.cosine({}, v[0]) == 0.0
