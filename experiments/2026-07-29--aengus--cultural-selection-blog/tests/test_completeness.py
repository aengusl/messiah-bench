"""Tests for the completeness report's stats and row building. No I/O, no network."""

from __future__ import annotations

import pytest

import artlib as A
import completeness_report as R


# ---------------------------------------------------------------- wilson interval

def test_wilson_centre_matches_proportion_in_the_easy_case():
    p, lo, hi = R.wilson(50, 100)
    assert p == pytest.approx(0.5)
    assert lo < 0.5 < hi
    assert lo == pytest.approx(1 - hi, abs=1e-9)  # symmetric at p=0.5


def test_wilson_stays_inside_zero_one_at_the_extremes():
    """The whole reason for Wilson over normal-approx: these proportions sit at 0 and 1."""
    for k, n in ((0, 10), (10, 10), (0, 1), (1, 1), (86, 86)):
        p, lo, hi = R.wilson(k, n)
        assert 0.0 <= lo <= hi <= 1.0, (k, n, lo, hi)


def test_wilson_interval_narrows_as_n_grows():
    _, lo_small, hi_small = R.wilson(9, 10)
    _, lo_big, hi_big = R.wilson(900, 1000)
    assert (hi_big - lo_big) < (hi_small - lo_small)


def test_wilson_at_p_one_has_upper_bound_at_or_below_one():
    """At p=1 the interval is not centred on p — the plot must clamp the whisker."""
    p, lo, hi = R.wilson(9, 9)
    assert p == 1.0
    assert hi <= 1.0
    assert lo < 1.0


def test_wilson_empty_sample():
    assert R.wilson(0, 0) == (0.0, 0.0, 0.0)


# ---------------------------------------------------------------- median

@pytest.mark.parametrize("xs,expected", [
    ([], 0.0),
    ([5], 5.0),
    ([1, 3], 2.0),
    ([1, 2, 3], 2.0),
    ([3, 1, 2], 2.0),
])
def test_median(xs, expected):
    assert R.median(xs) == expected


# ---------------------------------------------------------------- row building

def _art(html, turn=0, regime="v7"):
    return A.Artwork(art_id="a", regime=regime, religion="r", lineage="l",
                     version=1, turn=turn, html=html, source="fixture")


def test_analyse_marks_a_complete_artwork_paintable():
    row = R.analyse(_art("<svg><circle cx='1' cy='1' r='1'/></svg>"), "canon")
    assert row["paintable"] == 1
    assert row["truncated"] == 0
    assert row["n_drawable"] == 1
    assert row["html_bytes"] > 0


def test_analyse_marks_a_truncated_empty_artwork():
    """The dominant shape in the v7/v8 corpora: defs and keyframes, cut off."""
    row = R.analyse(_art("<svg><defs><radialGradient id='g'><stop offset='0%'/>"), "canon")
    assert row["truncated"] == 1
    assert row["paintable"] == 0
    assert row["n_drawable"] == 0


def test_analyse_carries_the_group_label():
    assert R.analyse(_art("<svg/>"), "proposal_rejected")["group"] == "proposal_rejected"


# ---------------------------------------------------------------- decile series

def test_decile_series_bins_and_orders_by_turn():
    rows = [{"turn": t, "paintable": 1 if t < 50 else 0, "n_drawable": 3 if t < 50 else 0}
            for t in range(0, 100, 10)]
    xs, paint, drawable = R.decile_series(rows)
    assert xs == sorted(xs)
    assert paint[0][0] == 1.0        # early bins fully paintable
    assert paint[-1][0] == 0.0       # late bins empty
    assert drawable[0] == 3 and drawable[-1] == 0


def test_decile_series_reports_n_per_bin():
    rows = [{"turn": 0, "paintable": 1, "n_drawable": 1} for _ in range(7)]
    xs, paint, _ = R.decile_series(rows)
    assert len(xs) == 1
    assert paint[0][3] == 7          # (p, lo, hi, n)


def test_decile_series_handles_empty_input():
    assert R.decile_series([]) == ([], [], [])


def test_decile_series_handles_a_single_turn_value():
    """A run where every artwork shares one turn must not divide by zero."""
    rows = [{"turn": 5, "paintable": 1, "n_drawable": 2} for _ in range(3)]
    xs, paint, drawable = R.decile_series(rows)
    assert len(xs) == 1 and paint[0][0] == 1.0 and drawable[0] == 2


# ---------------------------------------------------------------- csv contract

def test_csv_columns_match_what_analyse_produces():
    row = R.analyse(_art("<svg><rect x='1' y='1' width='2' height='2'/></svg>"), "canon")
    assert set(R.CSV_COLS) <= set(row), "CSV would KeyError on a missing column"
