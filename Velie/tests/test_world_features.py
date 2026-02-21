"""Tests for repo_learner, trust, and silence features."""

import json
import pytest
from pathlib import Path

from agent.repo_learner import (
    _MEMORY_DIR,
    classify_bug_pattern,
    get_context_prompt,
    load_memory,
    _save_memory,
)
from agent.trust import (
    _TRUST_FILE,
    get_trust_score,
    record_suggestion_outcome,
    record_review_verdict,
)


class TestBugPatternClassification:
    """Test bug pattern classification from diffs."""

    def test_detects_null_check(self):
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "+    result = data.get('key', '')\n"
        )
        patterns = classify_bug_pattern(diff)
        categories = [p["category"] for p in patterns]
        assert "null_check" in categories

    def test_detects_error_handling(self):
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "+    try:\n"
            "+        do_something()\n"
            "+    except ValueError:\n"
        )
        patterns = classify_bug_pattern(diff)
        categories = [p["category"] for p in patterns]
        assert "error_handling" in categories

    def test_ignores_removed_lines(self):
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "-    try:\n"
            "-        old_code()\n"
        )
        patterns = classify_bug_pattern(diff)
        assert len(patterns) == 0

    def test_empty_diff(self):
        patterns = classify_bug_pattern("")
        assert patterns == []


class TestRepoMemory:
    """Test repo memory loading and context generation."""

    def setup_method(self):
        _MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        safe_name = "test__repo"
        path = _MEMORY_DIR / f"{safe_name}.json"
        if path.exists():
            path.unlink()

    def test_load_nonexistent(self):
        assert load_memory("nonexistent/repo") is None

    def test_save_and_load(self):
        memory = {
            "repo": "test/repo",
            "total_fix_commits": 10,
            "total_patterns": 5,
            "category_counts": {"null_check": 3, "security": 2},
            "hotspots": [{"file": "app.py", "fix_count": 5}],
            "recent_patterns": [],
        }
        _save_memory("test/repo", memory)
        loaded = load_memory("test/repo")
        assert loaded["total_fix_commits"] == 10

    def test_context_prompt_empty(self):
        prompt = get_context_prompt("nonexistent/repo")
        assert prompt == ""

    def test_context_prompt_with_data(self):
        memory = {
            "repo": "test/repo",
            "total_fix_commits": 10,
            "total_patterns": 5,
            "category_counts": {"null_check": 3},
            "hotspots": [{"file": "app.py", "fix_count": 5}],
            "recent_patterns": [],
        }
        _save_memory("test/repo", memory)
        prompt = get_context_prompt("test/repo")
        assert "null_check" in prompt
        assert "app.py" in prompt


class TestTrustScore:
    """Test trust score tracking."""

    def setup_method(self):
        if _TRUST_FILE.exists():
            _TRUST_FILE.unlink()

    def teardown_method(self):
        if _TRUST_FILE.exists():
            _TRUST_FILE.unlink()

    def test_empty_trust_score(self):
        score = get_trust_score()
        assert score["trust_score"] == 0.0
        assert score["total_suggestions"] == 0

    def test_record_suggestion_outcome(self):
        record_suggestion_outcome("test/repo", 1, 10, 8)
        score = get_trust_score()
        assert score["total_suggestions"] == 10
        assert score["total_accepted"] == 8
        assert score["acceptance_rate"] == 0.8

    def test_multiple_repos(self):
        record_suggestion_outcome("repo/a", 1, 10, 8)
        record_suggestion_outcome("repo/b", 2, 5, 3)
        score = get_trust_score()
        assert score["total_suggestions"] == 15

    def test_repo_specific_score(self):
        record_suggestion_outcome("repo/a", 1, 10, 8)
        record_suggestion_outcome("repo/b", 2, 5, 1)
        score_a = get_trust_score("repo/a")
        score_b = get_trust_score("repo/b")
        assert score_a["acceptance_rate"] > score_b["acceptance_rate"]

    def test_record_verdicts(self):
        record_review_verdict("test/repo", 1, True, True)  # true positive
        record_review_verdict("test/repo", 2, True, False)  # false positive
        score = get_trust_score()
        assert score["true_positives"] == 1
        assert score["false_positives"] == 1
        assert score["precision"] == 0.5
