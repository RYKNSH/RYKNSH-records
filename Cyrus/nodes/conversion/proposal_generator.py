"""proposal_generator — 🟡 Conversion Layer / B2B Pipeline Node #2.

AI-generated proposals and RFP responses.
Coordinates with Lumina for visual design.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


class ProposalGenerator(CyrusNode):
    """Generate customized proposals for B2B deals."""

    name = "proposal_generator"
    layer = "conversion"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        trust_output = state.get("trust_engine_output", {})
        blueprint = state.get("blueprint", {})
        market_data = state.get("market_data", {})

        personality = trust_output.get("personality_profile", {})
        content_format = personality.get("preferred_content_format", "data_heavy")

        proposal = {
            "proposal_id": f"prop-{blueprint.get('tenant_id', 'unknown')}",
            "sections": [
                {"name": "Executive Summary", "tone": content_format},
                {"name": "Problem Analysis", "data": market_data.get("competitive_landscape", {})},
                {"name": "Proposed Solution", "nodes_involved": blueprint.get("conversion_config", {}).get("pipeline", [])},
                {"name": "ROI Projection", "model": blueprint.get("pricing_model", "usage")},
                {"name": "Implementation Timeline", "weeks": 4},
                {"name": "Pricing", "pricing_model": blueprint.get("pricing_model", "usage"), "outcome_rate": blueprint.get("outcome_config", {}).get("rate", 0.25)},
            ],
            "personalization": {
                "format": content_format,
                "hot_buttons": personality.get("hot_buttons", []),
                "avoid": personality.get("avoid_topics", []),
            },
            "lumina_handoff": True,
            "status": "draft",
        }
        return {"proposal": proposal}


proposal_generator = ProposalGenerator()
