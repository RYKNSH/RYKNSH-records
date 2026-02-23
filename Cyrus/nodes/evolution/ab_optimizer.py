"""ab_optimizer — 🔴 Evolution Layer Node #2.

Automated A/B testing with self-optimization.
Tests content, messaging, timing, and channel allocation.
Winners auto-adopted. Losers auto-terminated.
Triggers Intelligence Layer re-calculation for continuous learning.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.base import CyrusNode
from engine.state import CyrusState

logger = logging.getLogger(__name__)


class ABOptimizer(CyrusNode):
    """Automated A/B testing and self-optimization engine."""

    name = "ab_optimizer"
    layer = "evolution"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        performance = state.get("performance_metrics", {})
        business_model = blueprint.get("business_model", "b2b")

        # Generate test hypotheses from performance data
        tests = self._generate_tests(state, business_model)

        # Define optimization rules
        rules = self._define_rules(business_model)

        # Intelligence feedback loop
        feedback_loop = self._create_feedback_loop(performance)

        optimization_plan = {
            "active_tests": tests,
            "optimization_rules": rules,
            "feedback_loop": feedback_loop,
            "auto_adopt_threshold": {"confidence": 0.95, "min_sample_size": 100, "min_duration_hours": 48},
            "auto_terminate_threshold": {"max_loss_pct": -20, "patience_hours": 24},
        }

        return {"optimization_actions": [optimization_plan]}

    @staticmethod
    def _generate_tests(state: CyrusState, model: str) -> list[dict]:
        tests = []

        # Content A/B tests
        content_plan = state.get("content_plan", [])
        if content_plan:
            tests.append({
                "id": "test_content_hook",
                "type": "content",
                "variable": "hook_style",
                "variants": ["data_led", "story_led", "question_led"],
                "metric": "ctr",
                "status": "proposed",
            })

        # Outbound A/B tests
        if state.get("outbound_messages"):
            tests.append({
                "id": "test_outbound_subject",
                "type": "outbound",
                "variable": "email_subject_line",
                "variants": ["value_first", "curiosity", "social_proof"],
                "metric": "open_rate",
                "status": "proposed",
            })

        # Trust Engine A/B tests
        if state.get("trust_engine_output"):
            tests.append({
                "id": "test_value_first_type",
                "type": "trust",
                "variable": "value_first_action_type",
                "variants": ["report", "tool", "introduction"],
                "metric": "trust_score_delta",
                "status": "proposed",
            })

        # Model-specific tests
        if model == "b2b":
            tests.append({
                "id": "test_nurture_cadence",
                "type": "conversion",
                "variable": "nurture_email_frequency",
                "variants": ["every_3_days", "weekly", "biweekly"],
                "metric": "sql_conversion_rate",
                "status": "proposed",
            })
        elif model == "b2c":
            tests.append({
                "id": "test_monetization_timing",
                "type": "conversion",
                "variable": "upgrade_prompt_timing",
                "variants": ["day_7", "day_14", "usage_trigger"],
                "metric": "free_to_paid_rate",
                "status": "proposed",
            })
        else:  # c2c
            tests.append({
                "id": "test_onboarding_flow",
                "type": "conversion",
                "variable": "onboarding_steps",
                "variants": ["3_step_fast", "5_step_guided", "interactive_tour"],
                "metric": "activation_rate",
                "status": "proposed",
            })

        return tests

    @staticmethod
    def _define_rules(model: str) -> list[dict]:
        base_rules = [
            {"condition": "Variant wins with >95% confidence", "action": "Auto-adopt winner, terminate losers"},
            {"condition": "All variants within 5% of control", "action": "Keep control, test new hypothesis"},
            {"condition": "Variant loses by >20% for 24h", "action": "Auto-terminate variant"},
        ]

        model_rules = {
            "b2b": [{"condition": "CAC increases >30% during test", "action": "Pause test, revert to control"}],
            "b2c": [{"condition": "D1 retention drops >10%", "action": "Emergency rollback"}],
            "c2c": [{"condition": "Liquidity drops below 0.4", "action": "Pause supply-side tests"}],
        }

        return base_rules + model_rules.get(model, [])

    @staticmethod
    def _create_feedback_loop(performance: dict) -> dict:
        return {
            "trigger": "A/B test winner adopted",
            "actions": [
                "Update GrowthBlueprint with winning parameters",
                "Trigger Intelligence Layer re-scan with new data",
                "Recalculate ICP profiles with conversion data",
                "Update Trust Engine personality models",
            ],
            "frequency": "After each test conclusion",
            "health_score": performance.get("health_score", 0),
        }


ab_optimizer = ABOptimizer()
