"""close_advisor — 🟡 Conversion Layer / B2B Pipeline Node #4.

AI-powered closing assistance. Analyzes deal signals,
suggests closing tactics, and tracks deal progression.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.base import CyrusNode
from engine.state import CyrusState

logger = logging.getLogger(__name__)


CLOSING_TACTICS = {
    "analytical": ["ROI-focused close", "data comparison close", "logical next-step close"],
    "driver": ["urgency close", "exclusive offer close", "direct ask"],
    "amiable": ["relationship close", "consensus close", "trial close"],
    "expressive": ["vision close", "story-driven close", "enthusiastic close"],
}


class CloseAdvisor(CyrusNode):
    """Provide AI-powered deal closing assistance."""

    name = "close_advisor"
    layer = "conversion"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        trust_output = state.get("trust_engine_output", {})
        personality = trust_output.get("personality_profile", {})
        trust_score = trust_output.get("trust_score", 0)
        blueprint = state.get("blueprint", {})

        comm_style = personality.get("communication_style", "analytical")
        tactics = CLOSING_TACTICS.get(comm_style, CLOSING_TACTICS["analytical"])

        close_readiness = "not_ready"
        if trust_score >= 75:
            close_readiness = "ready"
        elif trust_score >= 50:
            close_readiness = "warm"
        elif trust_score >= 25:
            close_readiness = "nurturing"

        pricing_model = blueprint.get("pricing_model", "usage")
        close_strategy = {
            "readiness": close_readiness,
            "trust_score": trust_score,
            "recommended_tactics": tactics[:2],
            "objection_handlers": [
                {"objection": "Price too high", "response": f"Our {pricing_model} model means you only pay for results"},
                {"objection": "Need to think about it", "response": "Completely understand. Would a 14-day pilot help your decision?"},
                {"objection": "Competitor comparison", "response": "Happy to do a head-to-head. Our Full Outcome pricing means zero risk to compare."},
            ],
            "next_action": self._determine_next_action(close_readiness),
            "deal_score": min(trust_score * 1.2, 100),
        }
        return {"close_strategy": close_strategy}

    @staticmethod
    def _determine_next_action(readiness: str) -> str:
        actions = {
            "ready": "Send contract with Full Outcome terms",
            "warm": "Schedule decision-maker meeting",
            "nurturing": "Send additional case study + ROI calculator",
            "not_ready": "Continue nurture sequence, increase value delivery",
        }
        return actions.get(readiness, actions["not_ready"])


close_advisor = CloseAdvisor()
