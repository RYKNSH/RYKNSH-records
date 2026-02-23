"""nurture_sequencer — 🟡 Conversion Layer / B2B Pipeline Node #1.

Automated lead nurturing through multi-touch email/content sequences.
Adapts cadence and content based on Trust Score progression.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


NURTURE_PROMPT = """You are Cyrus Nurture Sequencer (B2B Pipeline).

Design a nurture sequence that warms leads from MQL to SQL.

## Lead Profile
{personality_profile}

## Trust Score: {trust_score}/100 (Stage: {trust_stage})

## Value-First Actions Already Taken
{value_first_actions}

## Sales Method: {sales_method}

## Task
Design a nurture sequence (respond in JSON):

{{
  "sequence": [
    {{
      "step": 1,
      "day": 0,
      "type": "email|linkedin_message|content_share|invitation",
      "subject": "...",
      "body_preview": "...",
      "goal": "...",
      "trust_score_threshold": 0,
      "exit_condition": "..."
    }}
  ],
  "total_duration_days": 30,
  "escalation_trigger": "...",
  "drop_off_action": "..."
}}
"""


class NurtureSequencer(CyrusNode):
    """B2B lead nurturing through automated sequences."""

    name = "nurture_sequencer"
    layer = "conversion"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        trust_output = state.get("trust_engine_output", {})
        blueprint = state.get("blueprint", {})
        trust_config = blueprint.get("trust_config", {})

        prompt = NURTURE_PROMPT.format(
            personality_profile=str(trust_output.get("personality_profile", {}))[:800],
            trust_score=trust_output.get("trust_score", 0),
            trust_stage=trust_output.get("trust_stage", "stranger"),
            value_first_actions=str(trust_output.get("value_first_actions", {}))[:500],
            sales_method=trust_config.get("method", "consultative"),
        )

        result = await self._call_ada(prompt)
        return {"nurture_sequence": result}

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        if not settings.ada_api_url or not settings.ada_api_key:
            return self._mock()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.ada_api_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.ada_api_key}", "Content-Type": "application/json"},
                json={"messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            )
            resp.raise_for_status()
            import json
            return json.loads(resp.json().get("choices", [{}])[0].get("message", {}).get("content", "{}"))

    @staticmethod
    def _mock() -> dict[str, Any]:
        return {
            "sequence": [
                {"step": 1, "day": 0, "type": "email", "subject": "Your CAC benchmark vs. industry", "body_preview": "Attached is the report...", "goal": "deliver_value", "trust_score_threshold": 0, "exit_condition": "reply"},
                {"step": 2, "day": 3, "type": "linkedin_message", "subject": "Quick thought on your CI pipeline", "body_preview": "Noticed your team is hiring...", "goal": "build_rapport", "trust_score_threshold": 20, "exit_condition": "engagement"},
                {"step": 3, "day": 7, "type": "content_share", "subject": "Case study: 60% CAC reduction", "body_preview": "Similar company to yours...", "goal": "social_proof", "trust_score_threshold": 35, "exit_condition": "click"},
                {"step": 4, "day": 14, "type": "invitation", "subject": "15-min growth audit?", "body_preview": "Based on our analysis...", "goal": "meeting_request", "trust_score_threshold": 50, "exit_condition": "accept"},
            ],
            "total_duration_days": 21,
            "escalation_trigger": "Trust score reaches 50 OR reply with buying intent",
            "drop_off_action": "Move to quarterly touch nurture cycle",
        }


nurture_sequencer = NurtureSequencer()
