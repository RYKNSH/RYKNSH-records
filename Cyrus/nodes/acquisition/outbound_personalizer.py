"""outbound_personalizer — 🟢 Acquisition Layer.

Generates Deep Personalization L1-L3 outbound messages.
Connects to Trust Engine for personality-aware tone and timing.

L1 Surface: Name, company, role
L2 Context: Pain points, recent activity, interests
L3 Empathy: Values, beliefs — never mentioned directly, resonated naturally
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


OUTBOUND_PROMPT = """You are Cyrus Outbound Personalizer. Generate a highly personalized outreach message.

## Personalization Level: {personalization_level}
- L1 (Surface): Use name, company, role. Basic personalization.
- L2 (Context): Reference their recent activity, pain points, interests.
- L3 (Empathy): Resonate with their values naturally. NEVER mention profiling directly.

## Target Profile
{personality_profile}

## Value-First Action
{value_first_action}

## Timing Context
{timing_context}

## Sales Method: {sales_method}
- B2B: Challenger approach (lead with insight)
- B2C: PASTOR (Problem → Amplify → Story → Testimony → Offer → Response)

## Task
Generate a personalized outreach message (respond in JSON):

{{
  "subject": "...",
  "body": "...",
  "channel": "email|linkedin|dm",
  "personalization_level": "l1|l2|l3",
  "call_to_action": "...",
  "follow_up_trigger": "...",
  "tone_rationale": "Why this tone was chosen (internal, not sent to target)"
}}

CRITICAL:
1. If L3: NEVER say "I know your values are X". Instead, naturally use tone/examples that resonate.
2. Lead with VALUE, not with pitch.
3. Keep it under 150 words. Respect their time.
"""


class OutboundPersonalizer(CyrusNode):
    """Generate Deep Personalized outbound messages.

    Uses Trust Engine output (personality, value-first, timing) to craft
    messages that feel genuinely helpful, not salesy.
    """

    name = "outbound_personalizer"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        trust_output = state.get("trust_engine_output", {})
        trust_config = blueprint.get("trust_config", {})

        personalization_level = trust_config.get("personalization_depth", "l2_context")
        sales_method = trust_config.get("method", "consultative")

        personality = trust_output.get("personality_profile", {})
        value_first = trust_output.get("value_first_actions", {})
        timing = trust_output.get("timing_decision", {})

        # Only generate message if timing says we should reach out
        should_reach = timing.get("should_reach_out", True)
        if not should_reach:
            return {
                "outbound_messages": [],
                "outbound_status": "deferred",
                "defer_reason": timing.get("reason", "Timing not optimal"),
            }

        prompt = OUTBOUND_PROMPT.format(
            personalization_level=personalization_level,
            personality_profile=str(personality)[:1000],
            value_first_action=str(value_first)[:1000],
            timing_context=str(timing)[:500],
            sales_method=sales_method,
        )

        message = await self._call_ada(prompt)

        return {
            "outbound_messages": [message],
            "outbound_status": "generated",
        }

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        """Call Ada Core API."""
        if not settings.ada_api_url or not settings.ada_api_key:
            return self._mock_response()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ada_api_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.ada_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            import json
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)

    @staticmethod
    def _mock_response() -> dict[str, Any]:
        return {
            "subject": "Quick benchmark: where does your CAC stack up?",
            "body": (
                "Hi — I put together a benchmark report covering CAC by company stage "
                "across 200+ SaaS companies. Thought it might be useful as you scale.\n\n"
                "No pitch, just data. Happy to share if you're interested.\n\n"
                "Best"
            ),
            "channel": "email",
            "personalization_level": "l2",
            "call_to_action": "Reply 'yes' for the report",
            "follow_up_trigger": "no_reply_3_days",
            "tone_rationale": "Analytical profile detected. Lead with data, minimal words, zero hype.",
        }


outbound_personalizer = OutboundPersonalizer()
