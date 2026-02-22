"""Ada Core API — Validator Node.

Validates LLM output quality before delivering to the user.
Catches hallucinations, format errors, empty responses, and tone issues.

Runs after invoke_llm, before log_usage.
If validation fails and retry_count < max_retries, triggers re-execution.

WHITEPAPER ref: Section 3 — validator, Section Security — output scanning
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent.nodes.base import AdaNode

logger = logging.getLogger(__name__)

MAX_RETRIES = 1


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def check_empty_response(content: str) -> dict[str, Any] | None:
    """Detect empty or extremely short responses."""
    stripped = content.strip()
    if not stripped:
        return {"check": "empty_response", "passed": False, "reason": "Response is empty"}
    if len(stripped) < 5:
        return {"check": "empty_response", "passed": False, "reason": f"Response too short ({len(stripped)} chars)"}
    return None


def check_format(content: str, expected_format: str | None) -> dict[str, Any] | None:
    """Validate response format if a specific format was expected."""
    if not expected_format:
        return None

    if expected_format == "json":
        try:
            json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # Try extracting JSON from markdown code blocks
            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if json_match:
                try:
                    json.loads(json_match.group(1))
                    return None  # Found valid JSON in code block
                except (json.JSONDecodeError, ValueError):
                    pass
            return {
                "check": "format_json",
                "passed": False,
                "reason": "Expected JSON format but response is not valid JSON",
            }

    if expected_format == "list":
        # Check for list indicators (numbered or bulleted)
        list_pattern = r"(?m)(^[\s]*[-*•]|^[\s]*\d+[.)]\s)"
        if not re.search(list_pattern, content):
            return {
                "check": "format_list",
                "passed": False,
                "reason": "Expected list format but no list items found",
            }

    return None


def check_grounding(
    content: str,
    rag_context: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Check if response is grounded in the provided RAG context.

    Only validates when RAG context is available. Uses simple keyword
    overlap as a fast heuristic (LLM-based grounding check in M3+).
    """
    if not rag_context:
        return None  # No RAG context → skip grounding check

    # Extract keywords from RAG context
    context_text = " ".join(c.get("content", "") for c in rag_context).lower()
    context_words = set(re.findall(r"\b[a-z]{4,}\b", context_text))

    if not context_words:
        return None

    # Check keyword overlap with response
    response_words = set(re.findall(r"\b[a-z]{4,}\b", content.lower()))
    overlap = context_words & response_words
    overlap_ratio = len(overlap) / len(context_words) if context_words else 0

    if overlap_ratio < 0.05 and len(content) > 100:
        return {
            "check": "grounding",
            "passed": False,
            "reason": f"Low context grounding (overlap={overlap_ratio:.2%})",
            "overlap_ratio": overlap_ratio,
        }

    return None


def check_refusal_leak(content: str) -> dict[str, Any] | None:
    """Detect when the LLM leaks internal refusal patterns."""
    refusal_patterns = [
        r"(?i)as an ai (language )?model",
        r"(?i)i('m| am) not able to",
        r"(?i)i don'?t have (access|the ability)",
        r"(?i)my training data",
        r"(?i)i was (trained|designed) (to|by)",
    ]
    for pattern in refusal_patterns:
        if re.search(pattern, content):
            return {
                "check": "refusal_leak",
                "passed": False,
                "reason": "Response contains AI self-reference patterns",
            }
    return None


# ---------------------------------------------------------------------------
# ValidatorNode
# ---------------------------------------------------------------------------

class ValidatorNode(AdaNode):
    """Output quality validation node.

    Validates LLM output and determines if it should be delivered
    or re-generated.

    State updates:
        validation_passed (bool): Whether output passed all checks
        validation_reason (str): Reason for failure, or "passed"
        validation_score (float): 0.0 (failed) to 1.0 (perfect)
        retry_count (int): Incremented on retry
    """

    name = "validator"

    async def process(
        self,
        state: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Validate the LLM response quality."""
        content = state.get("response_content", "")
        rag_context = state.get("rag_context", [])
        retry_count = state.get("retry_count", 0)

        # Determine expected format from config
        expected_format = None
        if config and "configurable" in config:
            expected_format = config["configurable"].get("expected_format")

        # Run all validation checks
        failures: list[dict[str, Any]] = []

        empty_check = check_empty_response(content)
        if empty_check:
            failures.append(empty_check)

        format_check = check_format(content, expected_format)
        if format_check:
            failures.append(format_check)

        grounding_check = check_grounding(content, rag_context)
        if grounding_check:
            failures.append(grounding_check)

        refusal_check = check_refusal_leak(content)
        if refusal_check:
            failures.append(refusal_check)

        # Calculate validation score
        total_checks = 4  # empty + format + grounding + refusal
        passed_checks = total_checks - len(failures)
        validation_score = passed_checks / total_checks

        if failures:
            reason = failures[0]["reason"]
            logger.warning(
                "Validator FAILED — %s (score=%.2f, retry=%d/%d, checks=%s)",
                reason, validation_score, retry_count, MAX_RETRIES,
                [f["check"] for f in failures],
            )
            return {
                "validation_passed": False,
                "validation_reason": reason,
                "validation_score": validation_score,
                "retry_count": retry_count,
            }

        logger.info("Validator PASSED (score=%.2f)", validation_score)
        return {
            "validation_passed": True,
            "validation_reason": "passed",
            "validation_score": validation_score,
            "retry_count": retry_count,
        }


# Module-level singleton
validator_node = ValidatorNode()
