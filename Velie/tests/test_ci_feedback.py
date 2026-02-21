"""Tests for CI monitor and feedback modules."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from agent.ci_monitor import get_check_runs
from agent.feedback import record_feedback, get_feedback_stats, _FEEDBACK_FILE


class TestGetCheckRuns:
    """Test check run data extraction."""

    @pytest.mark.asyncio
    async def test_extracts_check_run_fields(self):
        import httpx

        mock_response = httpx.Response(
            200,
            json={
                "check_runs": [
                    {
                        "name": "build",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://github.com/test/runs/1",
                    },
                    {
                        "name": "lint",
                        "status": "completed",
                        "conclusion": "failure",
                        "html_url": "https://github.com/test/runs/2",
                    },
                ]
            },
            request=httpx.Request("GET", "https://api.github.com/test"),
        )

        class MockClient:
            async def get(self, url, headers=None):
                return mock_response

        result = await get_check_runs(MockClient(), "test/repo", "abc123", {})
        assert len(result) == 2
        assert result[0]["name"] == "build"
        assert result[0]["conclusion"] == "success"
        assert result[1]["conclusion"] == "failure"


class TestFeedback:
    """Test feedback recording and stats."""

    def setup_method(self):
        """Clean up feedback file before each test."""
        if _FEEDBACK_FILE.exists():
            _FEEDBACK_FILE.unlink()

    def teardown_method(self):
        """Clean up feedback file after each test."""
        if _FEEDBACK_FILE.exists():
            _FEEDBACK_FILE.unlink()

    def test_record_feedback_creates_file(self):
        record_feedback(
            pr_number=1,
            repo_full_name="test/repo",
            feedback_type="fix_created",
        )
        assert _FEEDBACK_FILE.exists()
        data = json.loads(_FEEDBACK_FILE.read_text())
        assert len(data) == 1
        assert data[0]["feedback_type"] == "fix_created"

    def test_record_multiple_feedback(self):
        record_feedback(1, "test/repo", "fix_created")
        record_feedback(1, "test/repo", "ci_passed")
        data = json.loads(_FEEDBACK_FILE.read_text())
        assert len(data) == 2
        # Newest first
        assert data[0]["feedback_type"] == "ci_passed"

    def test_get_feedback_stats(self):
        record_feedback(1, "test/repo", "fix_created")
        record_feedback(2, "test/repo", "ci_passed")
        record_feedback(3, "test/repo", "ci_failed")
        record_feedback(4, "test/repo", "ci_passed")

        stats = get_feedback_stats()
        assert stats["total"] == 4
        assert stats["by_type"]["ci_passed"] == 2
        assert stats["by_type"]["ci_failed"] == 1

    def test_get_feedback_stats_filtered(self):
        record_feedback(1, "test/repo", "fix_created")
        record_feedback(2, "other/repo", "ci_passed")

        stats = get_feedback_stats(repo_full_name="test/repo")
        assert stats["total"] == 1

    def test_get_feedback_stats_empty(self):
        stats = get_feedback_stats()
        assert stats["total"] == 0

    def test_feedback_capped_at_1000(self):
        for i in range(1005):
            record_feedback(i, "test/repo", "fix_created")
        data = json.loads(_FEEDBACK_FILE.read_text())
        assert len(data) == 1000
