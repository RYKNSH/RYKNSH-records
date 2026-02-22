"""content_architect — 🟢 Acquisition Layer.

Designs and generates high-conversion content assets.
Integrates PASTOR method for B2C, Challenger insights for B2B.
Coordinates with Lumina for creative production.

Content Types:
- SEO blog articles
- Landing pages
- Case studies
- Social media posts
- Email sequences
- Video scripts (Lumina handoff)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


CONTENT_PROMPT = """You are Cyrus Content Architect — designs high-conversion content.

## Blueprint Context
- Business Model: {business_model}
- Sales Method: {sales_method}

## ICP Profile
{icp_profiles}

## Market Intelligence
{market_data}

## Trust Engine Output
{trust_output}

## Task
Design a content plan with 3-5 assets (respond in JSON):

{{
  "content_plan": [
    {{
      "type": "blog|landing_page|case_study|social_post|email_sequence|video_script",
      "title": "...",
      "hook": "...",
      "framework": "pastor|challenger_insight|data_story|ugc_prompt",
      "target_stage": "awareness|consideration|decision|retention",
      "channel": "...",
      "outline": ["..."],
      "cta": "...",
      "seo_keywords": ["..."],
      "estimated_impact": "high|medium|low",
      "lumina_handoff": true|false
    }}
  ],
  "content_calendar": {{
    "weekly_cadence": {{...}},
    "pillar_topics": ["..."]
  }}
}}
"""


class ContentArchitect(CyrusNode):
    """Design and generate high-conversion content assets."""

    name = "content_architect"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        trust_config = blueprint.get("trust_config", {})

        prompt = CONTENT_PROMPT.format(
            business_model=blueprint.get("business_model", "b2b"),
            sales_method=trust_config.get("method", "consultative"),
            icp_profiles=str(state.get("icp_profiles", []))[:1000],
            market_data=str(state.get("market_data", {}))[:1000],
            trust_output=str(state.get("trust_engine_output", {}))[:500],
        )

        result = await self._call_ada(prompt)
        return {
            "content_plan": result.get("content_plan", []),
            "content_calendar": result.get("content_calendar", {}),
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
            "content_plan": [
                {
                    "type": "blog",
                    "title": "Why Your CAC Is 3x Higher Than It Should Be",
                    "hook": "We analyzed 200+ SaaS companies. Here's what the top 10% do differently.",
                    "framework": "challenger_insight",
                    "target_stage": "awareness",
                    "channel": "blog_seo",
                    "outline": ["The CAC crisis", "Benchmark data", "3 levers to fix", "Calculator CTA"],
                    "cta": "Download the full benchmark report",
                    "seo_keywords": ["saas cac benchmark", "reduce customer acquisition cost"],
                    "estimated_impact": "high",
                    "lumina_handoff": False,
                },
                {
                    "type": "case_study",
                    "title": "How [Client] Cut CAC by 60% with Autonomous Growth",
                    "hook": "From 12-person sales team to 0 humans in the loop.",
                    "framework": "data_story",
                    "target_stage": "consideration",
                    "channel": "linkedin",
                    "outline": ["Challenge", "Solution", "Results (with numbers)", "Key takeaway"],
                    "cta": "See if autonomous growth works for your industry",
                    "seo_keywords": ["ai sales automation case study"],
                    "estimated_impact": "high",
                    "lumina_handoff": True,
                },
                {
                    "type": "video_script",
                    "title": "60s Explainer: What Is Full Outcome Pricing?",
                    "hook": "What if your growth engine only charged when you make money?",
                    "framework": "pastor",
                    "target_stage": "decision",
                    "channel": "youtube_shorts",
                    "outline": ["Problem", "Amplify", "Story", "Offer", "Response"],
                    "cta": "Try Cyrus — pay nothing until you close",
                    "seo_keywords": [],
                    "estimated_impact": "medium",
                    "lumina_handoff": True,
                },
            ],
            "content_calendar": {
                "weekly_cadence": {"monday": "blog", "wednesday": "linkedin_post", "friday": "case_study_or_video"},
                "pillar_topics": ["AI growth automation", "CAC optimization", "Outcome-based pricing"],
            },
        }


content_architect = ContentArchitect()
