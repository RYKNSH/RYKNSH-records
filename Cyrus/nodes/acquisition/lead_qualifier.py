"""lead_qualifier — 🟢 Acquisition Layer.

Automated lead qualification engine.
B2B: MQL/SQL classification. B2C: Activated User detection. C2C: Active Creator identification.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.base import CyrusNode
from engine.state import CyrusState

logger = logging.getLogger(__name__)


QUALIFICATION_CRITERIA = {
    "b2b": {
        "mql": [
            {"signal": "Downloaded gated content", "weight": 10},
            {"signal": "Visited pricing page", "weight": 15},
            {"signal": "Attended webinar", "weight": 10},
            {"signal": "Opened 3+ emails", "weight": 5},
        ],
        "sql": [
            {"signal": "Requested demo/meeting", "weight": 30},
            {"signal": "Budget confirmed", "weight": 25},
            {"signal": "Decision timeline < 90 days", "weight": 20},
            {"signal": "Champion identified", "weight": 15},
        ],
        "thresholds": {"mql": 25, "sql": 60},
    },
    "b2c": {
        "activated": [
            {"signal": "Completed onboarding", "weight": 20},
            {"signal": "Used core feature", "weight": 25},
            {"signal": "D1 return", "weight": 15},
            {"signal": "Invited friend", "weight": 20},
        ],
        "power_user": [
            {"signal": "D7 retention", "weight": 20},
            {"signal": "Used 3+ features", "weight": 15},
            {"signal": "Session > 10 min avg", "weight": 10},
        ],
        "thresholds": {"activated": 40, "power_user": 65},
    },
    "c2c": {
        "active_creator": [
            {"signal": "Published 3+ listings", "weight": 20},
            {"signal": "Received first transaction", "weight": 25},
            {"signal": "Profile completeness > 80%", "weight": 15},
            {"signal": "Response time < 2h", "weight": 10},
        ],
        "top_creator": [
            {"signal": "10+ completed transactions", "weight": 20},
            {"signal": "4.5+ avg rating", "weight": 15},
            {"signal": "Repeat customer rate > 30%", "weight": 15},
        ],
        "thresholds": {"active_creator": 35, "top_creator": 60},
    },
}


class LeadQualifier(CyrusNode):
    """Automated lead/user qualification across all business models."""

    name = "lead_qualifier"
    layer = "acquisition"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        business_model = blueprint.get("business_model", "b2b")

        criteria = QUALIFICATION_CRITERIA.get(business_model, QUALIFICATION_CRITERIA["b2b"])

        qualification = {
            "model": business_model,
            "criteria": criteria,
            "scoring_method": "weighted_signal_sum",
            "auto_actions": self._define_actions(business_model),
            "integration_points": {
                "trust_engine": "Feed qualification signals to trust score",
                "outbound_personalizer": "Adjust message level based on qualification",
                "campaign_orchestrator": "Route to appropriate campaign segment",
            },
        }
        return {"qualified_leads": [qualification]}

    @staticmethod
    def _define_actions(model: str) -> list[dict]:
        if model == "b2b":
            return [
                {"tier": "mql", "action": "Add to nurture sequence", "node": "nurture_sequencer"},
                {"tier": "sql", "action": "Generate proposal + set meeting", "node": "proposal_generator"},
                {"tier": "below_mql", "action": "Continue inbound magnet engagement", "node": "inbound_magnet"},
            ]
        elif model == "b2c":
            return [
                {"tier": "activated", "action": "Start retention loop", "node": "retention_looper"},
                {"tier": "power_user", "action": "Trigger monetization", "node": "monetization_trigger"},
                {"tier": "inactive", "action": "Re-engagement campaign", "node": "campaign_orchestrator"},
            ]
        else:  # c2c
            return [
                {"tier": "active_creator", "action": "Feature in marketplace", "node": "marketplace_growth_driver"},
                {"tier": "top_creator", "action": "Invite to ambassador program", "node": "community_seeder"},
                {"tier": "new_creator", "action": "Guided onboarding", "node": "onboarding_sequencer"},
            ]


lead_qualifier = LeadQualifier()
