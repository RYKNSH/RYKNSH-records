"""Tests for shadow review module."""

import json
import pytest
from pathlib import Path

from agent.shadow_review import (
    _check_agreement,
    _SHADOW_DIR,
    save_shadow_result,
    generate_accuracy_report,
)


class TestAgreementCheck:
    """Test Velie vs human agreement classification."""

    def test_true_positive(self):
        assert _check_agreement("critical", "changes_requested") == "true_positive"

    def test_true_negative(self):
        assert _check_agreement("clean", "approved") == "true_negative"

    def test_false_positive(self):
        assert _check_agreement("warning", "approved") == "false_positive"

    def test_false_negative(self):
        assert _check_agreement("clean", "changes_requested") == "false_negative"


class TestShadowReviewStorage:
    """Test shadow review save and report."""

    def setup_method(self):
        _SHADOW_DIR.mkdir(parents=True, exist_ok=True)
        # Clean up test files
        for f in _SHADOW_DIR.glob("test__repo_*.json"):
            f.unlink()

    def teardown_method(self):
        for f in _SHADOW_DIR.glob("test__repo_*.json"):
            f.unlink()

    def test_save_and_load(self):
        save_shadow_result(
            repo="test/repo",
            pr_number=1,
            velie_review="This looks risky",
            velie_severity="critical",
            human_reviews=[{"author": "dev", "state": "CHANGES_REQUESTED", "body": "Fix this"}],
            human_outcome="changes_requested",
        )
        path = _SHADOW_DIR / "test__repo_pr1.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["agreement"] == "true_positive"

    def test_accuracy_report_empty(self):
        report = generate_accuracy_report()
        # May or may not have results from other tests
        assert "total" in report

    def test_accuracy_report_with_data(self):
        save_shadow_result("test/repo", 10, "ok", "clean", [], "approved")
        save_shadow_result("test/repo", 11, "issue", "critical", [], "changes_requested")
        save_shadow_result("test/repo", 12, "issue", "warning", [], "approved")

        report = generate_accuracy_report()
        assert report["total"] >= 3
        assert "precision" in report
        assert "recall" in report
        assert "f1_score" in report
