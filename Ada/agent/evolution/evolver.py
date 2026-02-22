"""Ada Core API — Evolver (Statistical Parameter Optimizer).

Analyzes accumulated feedback to automatically adjust:
1. Model selection preferences (success rate based)
2. Temperature settings (by task type)
3. RAG parameters (retrieval thresholds)
4. Quality tier thresholds

WHITEPAPER ref: Section 3 — Evolution Layer, evolver
"""

from __future__ import annotations

import logging
from typing import Any

from agent.evolution.tester import QualityTester, quality_tester
from agent.lifecycle.blueprint import AgentBlueprint, PriorityWeights

logger = logging.getLogger(__name__)


# Minimum records required before optimization
MIN_RECORDS_FOR_OPTIMIZATION = 10


class Evolver:
    """Statistical parameter optimizer.

    Uses feedback data to generate optimized blueprint parameters.
    Does not mutate existing blueprints — creates new versions.
    """

    def __init__(self, tester: QualityTester | None = None) -> None:
        self._tester = tester or quality_tester

    def should_evolve(self, tenant_id: str) -> bool:
        """Check if enough data exists to run optimization."""
        stats = self._tester.get_tenant_stats(tenant_id)
        return stats["count"] >= MIN_RECORDS_FOR_OPTIMIZATION

    def optimize_model_selection(self, tenant_id: str = "") -> dict[str, Any]:
        """Optimize model selection based on success rates.

        Returns recommended model preferences ordered by performance.
        """
        model_stats = self._tester.get_model_stats(tenant_id)
        if not model_stats:
            return {"recommended_model": "claude-sonnet-4-20250514", "model_ranking": []}

        # Rank by success rate, break ties by avg_score
        ranked = sorted(
            model_stats.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["avg_score"]),
            reverse=True,
        )

        return {
            "recommended_model": ranked[0][0],
            "model_ranking": [
                {"model": model, **stats} for model, stats in ranked
            ],
        }

    def optimize_temperature(self, tenant_id: str = "") -> dict[str, float]:
        """Suggest temperature adjustments based on feedback patterns.

        Higher retry rate → lower temperature (more deterministic)
        Higher overall score → maintain current temperature
        """
        stats = self._tester.get_tenant_stats(tenant_id)
        if stats["count"] == 0:
            return {"recommended_temperature": 0.7, "adjustment": 0.0}

        retry_rate = stats["retry_rate"]
        avg_score = stats["avg_score"]

        current_temp = 0.7
        adjustment = 0.0

        # High retry rate → lower temperature
        if retry_rate > 0.3:
            adjustment = -0.2
        elif retry_rate > 0.15:
            adjustment = -0.1

        # Low quality → lower temperature
        if avg_score < 0.5:
            adjustment -= 0.1

        # High quality → slightly increase (more creative)
        if avg_score > 0.85 and retry_rate < 0.1:
            adjustment += 0.05

        new_temp = max(0.1, min(1.0, current_temp + adjustment))
        return {
            "recommended_temperature": round(new_temp, 2),
            "adjustment": round(adjustment, 2),
        }

    def optimize_priority_weights(self, tenant_id: str = "") -> PriorityWeights:
        """Adjust priority weights based on feedback patterns.

        Low quality scores → increase quality weight
        High retry rate → increase efficiency weight
        High cost without quality → reduce cost tolerance
        """
        stats = self._tester.get_tenant_stats(tenant_id)
        if stats["count"] == 0:
            return PriorityWeights()

        avg_score = stats["avg_score"]
        retry_rate = stats["retry_rate"]

        # Start from defaults
        q, e, s, c = 0.4, 0.3, 0.2, 0.1

        # Low quality → boost quality weight
        if avg_score < 0.6:
            q += 0.1
            c -= 0.05
            s -= 0.05
        elif avg_score > 0.85:
            # Quality is good, can afford speed
            q -= 0.05
            s += 0.05

        # High retry rate → boost efficiency
        if retry_rate > 0.2:
            e += 0.1
            s -= 0.05
            c -= 0.05

        # Normalize to sum = 1.0
        total = q + e + s + c
        return PriorityWeights(
            quality=round(q / total, 3),
            efficiency=round(e / total, 3),
            speed=round(s / total, 3),
            cost=round(c / total, 3),
        )

    def evolve_blueprint(
        self,
        current: AgentBlueprint,
        tenant_id: str = "",
    ) -> AgentBlueprint:
        """Generate an evolved blueprint with optimized parameters.

        Does NOT persist — caller should use blueprint_store.save().
        """
        tid = tenant_id or current.tenant_id

        model_opt = self.optimize_model_selection(tid)
        temp_opt = self.optimize_temperature(tid)
        weight_opt = self.optimize_priority_weights(tid)

        evolved = AgentBlueprint(
            id=current.id,
            tenant_id=current.tenant_id,
            version=current.version,  # Will be incremented by store.save()
            name=current.name,
            persona=current.persona,
            system_prompt=current.system_prompt,
            priority_weights=weight_opt,
            allowed_models=current.allowed_models,
            default_model=model_opt["recommended_model"],
            temperature=temp_opt["recommended_temperature"],
            tools=current.tools,
            quality_tier=current.quality_tier,
            rag_enabled=current.rag_enabled,
            max_retries=current.max_retries,
            metadata={
                **current.metadata,
                "evolved_from_version": current.version,
                "evolution_reason": "statistical_optimization",
                "model_ranking": model_opt.get("model_ranking", []),
                "temp_adjustment": temp_opt["adjustment"],
            },
        )

        logger.info(
            "Blueprint evolved: %s model=%s→%s, temp=%.2f→%.2f",
            current.name,
            current.default_model, evolved.default_model,
            current.temperature, evolved.temperature,
        )

        return evolved

    def generate_report(self, tenant_id: str = "") -> dict[str, Any]:
        """Generate an evolution report with current stats and recommendations."""
        stats = self._tester.get_tenant_stats(tenant_id)
        model_opt = self.optimize_model_selection(tenant_id)
        temp_opt = self.optimize_temperature(tenant_id)
        weight_opt = self.optimize_priority_weights(tenant_id)

        return {
            "tenant_id": tenant_id,
            "feedback_count": stats["count"],
            "should_evolve": self.should_evolve(tenant_id),
            "current_stats": stats,
            "recommendations": {
                "model": model_opt,
                "temperature": temp_opt,
                "priority_weights": weight_opt.to_dict(),
            },
        }


# Module-level singleton
evolver = Evolver()
