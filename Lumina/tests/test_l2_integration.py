"""L2: Integration Tests — ノード間データフロー検証

World-Class Test Patterns > L2: Integration Tests
5つの検証パターン:
1. State Flow — Node A の出力が Node B の入力として正しく消費される
2. Key Collision — 各ノードの出力キーセットが相互に排他的
3. Error Propagation — 異形入力での動作
4. Observability — メタデータ蓄積
5. Full Pipeline — 全ノード連結時の状態一貫性
"""

import pytest

from src.models.state import (
    BriefParams,
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
    TasteScore,
)
from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.graph.nodes.creation.model_selector import model_selector
from src.graph.nodes.creation.generator import generator
from src.graph.nodes.creation.enhancer_pipeline import enhancer_pipeline
from src.graph.nodes.creation.multi_model_compositor import multi_model_compositor
from src.graph.nodes.quality.taste_engine import taste_engine
from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
from src.graph.nodes.quality.ai_escalation_chain import ai_escalation_chain
from src.graph.nodes.delivery.delivery_nodes import (
    format_optimizer,
    asset_packager,
    brand_consistency_check,
)
from src.registry.client import ModelRegistryClient


# =========================
# L2-1: State Flow Tests
# =========================

class TestStateFlowCreationLayer:
    """Creation Layer: brief_interpreter → model_selector → generator の状態フロー"""

    @pytest.mark.asyncio
    async def test_brief_to_selector_flow(self):
        """brief_interpreter の出力が model_selector の入力として消費される"""
        state = LuminaState(brief="サイバーパンクな東京の夜景")

        result_bi = await brief_interpreter(state)
        assert "brief_params" in result_bi
        assert result_bi["brief_params"] is not None

        # model_selector に渡す
        updated = state.model_copy(update=result_bi)
        result_ms = await model_selector(updated, registry=ModelRegistryClient())
        assert "model_selection" in result_ms
        assert result_ms["model_selection"].model_id != ""

    @pytest.mark.asyncio
    async def test_selector_to_generator_flow(self):
        """model_selector の出力が generator の入力として消費される"""
        state = LuminaState(
            brief="test",
            brief_params=BriefParams(prompt="cyberpunk city", style="cyberpunk"),
        )
        result_ms = await model_selector(state, registry=ModelRegistryClient())
        updated = state.model_copy(update=result_ms)

        result_gen = await generator(updated)
        assert result_gen["generated_asset_url"] != ""
        assert result_gen["generated_asset_metadata"]["provider"] != ""

    @pytest.mark.asyncio
    async def test_generator_to_taste_engine_flow(self):
        """generator の出力が taste_engine の入力として消費される"""
        state = LuminaState(
            brief="dramatic landscape",
            brief_params=BriefParams(prompt="dramatic mountain landscape, vibrant colors"),
            generated_asset_url="https://example.com/generated.png",
        )
        result_te = await taste_engine(state)
        assert result_te["taste_score"].aggregated > 0

    @pytest.mark.asyncio
    async def test_taste_to_cascade_flow(self):
        """taste_engine の出力が quality_score_cascade で判定される"""
        state = LuminaState(
            brief="test",
            taste_score=TasteScore(aggregated=80.0),
            quality_threshold=75.0,
            quality_tier=QualityTier.STANDARD,
        )
        result = await quality_score_cascade(state)
        assert result["status"] == GenerationStatus.DELIVERING

    @pytest.mark.asyncio
    async def test_full_creation_to_delivery_flow(self):
        """Creation → Quality → Delivery の全フロー"""
        state = LuminaState(brief="ミニマルなロゴデザイン")

        # Step 1: brief_interpreter
        r1 = await brief_interpreter(state)
        state = state.model_copy(update=r1)
        assert state.brief_params is not None
        assert state.brief_params.style == "minimalist"

        # Step 2: model_selector
        r2 = await model_selector(state, registry=ModelRegistryClient())
        state = state.model_copy(update=r2)
        assert state.model_selection is not None

        # Step 3: generator
        r3 = await generator(state)
        state = state.model_copy(update=r3)
        assert state.generated_asset_url != ""

        # Step 4: enhancer
        r4 = await enhancer_pipeline(state)
        state = state.model_copy(update=r4)

        # Step 5: taste_engine
        r5 = await taste_engine(state)
        state = state.model_copy(update=r5)
        assert state.taste_score is not None
        assert state.taste_score.aggregated > 0

        # Step 6: delivery
        r6 = await format_optimizer(state)
        state = state.model_copy(update=r6)
        r7 = await asset_packager(state)
        state = state.model_copy(update=r7)
        r8 = await brand_consistency_check(state)
        state = state.model_copy(update=r8)
        assert state.deliverable_url != ""
        assert state.status == GenerationStatus.COMPLETED


# =========================
# L2-2: Key Collision Tests
# =========================

class TestNoStateKeyCollisions:
    """各ノードの出力キーセットが相互に排他的であることを検証"""

    @pytest.mark.asyncio
    async def test_creation_layer_no_collisions(self):
        """Creation Layer ノード間でキー衝突がないこと"""
        state = LuminaState(
            brief="test artwork",
            brief_params=BriefParams(prompt="test", style="general"),
            model_selection=ModelSelection(
                model_id="flux-1.1-pro", model_name="Flux", provider="black-forest-labs",
                capability_score=90, cost_per_call=0.04, selection_reason="test",
            ),
            generated_asset_url="https://example.com/test.png",
        )

        r_bi = await brief_interpreter(state)
        r_ms = await model_selector(state, registry=ModelRegistryClient())
        r_gen = await generator(state)

        # status はどのノードも返すため除外
        keys_bi = {k for k in r_bi.keys() if k != "status"}
        keys_ms = {k for k in r_ms.keys() if k != "status"}
        keys_gen = {k for k in r_gen.keys() if k not in ("status", "generated_asset_metadata")}

        assert keys_bi.isdisjoint(keys_ms), f"Collision bi↔ms: {keys_bi & keys_ms}"
        assert keys_bi.isdisjoint(keys_gen), f"Collision bi↔gen: {keys_bi & keys_gen}"
        assert keys_ms.isdisjoint(keys_gen), f"Collision ms↔gen: {keys_ms & keys_gen}"


# =========================
# L2-3: Error Propagation Tests
# =========================

class TestErrorPropagation:
    """異形入力がグレースフルに処理されること"""

    @pytest.mark.asyncio
    async def test_empty_brief_propagates_error(self):
        """空ブリーフが適切にエラーとして伝搬"""
        state = LuminaState(brief="")
        result = await brief_interpreter(state)
        assert result["status"] == GenerationStatus.FAILED
        assert "error" in result

    @pytest.mark.asyncio
    async def test_missing_brief_params_for_selector(self):
        """brief_params未設定で model_selector がエラーを返す"""
        state = LuminaState(brief="test", brief_params=None)
        result = await model_selector(state, registry=ModelRegistryClient())
        assert result["status"] == GenerationStatus.FAILED

    @pytest.mark.asyncio
    async def test_missing_model_for_generator(self):
        """model_selection未設定で generator がエラーを返す"""
        state = LuminaState(brief="test", model_selection=None)
        result = await generator(state)
        assert result["status"] == GenerationStatus.FAILED

    @pytest.mark.asyncio
    async def test_no_asset_for_taste_engine(self):
        """生成物なしで taste_engine がエラーを返す"""
        state = LuminaState(brief="test", generated_asset_url="")
        result = await taste_engine(state)
        assert result["status"] == GenerationStatus.FAILED

    @pytest.mark.asyncio
    async def test_no_taste_score_for_cascade(self):
        """Taste Score なしで cascade がエラーを返す"""
        state = LuminaState(brief="test", taste_score=None)
        result = await quality_score_cascade(state)
        assert result["status"] == GenerationStatus.FAILED
