"""Shared fixtures for messiah-bench test suite."""

import copy
import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# sim.py fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_state():
    """Return a fresh initial state matching sim.make_initial_state()."""
    import sim
    with patch.object(sim, "SACRAMENTS_DIR", sim.Path("/tmp/messiah-test-sacraments")):
        state = sim.make_initial_state()
    return state


# ---------------------------------------------------------------------------
# messiah_bench.py fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_messiah_state():
    """Return a fresh initial state matching messiah_bench.make_initial_state()."""
    import messiah_bench
    with patch.object(messiah_bench, "SACRAMENTS_DIR", messiah_bench.Path("/tmp/messiah-test-sacraments")):
        state = messiah_bench.make_initial_state()
    return state


# ---------------------------------------------------------------------------
# LLM mock fixture (shared)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm():
    """Patch call_llm in both sim and messiah_bench to return pray by default."""
    default_response = '{"action": "pray"}'

    with patch("sim.call_llm", return_value=default_response) as sim_mock, \
         patch("messiah_bench.call_llm", return_value=default_response) as mb_mock:
        yield {"sim": sim_mock, "messiah_bench": mb_mock}
