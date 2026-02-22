"""campaign_orchestrator — 🟢 Acquisition Layer.

Multi-channel campaign coordination engine.
Synchronizes content, outbound, inbound, and ads across channels.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


CAMPAIGN_PROMPT = """You are Cyrus Campaign Orchestrator — coordinates multi-channel growth campaigns.

## Content Plan
{content_plan}

## Outbound Messages
{outbound_messages}

## Inbound Magnets
{inbound_magnets}

## Blueprint
- Business Model: {business_model}
- Channels: {channels}

## Task
Design a coordinated campaign (respond in JSON):

{{
  "campaign": {{
    "name": "...",
    "objective": "...",
    "duration_days": 30,
    "channels": [
      {{
        "channel": "...",
        "role": "primary|support|retarget",
        "budget_pct": 0.0-1.0,
        "content_ids": ["..."],
        "schedule": "..."
      }}
    ],
    "sequence": [
      {{"day": 1, "action": "...", "channel": "...", "content": "..."}},
      {{"day": 3, "action": "...", "channel": "...", "content": "..."}}
    ],
    "success_metrics": {{
      "primary": {{"metric": "...", "target": "..."}},
      "secondary": [{{"metric": "...", "target": "..."}}]
    }},
    "abort_conditions": ["..."]
  }}
}}
"""


class CampaignOrchestrator(CyrusNode):
    """Coordinate multi-channel campaigns."""

    name = "campaign_orchestrator"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        acq_config = blueprint.get("acquisition_config", {})

        prompt = CAMPAIGN_PROMPT.format(
            content_plan=str(state.get("content_plan", []))[:1000],
            outbound_messages=str(state.get("outbound_messages", []))[:500],
            inbound_magnets=str(state.get("inbound_magnets", []))[:500],
            business_model=blueprint.get("business_model", "b2b"),
            channels=str(acq_config.get("channels", {}))[:300],
        )

        result = await self._call_ada(prompt)
        return {"campaign": result.get("campaign", {})}

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        if not settings.ada_api_url or not settings.ada_api_key:
            return self._mock_response()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ada_api_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.ada_api_key}", "Content-Type": "application/json"},
                json={"messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            )
            response.raise_for_status()
            import json
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)

    @staticmethod
    def _mock_response() -> dict[str, Any]:
        return {
            "campaign": {
                "name": "Q1 SaaS Growth Sprint",
                "objective": "Generate 50 SQLs from Series A-C SaaS companies",
                "duration_days": 30,
                "channels": [
                    {"channel": "linkedin", "role": "primary", "budget_pct": 0.4, "content_ids": ["blog_cac", "case_study"], "schedule": "3x/week"},
                    {"channel": "email", "role": "support", "budget_pct": 0.2, "content_ids": ["outbound_seq"], "schedule": "drip"},
                    {"channel": "google_ads", "role": "retarget", "budget_pct": 0.3, "content_ids": ["landing_page"], "schedule": "always_on"},
                    {"channel": "x", "role": "support", "budget_pct": 0.1, "content_ids": ["thought_leadership"], "schedule": "daily"},
                ],
                "sequence": [
                    {"day": 1, "action": "Launch blog + LinkedIn post", "channel": "linkedin", "content": "CAC benchmark article"},
                    {"day": 3, "action": "Outbound to engaged viewers", "channel": "email", "content": "Personalized outreach"},
                    {"day": 7, "action": "Case study retarget", "channel": "google_ads", "content": "Case study LP"},
                    {"day": 14, "action": "Value-first follow-up", "channel": "email", "content": "ROI calculator"},
                    {"day": 21, "action": "Meeting request for warm leads", "channel": "linkedin", "content": "Direct DM"},
                ],
                "success_metrics": {
                    "primary": {"metric": "SQLs generated", "target": "50"},
                    "secondary": [{"metric": "MQL→SQL rate", "target": "15%"}, {"metric": "Cost per SQL", "target": "¥15,000"}],
                },
                "abort_conditions": ["Cost per SQL > ¥50,000 for 7 consecutive days", "Zero SQLs after 14 days"],
            },
        }


campaign_orchestrator = CampaignOrchestrator()
