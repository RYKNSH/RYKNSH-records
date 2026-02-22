"""Tests for GrowthBlueprint v3."""

from models.blueprint import (
    GrowthBlueprint,
    EntityConfig,
    TrustConfig,
    ConversionConfig,
    OutcomeConfig,
    b2b_saas_template,
    b2c_entertainment_template,
)
from models.entity import BusinessModel, DealComplexity


class TestGrowthBlueprint:
    def test_minimal_creation(self):
        bp = GrowthBlueprint(
            entity_config=EntityConfig(type="organization"),
        )
        assert bp.business_model == BusinessModel.B2B
        assert bp.deal_complexity == DealComplexity.STANDARD

    def test_b2b_blueprint(self):
        bp = GrowthBlueprint(
            business_model=BusinessModel.B2B,
            entity_config=EntityConfig(
                type="organization",
                industry="saas",
                size="mid",
            ),
            conversion_config=ConversionConfig(
                mode=BusinessModel.B2B,
                pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            ),
        )
        assert len(bp.conversion_config.pipeline) == 4

    def test_b2c_high_complexity(self):
        bp = GrowthBlueprint(
            business_model=BusinessModel.B2C,
            deal_complexity=DealComplexity.HIGH,
            entity_config=EntityConfig(type="individual", context="buyer"),
            conversion_config=ConversionConfig(
                mode=BusinessModel.B2C,
                deal_complexity=DealComplexity.HIGH,
                pipeline=["nurture_sequencer", "proposal_generator", "meeting_setter", "close_advisor"],
            ),
        )
        assert bp.deal_complexity == DealComplexity.HIGH

    def test_full_outcome_config(self):
        bp = GrowthBlueprint(
            entity_config=EntityConfig(type="organization"),
            pricing_model="full_outcome",
            outcome_config=OutcomeConfig(
                metric="closed_revenue",
                rate=0.25,
                min_contract_months=3,
                api_cost_cap_pct=0.05,
            ),
        )
        assert bp.outcome_config is not None
        assert bp.outcome_config.rate == 0.25
        assert bp.outcome_config.api_cost_cap_pct == 0.05

    def test_trust_config(self):
        bp = GrowthBlueprint(
            entity_config=EntityConfig(type="organization"),
            trust_config=TrustConfig(
                personalization_depth="l3_empathy",
                method="challenger_spin_consultative_meddic",
                value_first_actions=["industry_report", "roi_calculator"],
            ),
        )
        assert bp.trust_config.personalization_depth == "l3_empathy"
        assert len(bp.trust_config.value_first_actions) == 2


class TestBlueprintTemplates:
    def test_b2b_saas_template(self):
        bp = b2b_saas_template("test-tenant")
        assert bp.business_model == BusinessModel.B2B
        assert bp.tenant_id == "test-tenant"
        assert bp.entity_config.type == "organization"
        assert len(bp.conversion_config.pipeline) == 4

    def test_b2c_entertainment_template(self):
        bp = b2c_entertainment_template("test-tenant")
        assert bp.business_model == BusinessModel.B2C
        assert bp.entity_config.type == "individual"
        assert "tiktok" in bp.acquisition_config.channels

    def test_template_serialization(self):
        bp = b2b_saas_template("test-tenant")
        data = bp.model_dump()
        assert isinstance(data, dict)
        assert data["business_model"] == "b2b"
        # Round-trip
        bp2 = GrowthBlueprint(**data)
        assert bp2.business_model == bp.business_model
