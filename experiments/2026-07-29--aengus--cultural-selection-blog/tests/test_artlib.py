"""Offline tests for artlib. No network, no chromium, tiny fixtures."""

from __future__ import annotations

import json
import random
import re

import pytest

import artlib as A


# ---------------------------------------------------------------- fixtures

def art(art_id, regime, religion, turn, version=1, html="<div>x</div>"):
    return A.Artwork(
        art_id=art_id, regime=regime, religion=religion, lineage=religion,
        version=version, turn=turn, html=html, source="fixture",
    )


@pytest.fixture
def tiny():
    """3 regimes x 2 religions x spread of turns."""
    out = []
    for regime, hi in (("v7", 100), ("v8", 100), ("minimal", 100)):
        for rel in ("A", "B"):
            for turn in (0, 25, 50, 75, 100):
                out.append(art(f"{regime}-{rel}-{turn}", regime, rel, turn))
    return out


# ---------------------------------------------------------------- sampling

def test_time_decile_bounds():
    assert A.time_decile(0, 0, 100) == 0
    assert A.time_decile(100, 0, 100) == 9   # top end clamps into the last bin
    assert A.time_decile(50, 0, 100) == 5
    assert A.time_decile(7, 0, 100) == 0
    assert A.time_decile(5, 5, 5) == 0       # degenerate range


def test_stratified_sample_is_deterministic(tiny):
    a = A.stratified_sample(tiny, 12, seed=1)
    b = A.stratified_sample(tiny, 12, seed=1)
    assert [x.art_id for x in a] == [x.art_id for x in b]
    assert [x.art_id for x in A.stratified_sample(tiny, 12, seed=2)] != [x.art_id for x in a]


def test_stratified_sample_spreads_across_regimes(tiny):
    sample = A.stratified_sample(tiny, 12, seed=0)
    assert len(sample) == 12
    counts = {r: sum(1 for a in sample if a.regime == r) for r in ("v7", "v8", "minimal")}
    # round-robin means every regime gets an equal share when cells are equal
    assert set(counts.values()) == {4}, counts


def test_stratified_sample_spreads_across_religions_and_time(tiny):
    sample = A.stratified_sample(tiny, 18, seed=0)
    assert {a.religion for a in sample} == {"A", "B"}
    # at least 4 distinct time deciles represented
    bounds = A.regime_bounds(tiny)
    deciles = {A.time_decile(a.turn, *bounds[a.regime]) for a in sample}
    assert len(deciles) >= 4, deciles


def test_stratified_sample_is_unbiased_toward_one_big_regime():
    """A regime with 100x the rows must not swallow the sample."""
    arts = [art(f"big-{i}", "v7", "R", i % 100) for i in range(1000)]
    arts += [art(f"small-{i}", "minimal", "R", i) for i in range(10)]
    sample = A.stratified_sample(arts, 20, seed=0)
    n_small = sum(1 for a in sample if a.regime == "minimal")
    assert n_small >= 5, f"minimal regime under-sampled: {n_small}"


def test_stratified_sample_caps_at_available(tiny):
    assert len(A.stratified_sample(tiny, 10_000, seed=0)) == len(tiny)
    assert A.stratified_sample(tiny, 0, seed=0) == []
    assert A.stratified_sample([], 5, seed=0) == []


def test_stratified_sample_has_no_duplicates(tiny):
    sample = A.stratified_sample(tiny, 25, seed=3)
    ids = [a.art_id for a in sample]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------- pairing

def test_build_pairs_mixes_cross_and_within_regime(tiny):
    pairs = A.build_pairs(tiny, 40, seed=0)
    assert len(pairs) == 40
    by_id = {a.art_id: a for a in tiny}
    cross = sum(1 for x, y in pairs if by_id[x].regime != by_id[y].regime)
    within = len(pairs) - cross
    assert cross > 0 and within > 0, (cross, within)
    assert abs(cross - 20) <= 2, cross  # ~50/50 split


def test_build_pairs_no_self_or_duplicate_pairs(tiny):
    pairs = A.build_pairs(tiny, 60, seed=1)
    assert all(x != y for x, y in pairs)
    keys = {frozenset(p) for p in pairs}
    assert len(keys) == len(pairs)


def test_build_pairs_handles_single_regime():
    arts = [art(f"v7-{i}", "v7", "A", i) for i in range(6)]
    pairs = A.build_pairs(arts, 10, seed=0)
    assert len(pairs) == 10
    assert all(x != y for x, y in pairs)


# ---------------------------------------------------------------- elo

def test_elo_expected_symmetric():
    assert A.elo_expected(1500, 1500) == pytest.approx(0.5)
    assert A.elo_expected(1900, 1500) > 0.9
    assert A.elo_expected(1500, 1900) < 0.1


def test_elo_update_is_zero_sum():
    ra, rb = A.elo_update(1500, 1500, a_won=True, k=24)
    assert ra == pytest.approx(1512)
    assert rb == pytest.approx(1488)
    assert ra + rb == pytest.approx(3000)


def test_elo_update_upset_moves_more_than_expected_win():
    strong_beats_weak, _ = A.elo_update(1800, 1200, a_won=True)
    weak_beats_strong, _ = A.elo_update(1200, 1800, a_won=True)
    assert (weak_beats_strong - 1200) > (strong_beats_weak - 1800)


def test_run_elo_orders_a_dominant_artwork_first():
    judgments = [{"winner_id": "good", "loser_id": f"bad{i%3}"} for i in range(30)]
    ratings, record = A.run_elo(judgments)
    assert max(ratings, key=ratings.get) == "good"
    assert record["good"]["wins"] == 30
    assert sum(r["losses"] for r in record.values()) == 30


def test_run_elo_ignores_malformed_rows():
    judgments = [
        {"winner_id": "a", "loser_id": "b"},
        {"winner_id": "a", "loser_id": "a"},   # self-match
        {"winner_id": None, "loser_id": "b"},  # missing winner
        {},                                    # empty
    ]
    ratings, record = A.run_elo(judgments)
    assert set(ratings) == {"a", "b"}
    assert record["a"]["wins"] == 1


# ---------------------------------------------------------------- judgment parsing

def test_parse_judgment_plain_json():
    v = A.parse_judgment('{"winner": "A", "confidence": 4, "reason": "better balance"}')
    assert v == {"winner": "A", "confidence": 4, "reason": "better balance"}


def test_parse_judgment_code_fenced():
    v = A.parse_judgment('```json\n{"winner":"B","confidence":2,"reason":"r"}\n```')
    assert v["winner"] == "B" and v["confidence"] == 2


def test_parse_judgment_with_prose_around_it():
    v = A.parse_judgment('Sure! Here is my verdict:\n{"winner": "b", "confidence": 5, '
                         '"reason": "x"}\nHope that helps.')
    assert v["winner"] == "B"


def test_parse_judgment_clamps_confidence():
    assert A.parse_judgment('{"winner":"A","confidence":99}')["confidence"] == 5
    assert A.parse_judgment('{"winner":"A","confidence":-4}')["confidence"] == 1
    assert A.parse_judgment('{"winner":"A","confidence":"nope"}')["confidence"] == 3
    assert A.parse_judgment('{"winner":"A"}')["confidence"] == 3


@pytest.mark.parametrize("bad", [
    "",
    "   ",
    "I cannot judge these images.",
    '{"winner": "C", "confidence": 3}',
    '{"confidence": 3, "reason": "no winner field"}',
    "{not json at all",
])
def test_parse_judgment_rejects_malformed(bad):
    with pytest.raises(ValueError):
        A.parse_judgment(bad)


# ---------------------------------------------------------------- A/B derandomization

def test_derandomize_maps_slots_back_to_ids():
    assert A.derandomize("A", "art-x", "art-y") == ("art-x", "art-y")
    assert A.derandomize("B", "art-x", "art-y") == ("art-y", "art-x")


def test_derandomize_rejects_bad_slot():
    with pytest.raises(ValueError):
        A.derandomize("X", "a", "b")


def test_assign_slots_is_balanced_and_lossless():
    rng = random.Random(0)
    first_is_x = 0
    n = 2000
    for _ in range(n):
        a, b = A.assign_slots("x", "y", rng)
        assert {a, b} == {"x", "y"}   # never drops or duplicates an artwork
        first_is_x += a == "x"
    assert 0.45 < first_is_x / n < 0.55, first_is_x / n


def test_position_bias_cancels_end_to_end():
    """A judge that always picks slot A must produce a 50/50 win rate overall."""
    rng = random.Random(7)
    wins = {"x": 0, "y": 0}
    for _ in range(2000):
        slot_a, slot_b = A.assign_slots("x", "y", rng)
        winner, _loser = A.derandomize("A", slot_a, slot_b)  # judge always says A
        wins[winner] += 1
    assert 0.45 < wins["x"] / 2000 < 0.55, wins


# ---------------------------------------------------------------- cost log

def test_costlog_line_format():
    line = A.costlog_line("2026-08-06 12:00 UTC", "pilot", "claude-haiku-4-5-20251001",
                          30, 40000, 2700, 0.0535, 61.2)
    assert line.startswith("| 2026-08-06 12:00 UTC | pilot | claude-haiku-4-5-20251001 |")
    assert line.endswith("\n")
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    assert len(cells) == 8
    assert cells[3] == "30" and cells[4] == "40000" and cells[5] == "2700"
    assert cells[6] == "$0.0535"
    assert cells[7] == "61.2"


def test_append_costlog_writes_header_once(tmp_path):
    p = tmp_path / "COSTLOG.md"
    A.append_costlog(p, "pilot", A.CLAUDE_MODEL, 1, 100, 10, 0.001, 1.0)
    A.append_costlog(p, "full", A.GEMINI_MODEL, 2, 200, 20, 0.002, 2.0)
    text = p.read_text()
    assert text.count("| date | phase | model |") == 1
    assert len([l for l in text.splitlines() if l.startswith("| 20")]) == 2


def test_cost_usd_matches_published_rates():
    # haiku 4.5: $1/MTok in, $5/MTok out
    assert A.cost_usd(A.CLAUDE_MODEL, 1_000_000, 0) == pytest.approx(1.00)
    assert A.cost_usd(A.CLAUDE_MODEL, 0, 1_000_000) == pytest.approx(5.00)
    assert A.cost_usd(A.GEMINI_MODEL, 1_000_000, 1_000_000) == pytest.approx(2.80)
    assert A.cost_usd("unknown-model", 1_000_000, 1_000_000) == 0.0


# ---------------------------------------------------------------- html wrapping / io

def test_wrap_html_wraps_fragments_only():
    wrapped = A.wrap_html("<svg width='10'></svg>")
    assert wrapped.startswith("<!doctype html>") and "<svg" in wrapped
    doc = "<!doctype html><html><body>hi</body></html>"
    assert A.wrap_html(doc) == doc
    assert A.wrap_html("<html><body>hi</body></html>").count("<html") == 1


def test_wrap_html_injects_fit_to_frame_scaling():
    """Fragments must be scaled up, or a 200x200 SVG loses to a full-frame one on size."""
    wrapped = A.wrap_html("<svg width='200' height='200'></svg>")
    assert 'id="art-root"' in wrapped
    assert "getBoundingClientRect" in wrapped
    assert str(A.FILL_FRACTION) in wrapped
    assert "{body}" not in wrapped and "{fill}" not in wrapped  # format placeholders consumed


def test_wrap_html_leaves_full_documents_alone():
    """Whole documents already size themselves to the viewport."""
    doc = "<!doctype html><html><body><div>hi</div></body></html>"
    assert "art-root" not in A.wrap_html(doc)


def test_write_jsonl_atomic_roundtrip(tmp_path):
    p = tmp_path / "m.jsonl"
    arts = [art("a-1", "v7", "R", 1), art("a-2", "v8", "R", 2)]
    A.write_jsonl_atomic(p, arts)
    assert not (tmp_path / "m.jsonl.tmp").exists()   # temp file cleaned up
    back = A.manifest_to_artworks(A.read_jsonl(p))
    assert [a.art_id for a in back] == ["a-1", "a-2"]
    assert back[0].html == arts[0].html


def test_append_jsonl_never_truncates(tmp_path):
    p = tmp_path / "j.jsonl"
    for i in range(5):
        A.append_jsonl(p, {"i": i})
    rows = A.read_jsonl(p)
    assert [r["i"] for r in rows] == [0, 1, 2, 3, 4]


def test_read_jsonl_missing_file(tmp_path):
    assert A.read_jsonl(tmp_path / "nope.jsonl") == []


# ---------------------------------------------------------------- concurrency

def test_append_jsonl_loses_nothing_under_thread_hammering(tmp_path):
    """Every concurrent append lands exactly once and stays parseable.

    Note this passes with the lock removed too: on Linux an O_APPEND write to a
    regular file does not interleave. The lock is what makes that guarantee ours
    rather than the platform's — `test_append_jsonl_serializes_writers` is the
    test that actually pins it.
    """
    from concurrent.futures import ThreadPoolExecutor

    p = tmp_path / "j.jsonl"
    n = 400
    rows = [{"i": i, "pad": "x" * 3000} for i in range(n)]
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda r: A.append_jsonl(p, r), rows))

    lines = p.read_text().splitlines()
    assert len(lines) == n, f"expected {n} lines, got {len(lines)}"
    parsed = [json.loads(l) for l in lines]
    assert sorted(r["i"] for r in parsed) == list(range(n))
    assert all(len(r["pad"]) == 3000 for r in parsed)


def test_append_jsonl_serializes_writers(tmp_path):
    """Holding the module lock must block any other thread's append."""
    import threading

    p = tmp_path / "j.jsonl"
    started = threading.Event()
    finished = threading.Event()

    def writer():
        started.set()
        A.append_jsonl(p, {"i": 1})
        finished.set()

    with A._APPEND_LOCK:
        t = threading.Thread(target=writer, daemon=True)
        t.start()
        assert started.wait(2)
        # Lock is held here, so the writer must not have gotten through.
        assert not finished.wait(0.3), "append_jsonl wrote while the lock was held"

    assert finished.wait(2), "append_jsonl never completed after the lock released"
    t.join(2)
    assert A.read_jsonl(p) == [{"i": 1}]


def test_cost_tracker_totals_are_exact_under_threads():
    from concurrent.futures import ThreadPoolExecutor

    tracker = A.CostTracker()
    n = 500
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda _: tracker.add(A.CLAUDE_MODEL, 1000, 100, 0.5), range(n)))

    snap = tracker.snapshot()[A.CLAUDE_MODEL]
    assert snap["calls"] == n
    assert snap["in"] == 1000 * n
    assert snap["out"] == 100 * n
    assert snap["wall"] == pytest.approx(0.5 * n)
    assert tracker.total_usd() == pytest.approx(A.cost_usd(A.CLAUDE_MODEL, 1000, 100) * n)


def test_cost_tracker_error_count_under_threads():
    from concurrent.futures import ThreadPoolExecutor

    tracker = A.CostTracker()
    with ThreadPoolExecutor(max_workers=16) as pool:
        seen = list(pool.map(lambda _: tracker.add_error(), range(300)))
    assert tracker.errors == 300
    assert sorted(seen) == list(range(1, 301))  # every caller got a distinct count


def test_cost_tracker_snapshot_is_a_copy():
    tracker = A.CostTracker()
    tracker.add(A.GEMINI_MODEL, 10, 1, 0.1)
    snap = tracker.snapshot()
    snap[A.GEMINI_MODEL]["calls"] = 999
    assert tracker.snapshot()[A.GEMINI_MODEL]["calls"] == 1


# ---------------------------------------------------------------- retry

@pytest.mark.parametrize("exc", [
    type("RateLimitError", (Exception,), {})("429 too many requests"),
    type("APIStatusError", (Exception,), {"status_code": 503})("unavailable"),
    type("OverloadedError", (Exception,), {})("overloaded_error"),
    type("APIConnectionError", (Exception,), {})("connection reset"),
    type("Whatever", (Exception,), {"status_code": 529})("overloaded"),
])
def test_is_retryable_true_for_transient(exc):
    assert A.is_retryable(exc)


@pytest.mark.parametrize("exc", [
    type("BadRequestError", (Exception,), {"status_code": 400})("bad request"),
    type("AuthenticationError", (Exception,), {"status_code": 401})("bad key"),
    type("NotFoundError", (Exception,), {"status_code": 404})("no model"),
    ValueError("no JSON object in judge response"),
])
def test_is_retryable_false_for_permanent(exc):
    assert not A.is_retryable(exc)


def _flaky(n_failures, exc_factory):
    """A fake judge_pair that fails n times then succeeds."""
    state = {"calls": 0}

    def fn(judge, a, b, keys):
        state["calls"] += 1
        if state["calls"] <= n_failures:
            raise exc_factory()
        return {"judge": judge, "raw": "{}", "verdict": {"winner": "A", "confidence": 3,
                "reason": ""}, "tokens": {"input_tokens": 1, "output_tokens": 1},
                "wall_s": 0.0}
    return fn, state


def test_retry_recovers_from_transient_failure():
    rate_limit = type("RateLimitError", (Exception,), {"status_code": 429})
    fn, state = _flaky(2, lambda: rate_limit("slow down"))
    slept = []
    res = A.judge_pair_with_retry("j", "a.png", "b.png", {}, retries=2,
                                  sleep=slept.append, _judge_fn=fn)
    assert res["verdict"]["winner"] == "A"
    assert state["calls"] == 3          # 1 attempt + 2 retries
    assert res["retries"] == 2
    assert slept == [2.0, 4.0]          # exponential backoff


def test_retry_gives_up_after_budget():
    rate_limit = type("RateLimitError", (Exception,), {"status_code": 429})
    fn, state = _flaky(99, lambda: rate_limit("slow down"))
    with pytest.raises(Exception):
        A.judge_pair_with_retry("j", "a.png", "b.png", {}, retries=2,
                                sleep=lambda s: None, _judge_fn=fn)
    assert state["calls"] == 3          # bounded, does not loop forever


def test_retry_does_not_retry_permanent_errors():
    """A malformed judge reply is deterministic — retrying it just burns money."""
    fn, state = _flaky(99, lambda: ValueError("no JSON object"))
    with pytest.raises(ValueError):
        A.judge_pair_with_retry("j", "a.png", "b.png", {}, retries=2,
                                sleep=lambda s: None, _judge_fn=fn)
    assert state["calls"] == 1


def test_retry_absent_key_when_first_attempt_succeeds():
    fn, state = _flaky(0, lambda: RuntimeError("unused"))
    res = A.judge_pair_with_retry("j", "a.png", "b.png", {}, _judge_fn=fn)
    assert state["calls"] == 1
    assert "retries" not in res


# ---------------------------------------------------------------- key loading

def test_load_keys_env_overrides_stale_dotenv(tmp_path, monkeypatch):
    """The repo .env's ANTHROPIC_API_KEY is stale; the exported one must win."""
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=stale-from-file\nGOOGLE_API_KEY=g-from-file\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fresh-from-env")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    keys = A.load_keys(env_file)
    assert keys["ANTHROPIC_API_KEY"] == "fresh-from-env"
    assert keys["GOOGLE_API_KEY"] == "g-from-file"  # .env still fills the gap


def test_load_keys_drops_empty_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=\nGOOGLE_API_KEY=g\n")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    keys = A.load_keys(env_file)
    assert "ANTHROPIC_API_KEY" not in keys
    assert keys["GOOGLE_API_KEY"] == "g"
