"""performance_analyst — 🔴 Evolution Layer Node #1.

Unified KPI dashboard across all channels, pipelines, and business models.
Automatically tracks the right metrics based on entity type:
- B2B: CAC, LTV, Pipeline Velocity, SQL/MQL ratio
- B2C: DAU/MAU, Retention curves, ARPU, Conversion funnel
- C2C: Liquidity, GMV, Take rate, Supply/Demand ratio
"""

from __future__ import annotations

import logging
from typing import Any

from engine.base import CyrusNode
from engine.state import CyrusState

logger = logging.getLogger(__name__)


B2B_METRICS = {
    "acquisition": {
        "cac": {"label": "Customer Acquisition Cost", "target": "< ¥50,000", "unit": "¥"},
        "cpl": {"label": "Cost per Lead", "target": "< ¥5,000", "unit": "¥"},
        "mql_to_sql": {"label": "MQL→SQL Conversion", "target": "> 15%", "unit": "%"},
        "sql_to_close": {"label": "SQL→Close Rate", "target": "> 25%", "unit": "%"},
    },
    "revenue": {
        "ltv": {"label": "Lifetime Value", "target": "> ¥500,000", "unit": "¥"},
        "ltv_cac_ratio": {"label": "LTV:CAC Ratio", "target": "> 3.0", "unit": "x"},
        "mrr": {"label": "Monthly Recurring Revenue", "target": "growth > 10% MoM", "unit": "¥"},
        "arpc": {"label": "Average Revenue Per Customer", "target": "¥50,000/mo", "unit": "¥"},
    },
    "pipeline": {
        "velocity": {"label": "Pipeline Velocity", "target": "< 30 days", "unit": "days"},
        "win_rate": {"label": "Win Rate", "target": "> 30%", "unit": "%"},
        "deal_size_avg": {"label": "Average Deal Size", "target": "¥200,000", "unit": "¥"},
    },
}

B2C_METRICS = {
    "engagement": {
        "dau_mau": {"label": "DAU/MAU Ratio", "target": "> 25%", "unit": "%"},
        "session_duration": {"label": "Avg Session Duration", "target": "> 5 min", "unit": "min"},
        "d1_retention": {"label": "D1 Retention", "target": "> 60%", "unit": "%"},
        "d7_retention": {"label": "D7 Retention", "target": "> 30%", "unit": "%"},
        "d30_retention": {"label": "D30 Retention", "target": "> 15%", "unit": "%"},
    },
    "monetization": {
        "arpu": {"label": "ARPU", "target": "¥500/mo", "unit": "¥"},
        "free_to_paid": {"label": "Free→Paid CVR", "target": "> 6%", "unit": "%"},
        "churn_rate": {"label": "Monthly Churn", "target": "< 5%", "unit": "%"},
    },
}

C2C_METRICS = {
    "marketplace": {
        "liquidity": {"label": "Marketplace Liquidity", "target": "> 0.6", "unit": "ratio"},
        "gmv": {"label": "Gross Merchandise Value", "target": "¥10M/mo", "unit": "¥"},
        "take_rate": {"label": "Take Rate", "target": "10-15%", "unit": "%"},
        "supply_demand_ratio": {"label": "Supply/Demand", "target": "1.2-1.5", "unit": "ratio"},
    },
    "engagement": {
        "time_to_first_match": {"label": "Time to First Match", "target": "< 24h", "unit": "hours"},
        "repeat_transaction_rate": {"label": "Repeat Rate", "target": "> 40%", "unit": "%"},
        "nps": {"label": "Net Promoter Score", "target": "> 50", "unit": "score"},
    },
}


class PerformanceAnalyst(CyrusNode):
    """Unified cross-channel performance analytics."""

    name = "performance_analyst"
    layer = "evolution"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        business_model = blueprint.get("business_model", "b2b")

        # Select metrics framework based on business model
        metrics_framework = self._get_metrics_framework(business_model)

        # Collect pipeline-specific results
        pipeline_summary = self._summarize_pipeline(state, business_model)

        # Channel performance (from campaign + ad data)
        channel_performance = self._analyze_channels(state)

        # Trust Engine effectiveness
        trust_effectiveness = self._analyze_trust(state)

        analysis = {
            "business_model": business_model,
            "metrics_framework": metrics_framework,
            "pipeline_summary": pipeline_summary,
            "channel_performance": channel_performance,
            "trust_effectiveness": trust_effectiveness,
            "recommendations": self._generate_recommendations(business_model, pipeline_summary),
            "health_score": self._calculate_health_score(pipeline_summary),
        }

        return {"performance_metrics": analysis}

    @staticmethod
    def _get_metrics_framework(model: str) -> dict:
        frameworks = {"b2b": B2B_METRICS, "b2c": B2C_METRICS, "c2c": C2C_METRICS}
        return frameworks.get(model, B2B_METRICS)

    @staticmethod
    def _summarize_pipeline(state: CyrusState, model: str) -> dict:
        if model == "b2b":
            return {
                "nurture_active": bool(state.get("nurture_sequence")),
                "proposals_generated": bool(state.get("proposal")),
                "meetings_set": bool(state.get("meeting")),
                "close_readiness": state.get("close_strategy", {}).get("readiness", "unknown"),
            }
        elif model == "b2c":
            return {
                "activation_designed": bool(state.get("activation")),
                "retention_plan_active": bool(state.get("retention_plan")),
                "monetization_triggers_set": bool(state.get("monetization")),
            }
        else:  # c2c
            return {
                "onboarding_designed": bool(state.get("onboarding")),
                "trust_system_active": bool(state.get("trust_building")),
                "marketplace_strategy_set": bool(state.get("marketplace_strategy")),
            }

    @staticmethod
    def _analyze_channels(state: CyrusState) -> dict:
        campaign = state.get("campaign", {})
        ad_plan = state.get("ad_plan", {})
        return {
            "campaign_active": bool(campaign),
            "ad_channels": len(ad_plan.get("allocation", [])),
            "content_pieces": len(state.get("content_plan", [])),
            "viral_strategies": len(state.get("viral_strategies", [])),
            "outbound_status": state.get("outbound_status", "unknown"),
            "inbound_magnets_count": len(state.get("inbound_magnets", [])),
        }

    @staticmethod
    def _analyze_trust(state: CyrusState) -> dict:
        trust = state.get("trust_scores", {})
        return {
            "current_score": trust.get("overall", 0),
            "stage": trust.get("stage", "stranger"),
            "trust_engine_active": bool(state.get("trust_engine_output")),
        }

    @staticmethod
    def _generate_recommendations(model: str, pipeline: dict) -> list[str]:
        recs = []
        if model == "b2b":
            if pipeline.get("close_readiness") == "not_ready":
                recs.append("Increase value-first content delivery to warm leads")
            if not pipeline.get("proposals_generated"):
                recs.append("Generate personalized proposals for qualified leads")
        elif model == "b2c":
            if not pipeline.get("activation_designed"):
                recs.append("Design activation flow with clear Aha Moment")
        else:
            if not pipeline.get("trust_system_active"):
                recs.append("Activate trust building system with verification layers")
        return recs or ["All systems operational. Monitor KPIs for optimization opportunities."]

    @staticmethod
    def _calculate_health_score(pipeline: dict) -> float:
        active_count = sum(1 for v in pipeline.values() if v and v is not True and v != "unknown")
        true_count = sum(1 for v in pipeline.values() if v is True)
        total = len(pipeline)
        return round((active_count + true_count) / total * 100, 1) if total > 0 else 0.0


performance_analyst = PerformanceAnalyst()
