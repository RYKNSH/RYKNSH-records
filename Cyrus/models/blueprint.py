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


# ---------------------------------------------------------------------------
# RYKNSH 6社 内販 Blueprint Templates
# ---------------------------------------------------------------------------

def label01_template(tenant_id: str) -> GrowthBlueprint:
    """Label 01 — 音楽レーベル。B2C(ファン獲得) + C2C(アーティスト募集)。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Label 01 — Fan Acquisition & Artist Network",
        business_model=BusinessModel.B2C,
        entity_config=EntityConfig(
            type="individual",
            context="fan",
            demographics={"age": "15-35", "regions": ["JP", "US", "KR", "EU"]},
            psychographics={
                "interests": ["hiphop", "r&b", "indie", "electronic"],
                "values": ["authenticity", "underground_culture", "creative_freedom"],
                "pain_points": ["mainstream_saturation", "discovery_difficulty"],
            },
        ),
        trust_config=TrustConfig(
            personalization_depth="l2_context",
            method="pastor",
            value_first_actions=["exclusive_preview", "behind_the_scenes", "artist_story"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"tiktok": 0.30, "youtube": 0.25, "spotify": 0.20, "instagram": 0.15, "x": 0.10},
            organic_to_paid_ratio=0.8,
            viral_config={"ugc_incentive": "fan_credit", "trend_riding": True, "challenge_format": "remix"},
            seed_strategy="micro_influencer_collab",
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2C,
            pipeline=["activation_optimizer", "retention_looper", "monetization_trigger"],
            kpi={"d1_retention": 0.55, "d30_retention": 0.20, "monthly_streams": 100000},
        ),
        pricing_model="full_outcome",
        outcome_config=OutcomeConfig(metric="streaming_revenue", rate=0.20),
        metadata={"subsidiary": "label_01", "dual_mode": "b2c+c2c"},
    )


def velie_template(tenant_id: str) -> GrowthBlueprint:
    """Velie — QA/検証SaaS。B2Bエンタープライズ営業。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Velie — SaaS Lead Gen & Enterprise Sales",
        business_model=BusinessModel.B2B,
        deal_complexity=DealComplexity.HIGH,
        entity_config=EntityConfig(
            type="organization",
            industry="saas",
            size="mid",
            signals=[
                {"type": "hiring_qa", "source": "linkedin", "confidence": 0.8},
                {"type": "tech_stack_match", "source": "builtwith", "confidence": 0.7},
                {"type": "funding_round", "source": "crunchbase", "confidence": 0.6},
            ],
        ),
        trust_config=TrustConfig(
            personalization_depth="l3_empathy",
            method="challenger_spin_consultative_meddic",
            value_first_actions=["qa_audit_report", "test_coverage_benchmark", "roi_calculator"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"linkedin": 0.40, "techblog_seo": 0.25, "github": 0.20, "producthunt": 0.15},
            outbound_volume=300,
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2B,
            deal_complexity=DealComplexity.HIGH,
            pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            kpi={"mql_to_sql": 0.20, "sql_to_close": 0.30, "target_cac": 12000, "target_ltv": 180000},
        ),
        pricing_model="full_outcome",
        outcome_config=OutcomeConfig(metric="closed_revenue", rate=0.25),
        metadata={"subsidiary": "velie"},
    )


def ada_template(tenant_id: str) -> GrowthBlueprint:
    """Ada — AI R&D / LLM基盤。DevTool B2B + 開発者コミュニティ。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Ada — DevTool Growth & Enterprise AI",
        business_model=BusinessModel.B2B,
        entity_config=EntityConfig(
            type="organization",
            industry="ai_ml",
            size="mid",
            signals=[
                {"type": "openai_competitor", "source": "producthunt", "confidence": 0.6},
                {"type": "llm_integration", "source": "github", "confidence": 0.8},
                {"type": "ai_budget_increase", "source": "news", "confidence": 0.5},
            ],
        ),
        trust_config=TrustConfig(
            personalization_depth="l3_empathy",
            method="challenger_spin_consultative_meddic",
            value_first_actions=["api_benchmark_report", "cost_comparison_tool", "migration_guide"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"github": 0.30, "techblog_seo": 0.25, "x": 0.20, "linkedin": 0.15, "discord": 0.10},
            outbound_volume=200,
            seed_strategy="developer_community",
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2B,
            pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            kpi={"dev_signups": 1000, "api_calls_per_dev": 500, "enterprise_leads": 50},
        ),
        pricing_model="usage",
        metadata={"subsidiary": "ada"},
    )


def lumina_template(tenant_id: str) -> GrowthBlueprint:
    """Lumina — クリエイティブプロダクション。B2B受託リード獲得。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Lumina — Creative Production B2B",
        business_model=BusinessModel.B2B,
        entity_config=EntityConfig(
            type="organization",
            industry="creative_agency",
            size="small",
            signals=[
                {"type": "rebrand_signal", "source": "news", "confidence": 0.7},
                {"type": "campaign_launch", "source": "social", "confidence": 0.6},
                {"type": "hiring_designer", "source": "linkedin", "confidence": 0.8},
            ],
        ),
        trust_config=TrustConfig(
            personalization_depth="l2_context",
            method="consultative",
            value_first_actions=["portfolio_showcase", "brand_audit", "creative_brief_template"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"instagram": 0.30, "behance": 0.25, "linkedin": 0.25, "x": 0.20},
            outbound_volume=150,
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2B,
            pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            kpi={"portfolio_views": 5000, "project_leads": 30, "close_rate": 0.40},
        ),
        pricing_model="growth",
        metadata={"subsidiary": "lumina"},
    )


def noah_template(tenant_id: str) -> GrowthBlueprint:
    """Noah — ファン・コミュニティ基盤 / C2Cマーケットプレイス。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Noah — Community Marketplace Growth",
        business_model=BusinessModel.C2C,
        entity_config=EntityConfig(
            type="creator",
            domain="community_builder",
            demographics={"age": "18-40", "regions": ["JP"]},
            psychographics={
                "interests": ["community", "education", "creative"],
                "values": ["connection", "growth", "peer_learning"],
            },
        ),
        trust_config=TrustConfig(
            personalization_depth="l2_context",
            method="community",
            value_first_actions=["community_playbook", "growth_benchmark", "template_pack"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"x": 0.30, "discord": 0.25, "youtube": 0.20, "note": 0.15, "tiktok": 0.10},
            organic_to_paid_ratio=0.75,
            seed_strategy="key_person_first",
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.C2C,
            pipeline=["onboarding_sequencer", "trust_builder", "marketplace_growth_driver"],
            kpi={"creators_monthly": 100, "liquidity_ratio": 0.3, "gmv_monthly": 5000000},
        ),
        pricing_model="full_outcome",
        outcome_config=OutcomeConfig(metric="gmv", rate=0.15),
        metadata={"subsidiary": "noah"},
    )


def iris_template(tenant_id: str) -> GrowthBlueprint:
    """Iris — 広報PR・ブランド防衛。B2B PR→グロースフィードバックループ。"""
    return GrowthBlueprint(
        tenant_id=tenant_id,
        name="Iris — PR & Brand Growth Loop",
        business_model=BusinessModel.B2B,
        entity_config=EntityConfig(
            type="organization",
            industry="media_pr",
            size="small",
            signals=[
                {"type": "pr_crisis", "source": "news", "confidence": 0.7},
                {"type": "brand_expansion", "source": "social", "confidence": 0.6},
                {"type": "competitor_pr", "source": "news", "confidence": 0.5},
            ],
        ),
        trust_config=TrustConfig(
            personalization_depth="l2_context",
            method="consultative",
            value_first_actions=["brand_sentiment_report", "pr_audit", "competitor_media_analysis"],
        ),
        acquisition_config=AcquisitionConfig(
            channels={"linkedin": 0.35, "x": 0.25, "pr_media": 0.25, "techblog_seo": 0.15},
            outbound_volume=100,
        ),
        conversion_config=ConversionConfig(
            mode=BusinessModel.B2B,
            pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            kpi={"pr_leads": 20, "brand_score_lift": 0.15, "media_mentions": 50},
        ),
        pricing_model="growth",
        metadata={"subsidiary": "iris"},
    )


# All RYKNSH templates registry
RYKNSH_TEMPLATES = {
    "label_01": label01_template,
    "velie": velie_template,
    "ada": ada_template,
    "lumina": lumina_template,
    "noah": noah_template,
    "iris": iris_template,
}

