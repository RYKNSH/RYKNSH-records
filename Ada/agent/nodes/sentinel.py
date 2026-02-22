"""Ada Core API — Sentinel Node.

The gatekeeper of the Execution Layer. Every request passes through
sentinel first. It detects and blocks:
1. Prompt Injection attacks (pattern match + LLM judgment)
2. Harmful content
3. Malformed inputs

Detection is two-tiered:
- Tier 1 (fast): Regex pattern matching for known injection patterns
- Tier 2 (deep): LLM-based judgment for ambiguous cases

WHITEPAPER ref: Section 3 (Execution Layer), Section Security (横断的)
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent.nodes.base import AdaNode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Injection Patterns (Tier 1 — fast regex scan)
# ---------------------------------------------------------------------------

# Each pattern has a name, regex, and severity (high/medium)
INJECTION_PATTERNS: list[dict[str, Any]] = [
    # Direct instruction override
    {
        "name": "instruction_override",
        "pattern": re.compile(
            r"(?i)(ignore|disregard|forget|override|bypass)\s+"
            r"(all\s+)?(previous|above|prior|earlier|your|system)\s+"
            r"(instructions?|prompts?|rules?|guidelines?|context)",
        ),
        "severity": "high",
    },
    # System prompt extraction
    {
        "name": "system_prompt_extraction",
        "pattern": re.compile(
            r"(?i)(show|reveal|display|print|output|repeat|echo|tell)\s+"
            r"(me\s+)?(your\s+)?(the\s+)?"
            r"(system\s*prompt|system\s*message|initial\s+instructions?"
            r"|hidden\s+instructions?|original\s+prompt)",
        ),
        "severity": "high",
    },
    # Role hijacking
    {
        "name": "role_hijack",
        "pattern": re.compile(
            r"(?i)(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you\s+are)"
            r"|from\s+now\s+on\s+you|new\s+persona|switch\s+to\s+role"
            r"|roleplay\s+as|simulate\s+being)",
        ),
        "severity": "high",
    },
    # Delimiter injection (fake system messages)
    {
        "name": "delimiter_injection",
        "pattern": re.compile(
            r"(?i)(```\s*system|<\s*system\s*>|<<\s*SYS\s*>>|\[INST\]"
            r"|\[SYSTEM\]|<\|im_start\|>system|### ?System)",
        ),
        "severity": "high",
    },
    # Jailbreak keywords
    {
        "name": "jailbreak_keyword",
        "pattern": re.compile(
            r"(?i)(DAN\s*mode|jailbreak|do\s+anything\s+now"
            r"|developer\s+mode|god\s+mode|unrestricted\s+mode"
            r"|no\s+restrictions|without\s+limitations)",
        ),
        "severity": "high",
    },
    # Encoded/obfuscated injection attempts
    {
        "name": "encoding_bypass",
        "pattern": re.compile(
            r"(?i)(base64|rot13|hex\s*encode|url\s*encode|decode\s+this"
            r"|translate\s+from\s+base64|eval\(|exec\()",
        ),
        "severity": "medium",
    },
    # Output manipulation
    {
        "name": "output_manipulation",
        "pattern": re.compile(
            r"(?i)(respond\s+only\s+with|your\s+response\s+must\s+start\s+with"
            r"|begin\s+your\s+response|do\s+not\s+include\s+any\s+other"
            r"|output\s+nothing\s+but|just\s+say\s+yes)",
        ),
        "severity": "medium",
    },
]


# ---------------------------------------------------------------------------
# Harmful Content Patterns
# ---------------------------------------------------------------------------

HARMFUL_PATTERNS: list[dict[str, Any]] = [
    {
        "name": "code_execution_request",
        "pattern": re.compile(
            r"(?i)(write\s+.{0,30}(malware|virus|ransomware|keylogger|exploit)"
            r"|create\s+.{0,30}(backdoor|rootkit|trojan))",
        ),
        "severity": "high",
    },
]


# ---------------------------------------------------------------------------
# SentinelNode
# ---------------------------------------------------------------------------

class SentinelNode(AdaNode):
    """Gatekeeper node: validates input safety before processing.

    Two-tiered detection:
    1. Fast regex scan for known patterns (< 1ms)
    2. LLM judgment for ambiguous cases (only when needed)

    State updates:
        sentinel_passed (bool): Whether the input passed safety checks
        sentinel_reason (str): Reason for block, or "passed"
        sentinel_risk_score (float): 0.0 (safe) to 1.0 (dangerous)
    """

    name = "sentinel"

    async def process(
        self,
        state: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Scan input messages for injection attacks and harmful content."""

        messages = state.get("messages", [])
        if not messages:
            return {
                "sentinel_passed": True,
                "sentinel_reason": "no_messages",
                "sentinel_risk_score": 0.0,
            }

        # Extract user messages for scanning
        user_texts = self._extract_user_texts(messages)
        if not user_texts:
            return {
                "sentinel_passed": True,
                "sentinel_reason": "no_user_messages",
                "sentinel_risk_score": 0.0,
            }

        combined_text = "\n".join(user_texts)

        # ---------------------------------------------------------------
        # Tier 1: Fast pattern scan
        # ---------------------------------------------------------------
        detections = self._scan_patterns(combined_text)

        high_severity = [d for d in detections if d["severity"] == "high"]
        medium_severity = [d for d in detections if d["severity"] == "medium"]

        # High severity → immediate block
        if high_severity:
            reason = f"blocked:{high_severity[0]['name']}"
            logger.warning(
                "Sentinel BLOCKED — %s (patterns: %s)",
                reason,
                [d["name"] for d in high_severity],
            )
            return {
                "sentinel_passed": False,
                "sentinel_reason": reason,
                "sentinel_risk_score": 1.0,
            }

        # Medium severity → flag but pass (LLM judgment will be added in future)
        if medium_severity:
            risk_score = min(0.3 + 0.1 * len(medium_severity), 0.7)
            logger.info(
                "Sentinel FLAGGED — medium risk (%.2f), patterns: %s",
                risk_score,
                [d["name"] for d in medium_severity],
            )
            return {
                "sentinel_passed": True,
                "sentinel_reason": f"flagged:{medium_severity[0]['name']}",
                "sentinel_risk_score": risk_score,
            }

        # Clean — no detections
        return {
            "sentinel_passed": True,
            "sentinel_reason": "passed",
            "sentinel_risk_score": 0.0,
        }

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _extract_user_texts(messages: list[dict[str, str]]) -> list[str]:
        """Extract text content from user messages."""
        texts: list[str] = []
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    texts.append(content)
        return texts

    @staticmethod
    def _scan_patterns(text: str) -> list[dict[str, Any]]:
        """Scan text against all injection and harmful content patterns."""
        detections: list[dict[str, Any]] = []

        for pattern_def in INJECTION_PATTERNS + HARMFUL_PATTERNS:
            if pattern_def["pattern"].search(text):
                detections.append({
                    "name": pattern_def["name"],
                    "severity": pattern_def["severity"],
                })

        return detections


# Module-level singleton for easy graph integration
sentinel_node = SentinelNode()
