"""activation_optimizer — 🟡 Conversion Layer / B2C Pipeline Node #1.

Optimizes first-time user experience to reach the "Aha Moment".
Designs personalized onboarding flows based on user context.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.base import CyrusNode
from engine.state import CyrusState

logger = logging.getLogger(__name__)


AHA_MOMENTS = {
    "saas": "First successful workflow completion",
    "ec": "First purchase with satisfaction",
    "entertainment": "First content consumed to completion",
    "education": "First lesson completed with quiz passed",
    "healthcare": "First appointment booked",
    "finance": "First investment or transfer completed",
}


class ActivationOptimizer(CyrusNode):
    """Optimize B2C user activation and Aha Moment delivery."""

    name = "activation_optimizer"
    layer = "conversion"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        entity_config = blueprint.get("entity_config", {})
        industry = entity_config.get("industry", "saas")
        context = entity_config.get("context", "buyer")

        aha_moment = AHA_MOMENTS.get(industry, AHA_MOMENTS["saas"])

        activation = {
            "aha_moment": aha_moment,
            "onboarding_flow": [
                {"step": 1, "action": "Welcome + value proposition", "channel": "in_app", "time": "T+0"},
                {"step": 2, "action": "Guided first action", "channel": "in_app", "time": "T+2min"},
                {"step": 3, "action": "Aha moment delivery", "channel": "in_app", "time": "T+5min"},
                {"step": 4, "action": "Social proof nudge", "channel": "push", "time": "T+1h"},
                {"step": 5, "action": "D1 re-engagement", "channel": "email", "time": "T+24h"},
            ],
            "personalization": {
                "context": context,
                "industry": industry,
                "preferred_learning_style": "interactive",
            },
            "metrics": {
                "target_activation_rate": 0.40,
                "target_time_to_aha": "5 min",
                "target_d1_retention": 0.60,
            },
        }
        return {"activation": activation}


activation_optimizer = ActivationOptimizer()
