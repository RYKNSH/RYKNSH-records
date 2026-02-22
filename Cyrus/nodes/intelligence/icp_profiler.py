"""icp_profiler — 🔵 Intelligence Layer Node #2.

Profiles the Ideal Customer/Consumer/Creator using Adapter Pattern.
Entity Type determines which profiling adapter is used.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


PROFILE_PROMPT_TEMPLATE = """You are Cyrus, an autonomous growth engine's ICP profiler.

Based on the market data and blueprint, create an Ideal {entity_label} Profile.

## Market Data
{market_data}

## Blueprint Context
- Business Model: {business_model}
- Entity Type: {entity_type}
- Entity Config: {entity_config}

## Task
Create a detailed ICP profile as JSON:

{{
  "icp_name": "...",
  "description": "...",
  "demographics": {{...}},
  "psychographics": {{...}},
  "pain_points": ["..."],
  "goals": ["..."],
  "preferred_channels": ["..."],
  "buying_signals": ["..."],
  "objections": ["..."],
  "ideal_approach": "...",
  "estimated_ltv": "...",
  "acquisition_difficulty": "low/medium/high"
}}
"""

ENTITY_LABELS = {
    "organization": "Customer (Organization)",
    "individual": "Consumer (Individual)",
    "creator": "Creator",
}


class ICPProfiler(CyrusNode):
    """Profile ideal targets using Adapter Pattern per Entity Type.

    Adapts profiling strategy based on whether the target is:
    - Organization (B2B): Firmographic + technographic data
    - Individual (B2C): Demographic + psychographic data
    - Creator (C2C): Domain expertise + audience data
    """

    name = "icp_profiler"
    layer = "intelligence"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        entity_config = blueprint.get("entity_config", {})
        entity_type = entity_config.get("type", "organization")
        market_data = state.get("market_data", {})

        entity_label = ENTITY_LABELS.get(entity_type, "Customer")

        prompt = PROFILE_PROMPT_TEMPLATE.format(
            entity_label=entity_label,
            market_data=str(market_data)[:2000],
            business_model=blueprint.get("business_model", "b2b"),
            entity_type=entity_type,
            entity_config=str(entity_config)[:1000],
        )

        profiles = await self._call_ada(prompt)

        return {"icp_profiles": [profiles] if isinstance(profiles, dict) else profiles}

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        """Call Ada Core API."""
        if not settings.ada_api_url or not settings.ada_api_key:
            logger.warning("Ada API not configured, returning mock ICP")
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
        """Fallback mock ICP for development."""
        return {
            "icp_name": "Growth-Stage SaaS CTO",
            "description": "CTO at Series A-B SaaS company struggling with developer velocity and QA",
            "demographics": {"role": "CTO/VP Eng", "company_size": "50-200", "funding": "Series A-B"},
            "psychographics": {"values": ["engineering excellence", "speed"], "communication_style": "direct"},
            "pain_points": ["Slow CI/CD pipeline", "No dedicated QA team", "Technical debt"],
            "goals": ["Ship faster", "Reduce bugs in production", "Scale engineering org"],
            "preferred_channels": ["LinkedIn", "GitHub", "Tech conferences"],
            "buying_signals": ["Hiring QA engineers", "Blog posts about testing", "CI pipeline complaints"],
            "objections": ["Budget constraints", "Build vs buy", "Integration concerns"],
            "ideal_approach": "challenger_spin_hybrid",
            "estimated_ltv": "¥2,000,000",
            "acquisition_difficulty": "medium",
        }


icp_profiler = ICPProfiler()
