"""Velie QA Agent — Diff Input Sanitizer.

Protects the review pipeline from prompt injection attacks
embedded in PR diff content.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Injection patterns — case-insensitive regex patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("instruction_override", re.compile(
        r"(?:ignore|forget|disregard|override)\s+(?:all\s+)?(?:previous|above|prior|earlier)\s+"
        r"(?:instructions?|prompts?|rules?|guidelines?|context)",
        re.IGNORECASE,
    )),
    ("role_hijack", re.compile(
        r"(?:you\s+are\s+now|act\s+as|pretend\s+(?:to\s+be|you(?:'re| are))|"
        r"switch\s+(?:to|into)\s+(?:a\s+)?(?:new\s+)?(?:role|mode|persona))",
        re.IGNORECASE,
    )),
    ("system_prompt_leak", re.compile(
        r"(?:(?:show|reveal|print|output|display|repeat)\s+(?:your\s+)?(?:system\s+)?prompt|"
        r"what\s+(?:is|are)\s+your\s+(?:system\s+)?(?:instructions?|rules?|prompt))",
        re.IGNORECASE,
    )),
    ("output_manipulation", re.compile(
        r"(?:respond\s+(?:only\s+)?with|your\s+(?:only\s+)?(?:response|output|answer)\s+"
        r"(?:should|must|will)\s+be|say\s+(?:only\s+)?[\"'])",
        re.IGNORECASE,
    )),
    ("review_manipulation", re.compile(
        r"(?:(?:always\s+)?(?:approve|lgtm|merge\s+immediately|skip\s+review|no\s+issues?\s+found)|"
        r"this\s+(?:code|pr|change)\s+is\s+(?:perfect|flawless|safe))",
        re.IGNORECASE,
    )),
]

# Boundary markers for diff isolation
DIFF_START_MARKER = "<DIFF_START>"
DIFF_END_MARKER = "<DIFF_END>"
SANITIZED_MARKER = "⚠️ [SANITIZED]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_injection_patterns(text: str) -> list[str]:
    """Detect prompt injection patterns in text.

    Returns a list of pattern names that were detected.
    """
    detected: list[str] = []
    for name, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(name)
    return detected


def sanitize_diff(diff: str) -> str:
    """Sanitize a PR diff to prevent prompt injection.

    - Detects and marks suspicious lines with a warning marker
    - Wraps the diff in boundary markers for context isolation
    - Does NOT delete content (preserves reviewability)

    Args:
        diff: Raw diff text from GitHub API.

    Returns:
        Sanitized diff wrapped in boundary markers.
    """
    if not diff:
        return f"{DIFF_START_MARKER}\n{DIFF_END_MARKER}"

    detected = detect_injection_patterns(diff)

    if detected:
        logger.warning(
            "Prompt injection patterns detected in diff: %s",
            ", ".join(detected),
        )

        # Mark suspicious lines (line-level granularity)
        sanitized_lines: list[str] = []
        for line in diff.splitlines():
            line_detections = detect_injection_patterns(line)
            if line_detections:
                sanitized_lines.append(f"{SANITIZED_MARKER} {line}")
            else:
                sanitized_lines.append(line)
        diff = "\n".join(sanitized_lines)

    return f"{DIFF_START_MARKER}\n{diff}\n{DIFF_END_MARKER}"
