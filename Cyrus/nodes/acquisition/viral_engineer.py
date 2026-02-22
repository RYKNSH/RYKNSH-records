"""viral_engineer — 🟢 Acquisition Layer.

Designs viral hooks and UGC campaigns for organic amplification.
Analyzes trending formats and creates share-worthy content strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


VIRAL_PROMPT = """You are Cyrus Viral Engineer — designs share-worthy content and UGC campaigns.

## Market Trends
{market_trends}

## ICP Profile
{icp_profiles}

## Business Model: {business_model}

## Task
Design 3 viral content strategies (respond in JSON):

{{
  "viral_strategies": [
    {{
      "name": "...",
      "type": "ugc_challenge|meme_format|data_visualization|controversy|tool_product",
      "hook": "...",
      "mechanic": "...",
      "platform": "tiktok|x|youtube|instagram|reddit",
      "incentive": "...",
      "estimated_reach": "...",
      "virality_score": 0.0-1.0,
      "risk_level": "low|medium|high"
    }}
  ],
  "trend_signals": [
    {{"trend": "...", "platform": "...", "ride_strategy": "..."}}
  ]
}}
"""


class ViralEngineer(CyrusNode):
    """Design viral hooks and UGC campaigns."""

    name = "viral_engineer"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})

        prompt = VIRAL_PROMPT.format(
            market_trends=str(state.get("market_data", {}).get("market_trends", []))[:1000],
            icp_profiles=str(state.get("icp_profiles", []))[:800],
            business_model=blueprint.get("business_model", "b2b"),
        )

        result = await self._call_ada(prompt)
        return {
            "viral_strategies": result.get("viral_strategies", []),
            "trend_signals": result.get("trend_signals", []),
        }

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
            "viral_strategies": [
                {
                    "name": "AI vs Human Sales Challenge",
                    "type": "ugc_challenge",
                    "hook": "Can AI outsell your best salesperson? We'll prove it live.",
                    "mechanic": "Companies submit their product. Cyrus runs a 7-day campaign. Results posted publicly.",
                    "platform": "x",
                    "incentive": "Free 30-day Cyrus trial for participants",
                    "estimated_reach": "100K impressions",
                    "virality_score": 0.75,
                    "risk_level": "medium",
                },
                {
                    "name": "The $0 Sales Team Infographic",
                    "type": "data_visualization",
                    "hook": "What if your entire sales team cost $0 upfront?",
                    "mechanic": "Interactive infographic comparing traditional vs outcome-based growth costs",
                    "platform": "linkedin",
                    "incentive": "Shareable, embeddable, citable",
                    "estimated_reach": "50K impressions",
                    "virality_score": 0.6,
                    "risk_level": "low",
                },
                {
                    "name": "Growth Roast Thread",
                    "type": "controversy",
                    "hook": "Your marketing stack is lying to you. Here's the proof.",
                    "mechanic": "Weekly X thread exposing common growth myths with data",
                    "platform": "x",
                    "incentive": "Engagement-driven reach, quote-tweet bait",
                    "estimated_reach": "200K cumulative",
                    "virality_score": 0.8,
                    "risk_level": "medium",
                },
            ],
            "trend_signals": [
                {"trend": "#AIAutomation trending", "platform": "x", "ride_strategy": "Reply with case study data"},
                {"trend": "Anti-SaaS pricing backlash", "platform": "reddit", "ride_strategy": "Position outcome-based as alternative"},
            ],
        }


viral_engineer = ViralEngineer()
