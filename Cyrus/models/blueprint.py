"""GrowthBlueprint v3 — Unified growth strategy configuration.

The Blueprint is the output of the Intelligence Layer and the input
to Acquisition/Conversion Layers. It defines WHO to target, WHERE to
reach them, and HOW to convert them.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from models.entity import BusinessModel, DealComplexity


# ---------------------------------------------------------------------------
# Sub-configs
# ---------------------------------------------------------------------------

class EntityConfig(BaseModel):
    """Target entity configuration."""

    type: str = Field(..., description="organization | individual | creator")
    industry: str | None = None
    size: str | None = None
    context: str | None = None
    domain: str | None = None
    demographics: dict[str, Any] = Field(default_factory=dict)
    psychographics: dict[str, Any] = Field(default_factory=dict)
    signals: list[dict[str, Any]] = Field(default_factory=list)


class TrustConfig(BaseModel):
    """Trust Engine configuration."""

    personalization_depth: str = Field(
        default="l2_context",
        description="l1_surface | l2_context | l3_empathy",
    )
    method: str = Field(
        default="consultative",
        description="Sales methodology: challenger_spin_consultative_meddic | pastor | community",
    )
    value_first_actions: list[str] = Field(default_factory=list)


class AcquisitionConfig(BaseModel):
    """Acquisition Layer configuration."""

    channels: dict[str, float] = Field(default_factory=dict)
    outbound_volume: int = 0
    organic_to_paid_ratio: float = 0.5
    viral_config: dict[str, Any] = Field(default_factory=dict)
    seed_strategy: str | None = None


class ConversionConfig(BaseModel):
    """Conversion Layer configuration."""

    mode: BusinessModel = BusinessModel.B2B
    deal_complexity: DealComplexity = DealComplexity.STANDARD
    pipeline: list[str] = Field(default_factory=list)
    kpi: dict[str, Any] = Field(default_factory=dict)


class OutcomeConfig(BaseModel):
    """Full Outcome pricing configuration."""

    metric: str = "closed_revenue"
    rate: float = Field(default=0.25, ge=0.0, le=1.0)
    min_contract_months: int = 3
    api_cost_cap_pct: float = Field(default=0.05, description="API cost cap as % of revenue")


# ---------------------------------------------------------------------------
# GrowthBlueprint
# ---------------------------------------------------------------------------

class GrowthBlueprint(BaseModel):
    """Complete growth strategy blueprint for a tenant."""

    blueprint_id: str | None = None
    tenant_id: str | None = None
    name: str = ""
    business_model: BusinessModel = BusinessModel.B2B
    deal_complexity: DealComplexity = DealComplexity.STANDARD

    entity_config: EntityConfig
    trust_config: TrustConfig = Field(default_factory=TrustConfig)
    acquisition_config: AcquisitionConfig = Field(default_factory=AcquisitionConfig)
    conversion_config: ConversionConfig = Field(default_factory=ConversionConfig)

    pricing_model: str = "growth"
    outcome_config: OutcomeConfig | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_pipeline_consistency(self) -> GrowthBlueprint:
        """Ensure conversion pipeline matches business model."""
        b2b_nodes = {"nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"}
        b2c_nodes = {"activation_optimizer", "retention_looper", "monetization_trigger"}
        c2c_nodes = {"onboarding_sequencer", "trust_builder", "marketplace_growth_driver"}

        pipeline_set = set(self.conversion_config.pipeline)

        if self.conversion_config.mode == BusinessModel.B2B:
            if pipeline_set and not pipeline_set.issubset(b2b_nodes | b2c_nodes | c2c_nodes):
                pass  # Allow custom nodes
        elif self.conversion_config.mode == BusinessModel.B2C:
            # B2C with high deal_complexity can use B2B pipeline
            if self.deal_complexity == DealComplexity.HIGH:
                pass  # B2B pipeline is valid for high-complexity B2C
        return self


# ---------------------------------------------------------------------------
# Blueprint Templates
# ---------------------------------------------------------------------------

def b2b_saas_template(tenant_id: str) -> GrowthBlueprint:
    """Pre-built blueprint for B2B SaaS customer acquisition."""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="B2B SaaS Growth",
        business_model=BusinessModel.B2B,
        entity_config=EntityConfig(
            type="organization",
            industry="saas",
            size="mid",
            signals=[{"type": "hiring_engineer", "source": "linkedin", "confidence": 0.7}],
        ),
        trust_config=TrustConfig(
            personalization_depth="l3_empathy",
            method="challenger_spin_consultative_meddic",
            value_first_actions=["industry_report", "roi_calculator", "case_study"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"linkedin": 0.4, "github": 0.3, "techblog_seo": 0.2, "x": 0.1},
            outbound_volume=500,
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2B,
            pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            kpi={"mql_to_sql": 0.15, "sql_to_close": 0.25, "target_cac": 15000},
        ),
    )


def b2c_entertainment_template(tenant_id: str) -> GrowthBlueprint:
    """Pre-built blueprint for B2C fan acquisition."""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="B2C Entertainment Growth",
        business_model=BusinessModel.B2C,
        entity_config=EntityConfig(
            type="individual",
            context="fan",
            demographics={"age": "15-35", "regions": ["JP", "US", "KR"]},
            psychographics={"interests": ["hiphop", "indie", "vocaloid"]},
        ),
        trust_config=TrustConfig(
            personalization_depth="l2_context",
            method="pastor",
        ),
        acquisition_config=AcquisitionConfig(
            channels={"tiktok": 0.35, "youtube": 0.25, "instagram": 0.20, "x": 0.10, "spotify": 0.10},
            organic_to_paid_ratio=0.7,
            viral_config={"ugc_incentive": "fan_credit", "trend_riding": True},
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2C,
            pipeline=["activation_optimizer", "retention_looper", "monetization_trigger"],
            kpi={"d1_retention": 0.60, "d7_retention": 0.35, "d30_retention": 0.15},
        ),
    )
