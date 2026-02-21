"""Tests for usage tracking module."""

import json
import pytest
from pathlib import Path

from agent.usage import (
    _USAGE_FILE,
    check_usage_allowed,
    get_usage,
    record_usage,
    update_plan,
    PLAN_LIMITS,
)


class TestUsage:
    """Test usage tracking."""

    def setup_method(self):
        if _USAGE_FILE.exists():
            _USAGE_FILE.unlink()

    def teardown_method(self):
        if _USAGE_FILE.exists():
            _USAGE_FILE.unlink()

    def test_record_usage_creates_file(self):
        record_usage("t1", "test/repo", 1, "claude-sonnet")
        assert _USAGE_FILE.exists()

    def test_get_usage_empty(self):
        usage = get_usage("nonexistent")
        assert usage["review_count"] == 0
        assert usage["plan"] == "free"

    def test_record_and_get(self):
        record_usage("t1", "test/repo", 1, "claude-sonnet")
        record_usage("t1", "test/repo", 2, "claude-sonnet")
        usage = get_usage("t1")
        assert usage["review_count"] == 2

    def test_free_limit(self):
        for i in range(5):
            record_usage("t1", "test/repo", i, "claude-sonnet")
        usage = get_usage("t1")
        assert usage["at_limit"] is True

    def test_check_usage_allowed_under_limit(self):
        record_usage("t1", "test/repo", 1, "claude-sonnet")
        allowed, _ = check_usage_allowed("t1")
        assert allowed is True

    def test_check_usage_blocked_at_limit(self):
        for i in range(5):
            record_usage("t1", "test/repo", i, "claude-sonnet")
        allowed, reason = check_usage_allowed("t1")
        assert allowed is False
        assert "limit" in reason.lower()

    def test_update_plan(self):
        update_plan("t1", "pro")
        usage = get_usage("t1")
        assert usage["plan"] == "pro"
        assert usage["reviews_limit"] == -1  # unlimited

    def test_pro_plan_no_limit(self):
        update_plan("t1", "pro")
        for i in range(10):
            record_usage("t1", "test/repo", i, "claude-sonnet")
        allowed, _ = check_usage_allowed("t1")
        assert allowed is True

    def test_repos_counted(self):
        record_usage("t1", "repo/a", 1, "claude-sonnet")
        record_usage("t1", "repo/b", 2, "claude-sonnet")
        usage = get_usage("t1")
        assert usage["repos_count"] == 2

    def test_invalid_plan_raises(self):
        with pytest.raises(ValueError):
            update_plan("t1", "nonexistent_plan")
