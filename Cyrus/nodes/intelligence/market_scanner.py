"""market_scanner — 🔵 Intelligence Layer Node #1.

Scans market trends, competitor landscape, and industry dynamics.
Outputs structured market intelligence for ICP profiling.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


SCAN_PROMPT_TEMPLATE = """You are Cyrus, an autonomous growth engine's market intelligence module.

Analyze the following market context and provide structured intelligence.

## Blueprint Context
- Business Model: {business_model}
- Industry: {industry}
- Target Entity Type: {entity_type}

## Task
Provide a comprehensive market scan with the following structure (respond in JSON):

{{
  "market_trends": [
    {{"trend": "...", "relevance": 0.0-1.0, "impact": "high/medium/low"}}
  ],
  "competitor_landscape": [
    {{"name": "...", "strength": "...", "weakness": "...", "threat_level": 0.0-1.0}}
  ],
  "opportunities": [
    {{"description": "...", "potential_value": "high/medium/low", "time_to_capitalize": "..."}}
  ],
  "tam_sam_som": {{
    "tam": {{"value": "...", "description": "..."}},
    "sam": {{"value": "...", "description": "..."}},
    "som": {{"value": "...", "description": "..."}}
  }},
  "key_signals_to_watch": [
    {{"signal": "...", "source": "...", "why": "..."}}
  ]
}}
"""


class MarketScanner(CyrusNode):
    """Scan market trends, competitors, and opportunities.

    Uses Ada Core API to analyze market dynamics based on the blueprint.
    """

    name = "market_scanner"
    layer = "intelligence"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        entity_config = blueprint.get("entity_config", {})

        prompt = SCAN_PROMPT_TEMPLATE.format(
            business_model=blueprint.get("business_model", "b2b"),
            industry=entity_config.get("industry", "general"),
            entity_type=entity_config.get("type", "organization"),
        )

        market_data = await self._call_ada(prompt)

        return {"market_data": market_data}

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        """Call Ada Core API for LLM inference."""
        if not settings.ada_api_url or not settings.ada_api_key:
            logger.warning("Ada API not configured, returning mock market data")
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
        """Fallback mock data for development without Ada API."""
        return {
            "market_trends": [
                {"trend": "AI-powered sales automation growing 40% YoY", "relevance": 0.9, "impact": "high"},
                {"trend": "Outcome-based pricing becoming standard", "relevance": 0.85, "impact": "high"},
            ],
            "competitor_landscape": [
                {"name": "Clay", "strength": "Data enrichment", "weakness": "No full-funnel", "threat_level": 0.6},
                {"name": "Apollo.io", "strength": "Contact database", "weakness": "Manual workflows", "threat_level": 0.5},
            ],
            "opportunities": [
                {"description": "Full-funnel outcome-based pricing gap", "potential_value": "high", "time_to_capitalize": "3-6 months"},
            ],
            "tam_sam_som": {
                "tam": {"value": "$50B", "description": "Global sales & marketing automation"},
                "sam": {"value": "$5B", "description": "AI-powered growth platforms"},
                "som": {"value": "$50M", "description": "Full-funnel autonomous engines"},
            },
            "key_signals_to_watch": [
                {"signal": "hiring_growth_marketer", "source": "linkedin", "why": "Indicates growth investment"},
            ],
        }


market_scanner = MarketScanner()
