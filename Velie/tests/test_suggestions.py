"""Tests for the suggestion parser and GitHub API formatter."""

import pytest

from agent.suggestions import (
    Suggestion,
    build_review_comments,
    calculate_diff_position,
    parse_suggestions,
)


# ---------------------------------------------------------------------------
# Sample diff for position calculation tests
# ---------------------------------------------------------------------------

SAMPLE_DIFF = """\
diff --git a/server/app.py b/server/app.py
index abc1234..def5678 100644
--- a/server/app.py
+++ b/server/app.py
@@ -10,7 +10,7 @@
 import logging
 from contextlib import asynccontextmanager
 
-from fastapi import FastAPI, Header, HTTPException
+from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
 import httpx
 
 logger = logging.getLogger(__name__)
@@ -20,6 +20,7 @@
 
 def process_data(data):
     result = data.get('key')
+    value = result.strip()
     return result
"""

# ---------------------------------------------------------------------------
# parse_suggestions
# ---------------------------------------------------------------------------

class TestParseSuggestions:
    def test_empty_string(self):
        assert parse_suggestions("") == []

    def test_valid_json_array(self):
        output = """[
            {
                "path": "server/app.py",
                "line": 13,
                "original": "from fastapi import FastAPI",
                "suggested": "from fastapi import BackgroundTasks, FastAPI",
                "reason": "Missing import"
            }
        ]"""
        result = parse_suggestions(output)
        assert len(result) == 1
        assert result[0].path == "server/app.py"
        assert result[0].line == 13

    def test_json_in_markdown_fence(self):
        output = """Here are my suggestions:
```json
[
    {
        "path": "app.py",
        "line": 5,
        "original": "x = 1",
        "suggested": "x = 2",
        "reason": "Wrong value"
    }
]
```"""
        result = parse_suggestions(output)
        assert len(result) == 1

    def test_empty_array(self):
        result = parse_suggestions("[]")
        assert result == []

    def test_invalid_json(self):
        result = parse_suggestions("this is not json")
        assert result == []

    def test_missing_fields_skipped(self):
        output = '[{"path": "app.py", "line": 5}]'
        result = parse_suggestions(output)
        assert result == []

    def test_multiple_suggestions(self):
        output = """[
            {"path": "a.py", "line": 1, "original": "x", "suggested": "y", "reason": "r1"},
            {"path": "b.py", "line": 2, "original": "a", "suggested": "b", "reason": "r2"}
        ]"""
        result = parse_suggestions(output)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# calculate_diff_position
# ---------------------------------------------------------------------------

class TestCalculateDiffPosition:
    def test_finds_added_line(self):
        # Line 23 in new file is the added line: `value = result.strip()`
        pos = calculate_diff_position(SAMPLE_DIFF, "server/app.py", 23)
        assert pos is not None
        assert pos > 0

    def test_finds_modified_line(self):
        # Line 13 in new file is the modified import line
        pos = calculate_diff_position(SAMPLE_DIFF, "server/app.py", 13)
        assert pos is not None

    def test_returns_none_for_missing_file(self):
        pos = calculate_diff_position(SAMPLE_DIFF, "nonexistent.py", 10)
        assert pos is None

    def test_returns_none_for_missing_line(self):
        pos = calculate_diff_position(SAMPLE_DIFF, "server/app.py", 999)
        assert pos is None


# ---------------------------------------------------------------------------
# build_review_comments
# ---------------------------------------------------------------------------

class TestBuildReviewComments:
    def test_builds_comment_with_suggestion(self):
        suggestions = [
            Suggestion(
                path="server/app.py",
                line=13,
                original="from fastapi import FastAPI",
                suggested="from fastapi import BackgroundTasks, FastAPI",
                reason="Missing import",
            )
        ]
        comments = build_review_comments(suggestions, SAMPLE_DIFF)
        assert len(comments) == 1
        assert comments[0]["path"] == "server/app.py"
        assert "```suggestion" in comments[0]["body"]
        assert "Missing import" in comments[0]["body"]

    def test_skips_unfound_position(self):
        suggestions = [
            Suggestion(
                path="nonexistent.py",
                line=1,
                original="x",
                suggested="y",
                reason="test",
            )
        ]
        comments = build_review_comments(suggestions, SAMPLE_DIFF)
        assert len(comments) == 0

    def test_empty_suggestions(self):
        comments = build_review_comments([], SAMPLE_DIFF)
        assert comments == []
