"""L4: Lifecycle E2E Tests — Brief入力→Deliverable出力まで完全統合

World-Class Test Patterns > L4
全レイヤーを実際に通す。モックなし。各中間成果物を検証。
"""

import pytest

from src.models.state import (
    BriefParams,
    GenerationStatus,
    LuminaState,
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
from src.graph.nodes.delivery.delivery_nodes import (
    format_optimizer,
    asset_packager,
    brand_consistency_check,
)
from src.registry.client import ModelRegistryClient
from src.graph.lumina_graph import get_graph_spec


class TestFullPipelineE2E:
    """Brief入力 → Deliverable出力 の完全E2E"""

    @pytest.mark.asyncio
    async def test_standard_b2b_full_pipeline(self):
        """Standard B2B: 全パイプライン通過"""
        # Stage 1: Brief → BriefParams
        state = LuminaState(
            brief="モダンなSaaS企業のヒーロー画像、青と白のグラデーション",
            quality_tier=QualityTier.STANDARD,
            tenant_id="acme-saas",
        )
        r1 = await brief_interpreter(state)
        state = state.model_copy(update=r1)
        assert state.status == GenerationStatus.SELECTING
        assert state.brief_params is not None
        assert state.brief_params.prompt != ""
        assert state.brief_params.style != ""

        # Stage 2: Model Selection
        r2 = await model_selector(state, registry=ModelRegistryClient())
        state = state.model_copy(update=r2)
        assert state.status == GenerationStatus.GENERATING
        assert state.model_selection is not None
        assert state.model_selection.cost_per_call > 0

        # Stage 3: Generation
        r3 = await generator(state)
        state = state.model_copy(update=r3)
        assert state.status == GenerationStatus.COMPLETED
        assert state.generated_asset_url != ""
        assert state.generated_asset_metadata.get("provider") != ""

        # Stage 4: Enhance (Standard = enhanced)
        r4 = await enhancer_pipeline(state)
        state = state.model_copy(update=r4)
        assert state.generated_asset_metadata.get("enhanced") is True
        assert state.generated_asset_metadata.get("upscale", {}).get("upscaled") is True

        # Stage 5: Taste Engine
        r5 = await taste_engine(state)
        state = state.model_copy(update=r5)
        assert state.status == GenerationStatus.EVALUATING
        assert state.taste_score is not None
        assert state.taste_score.composition > 0
        assert state.taste_score.color > 0
        assert state.taste_score.brand_fit > 0
        assert state.taste_score.emotional_impact > 0
        assert 0 < state.taste_score.aggregated <= 100

        # Stage 6: Quality Score Cascade (force pass by setting low threshold)
        state = state.model_copy(update={"quality_threshold": 0.0})
        r6 = await quality_score_cascade(state)
        state = state.model_copy(update=r6)
        assert state.status == GenerationStatus.DELIVERING

        # Stage 7: Delivery Pipeline
        r7 = await format_optimizer(state)
        state = state.model_copy(update=r7)
        assert state.delivery_metadata.get("format_optimized") is True

        r8 = await asset_packager(state)
        state = state.model_copy(update=r8)
        assert "acme-saas" in state.delivery_metadata.get("filename", "")
        assert state.delivery_metadata.get("version") == 1

        r9 = await brand_consistency_check(state)
        state = state.model_copy(update=r9)
        assert state.status == GenerationStatus.COMPLETED
        assert state.deliverable_url != ""
        assert state.delivery_metadata.get("brand_check_passed") is True

    @pytest.mark.asyncio
    async def test_preview_fast_path(self):
        """Preview ティア: エンハンスなし + 品質無条件通過"""
        state = LuminaState(
            brief="シンプルなアイコン",
            quality_tier=QualityTier.PREVIEW,
        )

        r1 = await brief_interpreter(state)
        state = state.model_copy(update=r1)

        r2 = await model_selector(state, registry=ModelRegistryClient())
        state = state.model_copy(update=r2)
        assert state.model_selection.cost_per_call <= 0.02  # Preview = 安いモデル

        r3 = await generator(state)
        state = state.model_copy(update=r3)

        # Preview: エンハンスなし
        r4 = await enhancer_pipeline(state)
        state = state.model_copy(update=r4)
        assert "enhanced" not in state.generated_asset_metadata

        # Preview: Taste は実行するが cascade で無条件通過
        r5 = await taste_engine(state)
        state = state.model_copy(update=r5)
        r6 = await quality_score_cascade(state)
        state = state.model_copy(update=r6)
        assert state.status == GenerationStatus.DELIVERING

    @pytest.mark.asyncio
    async def test_premium_multi_model_path(self):
        """Premium ティア: マルチモデル合成が実行される"""
        state = LuminaState(
            brief="luxury brand campaign key visual, epic dramatic composition",
            quality_tier=QualityTier.PREMIUM,
        )

        r1 = await brief_interpreter(state)
        state = state.model_copy(update=r1)

        r2 = await model_selector(state, registry=ModelRegistryClient())
        state = state.model_copy(update=r2)

        r3 = await generator(state)
        state = state.model_copy(update=r3)

        # Premium: マルチモデル合成
        r_mm = await multi_model_compositor(state)
        state = state.model_copy(update=r_mm)
        assert state.generated_asset_metadata.get("multi_model") is True
        assert "composite_layers" in state.generated_asset_metadata

        r4 = await enhancer_pipeline(state)
        state = state.model_copy(update=r4)
        assert state.generated_asset_metadata.get("enhanced") is True


class TestRetryLoopE2E:
    """リトライ→エスカレーションのフルサイクル検証"""

    @pytest.mark.asyncio
    async def test_retry_then_pass(self):
        """品質不合格→リトライ→合格の流れ"""
        state = LuminaState(
            brief="test",
            taste_score=TasteScore(aggregated=60.0),
            quality_threshold=75.0,
            quality_tier=QualityTier.STANDARD,
            retry_count=0, max_retries=3,
        )

        # 1st: 不合格 → リトライ
        r1 = await quality_score_cascade(state)
        assert r1["status"] == GenerationStatus.RETRYING
        assert r1["retry_count"] == 1

        # 2nd: 合格スコアに更新
        state = state.model_copy(update={
            "taste_score": TasteScore(aggregated=80.0),
            "retry_count": 1,
        })
        r2 = await quality_score_cascade(state)
        assert r2["status"] == GenerationStatus.DELIVERING


class TestGraphSpec:
    """Graph Spec の構造検証"""

    def test_graph_spec_has_all_nodes(self):
        spec = get_graph_spec()
        assert len(spec["nodes"]) == 11
        assert spec["entry_point"] == "brief_interpreter"

    def test_graph_spec_layers(self):
        spec = get_graph_spec()
        assert len(spec["layers"]["creation"]) == 5
        assert len(spec["layers"]["quality"]) == 3
        assert len(spec["layers"]["delivery"]) == 3

    def test_graph_spec_all_nodes_have_edges(self):
        spec = get_graph_spec()
        for node in spec["nodes"]:
            assert node in spec["edges"], f"Node {node} has no edges defined"
