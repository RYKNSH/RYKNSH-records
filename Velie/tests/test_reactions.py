"""Tests for review reactions (PMF measurement)."""

import json
import pytest
from pathlib import Path

from agent.reactions import (
    record_reaction,
    get_reaction_stats,
    get_review_reaction,
    _REACTIONS_FILE,
    _DATA_DIR,
)


class TestReactions:
    """Test review reaction recording and stats."""

    def setup_method(self):
        _DATA_DIR.mkdir(exist_ok=True)
        if _REACTIONS_FILE.exists():
            self._backup = _REACTIONS_FILE.read_text()
        else:
            self._backup = None
        # Start fresh
        if _REACTIONS_FILE.exists():
            _REACTIONS_FILE.unlink()

    def teardown_method(self):
        if self._backup is not None:
            _REACTIONS_FILE.write_text(self._backup)
        elif _REACTIONS_FILE.exists():
            _REACTIONS_FILE.unlink()

    def test_record_helpful(self):
        result = record_reaction("rev-1", "helpful")
        assert result["total"] == 1
        assert result["helpful"] == 1
        assert result["helpfulness_rate"] == 1.0

    def test_record_not_helpful(self):
        result = record_reaction("rev-2", "not_helpful")
        assert result["total"] == 1
        assert result["not_helpful"] == 1
        assert result["helpfulness_rate"] == 0.0

    def test_mixed_reactions(self):
        record_reaction("rev-1", "helpful")
        record_reaction("rev-2", "helpful")
        result = record_reaction("rev-3", "not_helpful")
        assert result["total"] == 3
        assert result["helpful"] == 2
        assert result["not_helpful"] == 1
        assert result["helpfulness_rate"] == pytest.approx(0.667, abs=0.01)
        assert result["nps_proxy"] == pytest.approx(33.3, abs=0.1)

    def test_get_review_reaction(self):
        record_reaction("rev-test", "helpful", comment="good review")
        reaction = get_review_reaction("rev-test")
        assert reaction is not None
        assert reaction["reaction"] == "helpful"
        assert reaction["comment"] == "good review"

    def test_get_nonexistent_reaction(self):
        assert get_review_reaction("nonexistent") is None

    def test_invalid_reaction_raises(self):
        with pytest.raises(ValueError):
            record_reaction("rev-1", "invalid")

    def test_nps_proxy_calculation(self):
        record_reaction("r1", "helpful")
        record_reaction("r2", "helpful")
        record_reaction("r3", "helpful")
        result = record_reaction("r4", "not_helpful")
        # NPS proxy = (3 - 1) / 4 * 100 = 50.0
        assert result["nps_proxy"] == 50.0
