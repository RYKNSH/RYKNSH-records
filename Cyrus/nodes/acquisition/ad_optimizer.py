"""ad_optimizer — 🟢 Acquisition Layer.

Autonomous paid advertising optimizer.
Manages budget allocation across Meta, Google, TikTok, X.
Self-optimizes based on performance data.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


AD_PROMPT = """You are Cyrus Ad Optimizer — autonomous paid advertising management.

## Campaign Context
{campaign}

## Content Available
{content_plan}

## Budget & Channels
{channels}

## Business Model: {business_model}

## Task
Design an ad optimization plan (respond in JSON):

{{
  "ad_plan": {{
    "total_budget": "...",
    "allocation": [
      {{
        "platform": "meta|google|tiktok|x|linkedin",
        "budget_pct": 0.0-1.0,
        "objective": "awareness|traffic|conversion|retargeting",
        "ad_format": "...",
        "targeting": {{...}},
        "bid_strategy": "...",
        "creative_brief": "..."
      }}
    ],
    "optimization_rules": [
      {{
        "condition": "...",
        "action": "...",
        "threshold": "..."
      }}
    ],
    "test_plan": [
      {{
        "variable": "...",
        "variants": ["..."],
        "success_metric": "..."
      }}
    ]
  }}
}}
"""


class AdOptimizer(CyrusNode):
    """Autonomous paid ad budget allocation and optimization."""

    name = "ad_optimizer"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        acq_config = blueprint.get("acquisition_config", {})

        prompt = AD_PROMPT.format(
            campaign=str(state.get("campaign", {}))[:1000],
            content_plan=str(state.get("content_plan", []))[:800],
            channels=str(acq_config.get("channels", {}))[:500],
            business_model=blueprint.get("business_model", "b2b"),
        )

        result = await self._call_ada(prompt)
        return {"ad_plan": result.get("ad_plan", {})}

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
            "ad_plan": {
                "total_budget": "¥500,000/month",
                "allocation": [
                    {
                        "platform": "linkedin",
                        "budget_pct": 0.35,
                        "objective": "conversion",
                        "ad_format": "sponsored_content",
                        "targeting": {"job_titles": ["CTO", "VP Engineering"], "company_size": "50-500", "industry": "SaaS"},
                        "bid_strategy": "target_cpa",
                        "creative_brief": "CAC benchmark data with clear CTA to download report",
                    },
                    {
                        "platform": "google",
                        "budget_pct": 0.30,
                        "objective": "traffic",
                        "ad_format": "search_ads",
                        "targeting": {"keywords": ["ai sales automation", "reduce cac saas", "growth automation"]},
                        "bid_strategy": "maximize_conversions",
                        "creative_brief": "Search intent matching with benefit-first headlines",
                    },
                    {
                        "platform": "meta",
                        "budget_pct": 0.20,
                        "objective": "retargeting",
                        "ad_format": "carousel",
                        "targeting": {"custom_audience": "website_visitors_30d", "lookalike": "top_20pct_customers"},
                        "bid_strategy": "lowest_cost",
                        "creative_brief": "Case study carousel with before/after metrics",
                    },
                    {
                        "platform": "x",
                        "budget_pct": 0.15,
                        "objective": "awareness",
                        "ad_format": "promoted_tweet",
                        "targeting": {"followers_of": ["@lemlist", "@apollo_io", "@clay_hq"]},
                        "bid_strategy": "maximum_reach",
                        "creative_brief": "Provocative stat + link to benchmark",
                    },
                ],
                "optimization_rules": [
                    {"condition": "CPA > 2x target for 3 days", "action": "Pause ad set, reallocate budget", "threshold": "¥30,000"},
                    {"condition": "CTR < 0.5% for 48 hours", "action": "Swap creative variant", "threshold": "0.5%"},
                    {"condition": "ROAS > 5x for 7 days", "action": "Scale budget +30%", "threshold": "5.0"},
                ],
                "test_plan": [
                    {"variable": "headline", "variants": ["Data-led", "Story-led", "Question-led"], "success_metric": "CTR"},
                    {"variable": "CTA", "variants": ["Get Report", "Calculate ROI", "Book Demo"], "success_metric": "conversion_rate"},
                ],
            },
        }


ad_optimizer = AdOptimizer()
