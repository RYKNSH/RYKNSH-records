"""inbound_magnet — 🟢 Acquisition Layer.

Always-On lead magnet engine that creates "pull" through "push".
3 strategies:
1. Authority Building — Free reports, benchmarks, tools
2. Event-Driven Outreach — Funding, hiring, competitor news triggers
3. Community Presence — Slack/Discord/Reddit value-first participation
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


MAGNET_PROMPT = """You are Cyrus Inbound Magnet — the Always-On lead attraction engine.

Your job: Create content/actions that make targets come to US.
You never sell. You provide so much value that they WANT to learn more.

## Market Intelligence
{market_data}

## ICP Profile
{icp_profiles}

## Detected Signals
{detected_signals}

## Business Model: {business_model}

## Task
Design 3 inbound magnet actions (respond in JSON):

{{
  "magnets": [
    {{
      "strategy": "authority_building|event_driven|community_presence",
      "type": "report|benchmark|tool|webinar|newsletter|comment|oss_contribution|ugc_campaign",
      "title": "...",
      "description": "...",
      "target_audience": "...",
      "distribution_channel": "blog|linkedin|x|youtube|slack|discord|reddit|email",
      "content_outline": "...",
      "expected_leads": "...",
      "creation_effort": "low|medium|high",
      "evergreen": true|false
    }}
  ],
  "always_on_schedule": {{
    "daily": ["..."],
    "weekly": ["..."],
    "on_trigger": ["..."]
  }}
}}
"""


class InboundMagnet(CyrusNode):
    """Always-On inbound lead magnet engine.

    Continuously generates "pull" opportunities through strategic
    value provision. Connected to Evolution Layer feedback for
    auto-optimization of magnet effectiveness.
    """

    name = "inbound_magnet"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        market_data = state.get("market_data", {})
        icp_profiles = state.get("icp_profiles", [])
        detected_signals = state.get("detected_signals", [])

        prompt = MAGNET_PROMPT.format(
            market_data=str(market_data)[:1500],
            icp_profiles=str(icp_profiles)[:1000],
            detected_signals=str(detected_signals)[:1000],
            business_model=blueprint.get("business_model", "b2b"),
        )

        result = await self._call_ada(prompt)

        return {
            "inbound_magnets": result.get("magnets", []),
            "inbound_schedule": result.get("always_on_schedule", {}),
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
            "magnets": [
                {
                    "strategy": "authority_building",
                    "type": "report",
                    "title": "2026 SaaS Growth Benchmark Report",
                    "description": "Anonymous CAC/LTV/Churn benchmarks from 200+ SaaS companies",
                    "target_audience": "Growth-stage SaaS CTOs and CMOs",
                    "distribution_channel": "linkedin",
                    "content_outline": "1. CAC by stage 2. LTV:CAC ratios 3. Channel effectiveness 4. AI adoption rates",
                    "expected_leads": "50-100 per month",
                    "creation_effort": "medium",
                    "evergreen": False,
                },
                {
                    "strategy": "event_driven",
                    "type": "tool",
                    "title": "ROI Calculator: AI Growth Engine vs. Traditional Sales Team",
                    "description": "Interactive calculator showing cost savings with autonomous growth",
                    "target_audience": "CFOs and Revenue leaders",
                    "distribution_channel": "blog",
                    "content_outline": "Input: team size, CAC, avg deal size. Output: projected savings with Cyrus",
                    "expected_leads": "30-50 per month",
                    "creation_effort": "high",
                    "evergreen": True,
                },
                {
                    "strategy": "community_presence",
                    "type": "comment",
                    "title": "Daily value drops in r/saas and r/startups",
                    "description": "Answer growth questions with data-backed insights. Zero self-promotion.",
                    "target_audience": "SaaS founders in growth phase",
                    "distribution_channel": "reddit",
                    "content_outline": "Monitor top posts → provide actionable advice → link to free tools only when directly relevant",
                    "expected_leads": "10-20 per month",
                    "creation_effort": "low",
                    "evergreen": False,
                },
            ],
            "always_on_schedule": {
                "daily": ["Reddit/community monitoring + value drops"],
                "weekly": ["LinkedIn insight post", "Newsletter send"],
                "on_trigger": ["Funding detected → congrats + report", "Hiring surge → relevance outreach"],
            },
        }


inbound_magnet = InboundMagnet()
