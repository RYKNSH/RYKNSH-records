"""Tests for self-improvement and health monitoring modules."""

import json
import pytest
from pathlib import Path

from agent.self_improve import (
    _LEARNING_FILE,
    analyze_feedback_patterns,
    get_quality_trend,
    record_quality_score,
)
from agent.health import (
    _HEALTH_FILE,
    get_health_summary,
    record_error,
    record_startup,
    should_alert,
)


class TestSelfImprove:
    """Test self-improvement engine."""

    def setup_method(self):
        for f in [_LEARNING_FILE]:
            if f.exists():
                f.unlink()

    def teardown_method(self):
        for f in [_LEARNING_FILE]:
            if f.exists():
                f.unlink()

    def test_record_quality_score(self):
        record_quality_score(1, "test/repo", 0.85)
        assert _LEARNING_FILE.exists()

    def test_get_quality_trend_empty(self):
        trend = get_quality_trend()
        assert trend["count"] == 0
        assert trend["trend"] == "neutral"

    def test_get_quality_trend_with_data(self):
        for i in range(5):
            record_quality_score(i, "test/repo", 0.7)
        trend = get_quality_trend()
        assert trend["count"] == 5
        assert trend["average"] == 0.7

    def test_analyze_feedback_patterns_empty(self):
        result = analyze_feedback_patterns()
        assert result["patterns"] == []


class TestHealth:
    """Test health monitoring."""

    def setup_method(self):
        if _HEALTH_FILE.exists():
            _HEALTH_FILE.unlink()

    def teardown_method(self):
        if _HEALTH_FILE.exists():
            _HEALTH_FILE.unlink()

    def test_record_startup(self):
        record_startup()
        assert _HEALTH_FILE.exists()

    def test_get_health_summary_empty(self):
        summary = get_health_summary()
        assert summary["status"] == "healthy"
        assert summary["total_errors"] == 0

    def test_record_error(self):
        record_error("test", "test error")
        summary = get_health_summary()
        assert summary["total_errors"] == 1

    def test_should_alert_healthy(self):
        alert, reason = should_alert()
        assert alert is False

    def test_should_alert_degraded(self):
        for i in range(10):
            record_error("test", f"error {i}")
        alert, reason = should_alert(threshold=5)
        assert alert is True

    def test_health_status_degraded(self):
        for i in range(10):
            record_error("test", f"error {i}")
        summary = get_health_summary()
        assert summary["status"] == "degraded"

    def test_error_types_tracked(self):
        record_error("github_api", "rate limit")
        record_error("github_api", "timeout")
        record_error("llm", "token limit")
        summary = get_health_summary()
        assert summary["error_types"]["github_api"] == 2
        assert summary["error_types"]["llm"] == 1
