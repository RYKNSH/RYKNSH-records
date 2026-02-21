"""Velie QA Agent — Suggestion Parser & GitHub API Formatter.

Converts Claude's structured JSON suggestions into GitHub PR Review API
format with inline code suggestions.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A single code fix suggestion."""

    path: str
    line: int
    original: str
    suggested: str
    reason: str


def parse_suggestions(claude_output: str) -> list[Suggestion]:
    """Parse Claude's JSON output into a list of Suggestion objects.

    Handles cases where the output contains markdown code fences or
    extra text around the JSON array.
    """
    if not claude_output or not claude_output.strip():
        return []

    text = claude_output.strip()

    # Strip markdown code fences if present
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # Try to find a JSON array
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if not array_match:
        logger.debug("No JSON array found in Claude suggestion output")
        return []

    try:
        data = json.loads(array_match.group(0))
    except json.JSONDecodeError:
        logger.warning("Failed to parse suggestion JSON")
        return []

    if not isinstance(data, list):
        return []

    suggestions: list[Suggestion] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            suggestions.append(Suggestion(
                path=str(item["path"]),
                line=int(item["line"]),
                original=str(item["original"]),
                suggested=str(item["suggested"]),
                reason=str(item["reason"]),
            ))
        except (KeyError, ValueError, TypeError):
            logger.debug("Skipping malformed suggestion: %s", item)
            continue

    logger.info("Parsed %d suggestions from Claude output", len(suggestions))
    return suggestions


def calculate_diff_position(diff_text: str, target_path: str, target_line: int) -> int | None:
    """Calculate the position in a unified diff for a given file and line number.

    GitHub's PR Review API requires a `position` which is the line number
    within the diff hunk (1-indexed from the first @@ line of the file).

    Args:
        diff_text: Full unified diff text.
        target_path: File path to find (e.g. "src/app.py").
        target_line: Line number in the NEW file (right side of diff).

    Returns:
        Position in the diff, or None if not found.
    """
    in_target_file = False
    position = 0  # Position counter within the current file's diff
    current_new_line = 0  # Current line number in the new file

    for line in diff_text.splitlines():
        # Detect file header
        if line.startswith("diff --git"):
            # Check if this is our target file
            # Format: diff --git a/path b/path
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                file_path = parts[1]
                in_target_file = (
                    file_path == target_path
                    or file_path.endswith(f"/{target_path}")
                    or target_path.endswith(f"/{file_path}")
                )
                position = 0
            continue

        if not in_target_file:
            continue

        # Skip file metadata lines
        if line.startswith("---") or line.startswith("+++"):
            continue

        # Parse hunk header
        if line.startswith("@@"):
            position += 1
            # Extract new file start line: @@ -old,count +new,count @@
            hunk_match = re.search(r"\+(\d+)", line)
            if hunk_match:
                current_new_line = int(hunk_match.group(1))
            continue

        position += 1

        # Track line numbers in the new file
        if line.startswith("-"):
            # Deleted line — doesn't count in new file
            continue
        elif line.startswith("+"):
            # Added line
            if current_new_line == target_line:
                return position
            current_new_line += 1
        else:
            # Context line (space prefix)
            if current_new_line == target_line:
                return position
            current_new_line += 1

    return None


def build_review_comments(
    suggestions: list[Suggestion],
    diff_text: str,
) -> list[dict]:
    """Convert Suggestion objects into GitHub PR Review API comment format.

    Each comment includes a suggestion block that GitHub renders as a
    clickable "Apply suggestion" button.

    Args:
        suggestions: Parsed suggestion objects.
        diff_text: Full unified diff for position calculation.

    Returns:
        List of dicts ready for the PR Review API `comments` array.
    """
    comments: list[dict] = []

    for s in suggestions:
        position = calculate_diff_position(diff_text, s.path, s.line)
        if position is None:
            logger.debug(
                "Could not find position for %s:%d, skipping suggestion",
                s.path, s.line,
            )
            continue

        body = (
            f"{s.reason}\n\n"
            f"```suggestion\n"
            f"{s.suggested}\n"
            f"```"
        )

        comments.append({
            "path": s.path,
            "position": position,
            "body": body,
        })

    logger.info(
        "Built %d review comments from %d suggestions",
        len(comments), len(suggestions),
    )
    return comments
