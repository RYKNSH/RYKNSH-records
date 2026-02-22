"""signal_detector — 🔵 Intelligence Layer Node #3.

Detects purchase/engagement/participation signals from ICP profiles
and market data. Outputs prioritized signal list for Acquisition Layer.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


SIGNAL_PROMPT_TEMPLATE = """You are Cyrus, an autonomous growth engine's signal detection module.

Based on the market data and ICP profiles, identify actionable signals.

## Market Data
{market_data}

## ICP Profiles
{icp_profiles}

## Blueprint Context
- Business Model: {business_model}
- Entity Type: {entity_type}

## Task
Detect and prioritize signals (respond in JSON):

{{
  "signals": [
    {{
      "type": "...",
      "description": "...",
      "source": "...",
      "detection_method": "...",
      "confidence": 0.0-1.0,
      "priority": "critical/high/medium/low",
      "recommended_action": "..."
    }}
  ],
  "monitoring_config": {{
    "check_frequency": "...",
    "data_sources": ["..."],
    "alert_thresholds": {{}}
  }}
}}
"""


class SignalDetector(CyrusNode):
    """Detect purchase/engagement signals from market and ICP data.

    Adapts signal types based on business model:
    - B2B: Hiring, funding, tech stack changes, PR mentions
    - B2C: Social engagement, content consumption, purchase patterns
    - C2C: Content creation frequency, collaboration signals, community activity
    """

    name = "signal_detector"
    layer = "intelligence"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        entity_config = blueprint.get("entity_config", {})
        market_data = state.get("market_data", {})
        icp_profiles = state.get("icp_profiles", [])

        prompt = SIGNAL_PROMPT_TEMPLATE.format(
            market_data=str(market_data)[:2000],
            icp_profiles=str(icp_profiles)[:2000],
            business_model=blueprint.get("business_model", "b2b"),
            entity_type=entity_config.get("type", "organization"),
        )

        result = await self._call_ada(prompt)
        signals = result.get("signals", [])

        return {"detected_signals": signals}

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        """Call Ada Core API."""
        if not settings.ada_api_url or not settings.ada_api_key:
            logger.warning("Ada API not configured, returning mock signals")
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
        """Fallback mock signals for development."""
        return {
            "signals": [
                {
                    "type": "hiring_qa_engineer",
                    "description": "Company posting QA engineer roles — indicates quality pain",
                    "source": "linkedin",
                    "detection_method": "job_board_scan",
                    "confidence": 0.85,
                    "priority": "critical",
                    "recommended_action": "Trigger outbound_personalizer with QA-focused value prop",
                },
                {
                    "type": "ci_pipeline_complaints",
                    "description": "Engineers complaining about slow CI on social media",
                    "source": "x",
                    "detection_method": "social_listening",
                    "confidence": 0.7,
                    "priority": "high",
                    "recommended_action": "Send Velie CI benchmark report as value-first action",
                },
                {
                    "type": "recent_funding",
                    "description": "Series B announced — budget available for tooling",
                    "source": "crunchbase",
                    "detection_method": "funding_tracker",
                    "confidence": 0.95,
                    "priority": "critical",
                    "recommended_action": "Trigger inbound_magnet with congratulatory outreach + growth report",
                },
            ],
            "monitoring_config": {
                "check_frequency": "daily",
                "data_sources": ["linkedin", "x", "crunchbase", "github"],
                "alert_thresholds": {"confidence_min": 0.6, "priority_min": "medium"},
            },
        }


signal_detector = SignalDetector()
