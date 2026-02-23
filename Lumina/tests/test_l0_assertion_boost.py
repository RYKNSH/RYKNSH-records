"""L0 強化: Assertion Density Booster

既存テストに不足しているアサーションを追加。
- 型検証
- 境界値検証
- 状態遷移の完全性検証
"""

import pytest

from src.models.state import (
    AssetType,
    BriefParams,
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
    TasteScore,
)
from src.models.blueprint import BusinessModel, CreativeBlueprint
from src.registry.client import ModelRegistryClient, RegisteredModel
from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.graph.nodes.creation.generator import generator
from src.graph.nodes.quality.taste_engine import taste_engine, DEFAULT_CRITIC_WEIGHTS, MASTERPIECE_CRITIC_WEIGHTS
from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
from src.graph.nodes.quality.ai_escalation_chain import ai_escalation_chain
from src.graph.nodes.delivery.delivery_nodes import format_optimizer, asset_packager
from src.marketplace.style_packs import StylePack, StylePackMarketplace


# ==================== State Model 型検証 ====================

class TestStateModelIntegrity:
    """LuminaState の型・デフォルト値・境界値を徹底検証"""

    def test_default_state_values(self):
        state = LuminaState(brief="test")
        assert state.brief == "test"
        assert state.status == GenerationStatus.PENDING
        assert state.quality_tier == QualityTier.STANDARD
        assert state.retry_count == 0
        assert state.max_retries == 3
        assert state.quality_threshold == 75.0
        assert state.escalation_step == 0
        assert state.generated_asset_url == ""
        assert state.deliverable_url == ""
        assert state.tenant_id == ""
        assert state.brief_params is None
        assert state.model_selection is None
        assert state.taste_score is None

    def test_quality_tier_enum_values(self):
        assert QualityTier.PREVIEW.value == "preview"
        assert QualityTier.STANDARD.value == "standard"
        assert QualityTier.PREMIUM.value == "premium"
        assert QualityTier.MASTERPIECE.value == "masterpiece"
        assert len(QualityTier) == 4

    def test_generation_status_enum_completeness(self):
        statuses = [s.value for s in GenerationStatus]
        assert "pending" in statuses
        assert "selecting" in statuses
        assert "generating" in statuses
        assert "evaluating" in statuses
        assert "retrying" in statuses
        assert "delivering" in statuses
        assert "completed" in statuses
        assert "failed" in statuses

    def test_can_retry_logic(self):
        state = LuminaState(brief="t", retry_count=0, max_retries=3)
        assert state.can_retry() is True
        state2 = LuminaState(brief="t", retry_count=3, max_retries=3)
        assert state2.can_retry() is False
        state3 = LuminaState(brief="t", retry_count=4, max_retries=3)
        assert state3.can_retry() is False

    def test_taste_score_all_fields(self):
        ts = TasteScore(
            composition=80, color=85, brand_fit=90,
            emotional_impact=75, aggregated=82.5,
            ip_worldview=70, fan_expectation=65,
        )
        assert ts.composition == 80
        assert ts.color == 85
        assert ts.brand_fit == 90
        assert ts.emotional_impact == 75
        assert ts.aggregated == 82.5
        assert ts.ip_worldview == 70
        assert ts.fan_expectation == 65

    def test_brief_params_defaults(self):
        bp = BriefParams(prompt="test")
        assert bp.subject == ""
        assert bp.style == "general"
        assert bp.mood == "neutral"
        assert bp.reference_context == ""

    def test_model_selection_required_fields(self):
        ms = ModelSelection(
            model_id="test", model_name="Test", provider="test",
            capability_score=80, cost_per_call=0.05, selection_reason="test",
        )
        assert ms.model_id == "test"
        assert ms.capability_score == 80
        assert ms.cost_per_call == 0.05


# ==================== Blueprint 型検証 ====================

class TestBlueprintIntegrity:
    """CreativeBlueprint の全フィールド検証"""

    def test_blueprint_business_models(self):
        assert len(BusinessModel) == 4
        assert BusinessModel.B2B.value == "b2b"
        assert BusinessModel.B2C.value == "b2c"
        assert BusinessModel.C2C.value == "c2c"
        assert BusinessModel.INTERNAL.value == "internal"

    def test_blueprint_defaults(self):
        bp = CreativeBlueprint()
        assert bp.business_model == BusinessModel.INTERNAL
        assert bp.quality_tier == QualityTier.STANDARD


# ==================== Registry 強化 ====================

class TestRegistryIntegrity:
    """ModelRegistryClient のデータ整合性"""

    @pytest.mark.asyncio
    async def test_seed_models_have_all_fields(self):
        client = ModelRegistryClient()
        models = await client.get_active_models()
        for m in models:
            assert m.id != ""
            assert m.model_name != ""
            assert m.provider != ""
            assert m.model_type == "image"
            assert m.capability_score > 0
            assert m.cost_per_call >= 0
            assert m.is_active is True

    @pytest.mark.asyncio
    async def test_get_nonexistent_model_returns_none(self):
        client = ModelRegistryClient()
        result = await client.get_model("nonexistent-model-xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_cost_filter_excludes_expensive(self):
        client = ModelRegistryClient()
        cheap = await client.get_best_model(model_type="image", max_cost=0.001)
        assert cheap is None or cheap.cost_per_call <= 0.001


# ==================== Critic Weights 検証 ====================

class TestCriticWeightsIntegrity:
    """Critic重みの合計が1.0であることを保証"""

    def test_default_weights_sum_to_one(self):
        total = sum(DEFAULT_CRITIC_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Default weights sum: {total}"

    def test_masterpiece_weights_sum_to_one(self):
        total = sum(MASTERPIECE_CRITIC_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Masterpiece weights sum: {total}"

    def test_default_has_4_critics(self):
        assert len(DEFAULT_CRITIC_WEIGHTS) == 4

    def test_masterpiece_has_6_critics(self):
        assert len(MASTERPIECE_CRITIC_WEIGHTS) == 6


# ==================== Escalation Step Coverage ====================

class TestEscalationStepCoverage:
    """全4段階のエスカレーションステップ完全検証"""

    @pytest.mark.asyncio
    async def test_step_0_normal_retry(self):
        state = LuminaState(brief="t", escalation_step=0)
        result = await ai_escalation_chain(state)
        assert result["status"] == GenerationStatus.GENERATING
        assert result["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_step_3_creative_decomposition(self):
        state = LuminaState(brief="t", escalation_step=3)
        result = await ai_escalation_chain(state)
        assert result["escalation_step"] == 4
        assert "decomposed_elements" in result["generated_asset_metadata"]
        elements = result["generated_asset_metadata"]["decomposed_elements"]
        assert "background" in elements
        assert "subject" in elements

    @pytest.mark.asyncio
    async def test_tier_upgrade_chain(self):
        """各ティアの昇格が正しい順序で行われるか"""
        for from_tier, to_tier in [
            (QualityTier.PREVIEW, QualityTier.STANDARD),
            (QualityTier.STANDARD, QualityTier.PREMIUM),
            (QualityTier.PREMIUM, QualityTier.MASTERPIECE),
            (QualityTier.MASTERPIECE, QualityTier.MASTERPIECE),
        ]:
            state = LuminaState(brief="t", quality_tier=from_tier, escalation_step=2)
            result = await ai_escalation_chain(state)
            assert result["quality_tier"] == to_tier, f"{from_tier} should upgrade to {to_tier}"


# ==================== Marketplace 強化 ====================

class TestMarketplaceIntegrity:
    """Marketplace のデータ整合性"""

    @pytest.mark.asyncio
    async def test_royalty_calculation(self):
        mp = StylePackMarketplace()
        packs = await mp.list_packs()
        for pack in packs:
            result = await mp.apply_pack(pack.id, "test")
            expected_royalty = pack.price * pack.royalty_rate
            assert result["royalty"] == expected_royalty

    @pytest.mark.asyncio
    async def test_download_count_increments(self):
        mp = StylePackMarketplace()
        packs = await mp.list_packs()
        p = packs[0]
        initial = p.downloads
        await mp.apply_pack(p.id, "test")
        assert p.downloads == initial + 1
        await mp.apply_pack(p.id, "test2")
        assert p.downloads == initial + 2

    @pytest.mark.asyncio
    async def test_apply_nonexistent_pack(self):
        mp = StylePackMarketplace()
        result = await mp.apply_pack("nonexistent-id", "test")
        assert "error" in result


# ==================== Delivery 強化 ====================

class TestDeliveryIntegrity:
    """Delivery Layer のフィールド完全性"""

    @pytest.mark.asyncio
    async def test_format_optimizer_image_config(self):
        state = LuminaState(brief="t", asset_type=AssetType.IMAGE)
        result = await format_optimizer(state)
        assert result["delivery_metadata"]["format_optimized"] is True
        config = result["delivery_metadata"]["format_config"]
        assert "format" in config
        assert config["format"] == "webp"

    @pytest.mark.asyncio
    async def test_packager_filename_format(self):
        state = LuminaState(brief="t", tenant_id="acme-corp")
        result = await asset_packager(state)
        meta = result["delivery_metadata"]
        assert meta["filename"].startswith("lumina_acme-corp_")
        assert meta["version"] == 1
        assert len(meta["package_id"]) == 8
