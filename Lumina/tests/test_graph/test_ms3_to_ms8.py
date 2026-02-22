"""MS3-MS8 全ノードテスト

MS3: enhancer_pipeline, multi_model_compositor
MS4: format_optimizer, asset_packager, brand_consistency_check
MS5: multi_model_compositor Premium
MS6: Evolution Layer全ノード + Intelligence cycle
MS7: C2C Style Pack Marketplace
MS8: Autonomous Taste Calibration Loop (L3)
"""

import pytest

from src.graph.nodes.creation.enhancer_pipeline import enhancer_pipeline
from src.graph.nodes.creation.multi_model_compositor import multi_model_compositor
from src.graph.nodes.delivery.delivery_nodes import (
    asset_packager,
    brand_consistency_check,
    format_optimizer,
)
from src.graph.nodes.evolution.evolution_nodes import (
    _cross_validate_signals,
    TrendSignal,
    model_benchmarker,
    predictive_qc,
    sota_updater,
    sota_watchdog,
    style_frontier_tracker,
    taste_calibrator,
)
from src.graph.nodes.evolution.autonomous_loop import run_autonomous_loop
from src.graph.nodes.intelligence.intelligence_nodes import run_intelligence_cycle
from src.marketplace.style_packs import StylePack, StylePackMarketplace
from src.models.state import (
    BriefParams,
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
)


# ==================== MS3: Enhancer + Multi-Model ====================

@pytest.mark.asyncio
async def test_enhancer_pipeline_standard():
    """Standardティアのエンハンス実行"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(mood="vibrant", prompt="test"),
        generated_asset_url="https://example.com/test.png",
        quality_tier=QualityTier.STANDARD,
    )
    result = await enhancer_pipeline(state)
    assert result["generated_asset_metadata"]["enhanced"] is True
    assert result["generated_asset_metadata"]["upscale"]["upscaled"] is True


@pytest.mark.asyncio
async def test_enhancer_pipeline_preview_skip():
    """Previewティアはエンハンスをスキップ"""
    state = LuminaState(
        brief="test",
        generated_asset_url="https://example.com/test.png",
        quality_tier=QualityTier.PREVIEW,
    )
    result = await enhancer_pipeline(state)
    assert result["status"] == GenerationStatus.EVALUATING
    assert "generated_asset_metadata" not in result


@pytest.mark.asyncio
async def test_multi_model_compositor_premium():
    """Premiumティアのマルチモデル合成"""
    state = LuminaState(
        brief="test",
        generated_asset_url="https://example.com/test.png",
        quality_tier=QualityTier.PREMIUM,
        model_selection=ModelSelection(
            model_id="flux-1.1-pro", model_name="Flux 1.1 Pro",
            provider="bfl", capability_score=92, cost_per_call=0.04,
            selection_reason="test",
        ),
    )
    result = await multi_model_compositor(state)
    assert result["generated_asset_metadata"]["multi_model"] is True
    assert "composite_layers" in result["generated_asset_metadata"]


@pytest.mark.asyncio
async def test_multi_model_compositor_standard_skip():
    """Standardティアはマルチモデル合成をスキップ"""
    state = LuminaState(
        brief="test",
        generated_asset_url="https://example.com/test.png",
        quality_tier=QualityTier.STANDARD,
    )
    result = await multi_model_compositor(state)
    assert result == {}


# ==================== MS4: Delivery Layer ====================

@pytest.mark.asyncio
async def test_format_optimizer():
    """フォーマット最適化"""
    state = LuminaState(brief="test")
    result = await format_optimizer(state)
    assert result["delivery_metadata"]["format_optimized"] is True


@pytest.mark.asyncio
async def test_asset_packager():
    """アセットパッケージ化"""
    state = LuminaState(brief="test", tenant_id="tenant-001")
    result = await asset_packager(state)
    assert "package_id" in result["delivery_metadata"]
    assert "tenant-001" in result["delivery_metadata"]["filename"]


@pytest.mark.asyncio
async def test_brand_consistency_check():
    """ブランド一貫性チェック"""
    state = LuminaState(
        brief="test",
        generated_asset_url="https://example.com/test.png",
    )
    result = await brand_consistency_check(state)
    assert result["status"] == GenerationStatus.COMPLETED
    assert result["delivery_metadata"]["brand_check_passed"] is True
    assert result["deliverable_url"] != ""


# ==================== MS6: Evolution Layer ====================

@pytest.mark.asyncio
async def test_sota_watchdog():
    """SOTA Watchdog実行"""
    result = await sota_watchdog()
    assert "new_models" in result
    assert len(result["new_models"]) > 0


@pytest.mark.asyncio
async def test_style_frontier_tracker_cross_validation():
    """Cross-Validation で一過性バズを排除"""
    result = await style_frontier_tracker()
    trend_names = [t.name for t in result]
    assert "neo-brutalism" in trend_names  # 持続8w + 2ソース → 採用
    assert "ai-slop-trend" not in trend_names  # 持続1w → 排除


@pytest.mark.asyncio
async def test_cross_validate_signals_logic():
    """Cross-Validation ロジック詳細"""
    signals = [
        TrendSignal(source="award", name="trend-a", score=90, sustained_weeks=6),
        TrendSignal(source="buzz", name="trend-a", score=85, sustained_weeks=6),
        TrendSignal(source="buzz", name="trend-b", score=95, sustained_weeks=2),  # 短すぎ
        TrendSignal(source="award", name="trend-c", score=80, sustained_weeks=5),  # ソース1つだけ
    ]
    validated = _cross_validate_signals(signals)
    names = [t.name for t in validated]
    assert "trend-a" in names
    assert "trend-b" not in names
    assert "trend-c" not in names


@pytest.mark.asyncio
async def test_model_benchmarker():
    """モデルベンチマーク"""
    models = [
        {"id": "flux-1.1-pro", "capability_score": 92},
        {"id": "dall-e-3", "capability_score": 85},
    ]
    results = await model_benchmarker(models)
    assert len(results) == 2
    assert all("new_score" in r for r in results)


@pytest.mark.asyncio
async def test_taste_calibrator_update():
    """Taste Calibratorの更新"""
    trends = [
        TrendSignal(source="award", name="trend-x", score=90, sustained_weeks=8, is_validated=True),
    ]
    result = await taste_calibrator(trends, current_genome={"version": 1, "quality_score": 80})
    assert result["updated"] is True
    assert result["genome_version"] == 2


@pytest.mark.asyncio
async def test_taste_calibrator_no_trends():
    """トレンドなしの場合は更新しない"""
    result = await taste_calibrator([], current_genome={"version": 1})
    assert result["updated"] is False


@pytest.mark.asyncio
async def test_predictive_qc_declining():
    """品質低下の予測"""
    # 低下トレンド: 前半高い、後半低い
    scores = [90, 88, 89, 87, 88, 82, 80, 79, 78, 77]
    result = await predictive_qc(scores)
    assert result["prediction"] == "declining"
    assert "recommended_actions" in result


@pytest.mark.asyncio
async def test_predictive_qc_stable():
    """安定品質"""
    scores = [85, 86, 85, 84, 86, 85, 86, 85, 84, 85]
    result = await predictive_qc(scores)
    assert result["prediction"] == "stable"


@pytest.mark.asyncio
async def test_sota_updater():
    """SOTA Updater"""
    watchdog = {"new_models": [{"name": "NewModel", "estimated_score": 95}]}
    benchmarks = [{"model_id": "old-model", "degraded": True}]
    result = await sota_updater(watchdog, benchmarks)
    assert result["models_to_register"] == 1
    assert result["models_degraded"] == 1


@pytest.mark.asyncio
async def test_intelligence_cycle():
    """Intelligence Layer週次サイクル"""
    models = [{"id": "flux-1.1-pro", "capability_score": 92}]
    result = await run_intelligence_cycle(models)
    assert "watchdog" in result
    assert "trends" in result
    assert "benchmarks" in result


# ==================== MS7: C2C Style Pack ====================

@pytest.mark.asyncio
async def test_marketplace_list():
    """スタイルパック一覧"""
    mp = StylePackMarketplace()
    packs = await mp.list_packs()
    assert len(packs) == 2


@pytest.mark.asyncio
async def test_marketplace_list_by_genre():
    """ジャンル指定フィルター"""
    mp = StylePackMarketplace()
    packs = await mp.list_packs(genre="cyberpunk")
    assert len(packs) == 1
    assert packs[0].name == "Cyberpunk Tokyo"


@pytest.mark.asyncio
async def test_marketplace_apply_pack():
    """スタイルパック適用"""
    mp = StylePackMarketplace()
    packs = await mp.list_packs()
    result = await mp.apply_pack(packs[0].id, "a samurai warrior")
    assert "samurai warrior" in result["prompt"]
    assert result["royalty"] > 0


@pytest.mark.asyncio
async def test_marketplace_publish_quality_gate():
    """品質ゲート: taste_score < 80 は拒否"""
    mp = StylePackMarketplace()
    low_quality = StylePack(name="bad", taste_score=50.0)
    result = await mp.publish_pack(low_quality)
    assert result["published"] is False


@pytest.mark.asyncio
async def test_marketplace_publish_success():
    """品質ゲート通過で公開成功"""
    mp = StylePackMarketplace()
    good_pack = StylePack(name="good", taste_score=85.0, price=300)
    result = await mp.publish_pack(good_pack)
    assert result["published"] is True


# ==================== MS8: L3 Full Auto ====================

@pytest.mark.asyncio
async def test_autonomous_loop_full_cycle():
    """L3 Autonomous Loop 完全サイクル"""
    models = [{"id": "flux-1.1-pro", "capability_score": 92}]
    scores = [85, 86, 85, 84, 86, 85, 86, 85, 84, 85]
    genome = {"version": 1, "quality_score": 80}

    report = await run_autonomous_loop(
        model_registry_data=models,
        current_genome=genome,
        quality_scores_30d=scores,
    )

    assert report.new_models_detected is not None
    assert len(report.trends_validated) > 0  # neo-brutalism must pass
    assert report.quality_prediction == "stable"
    assert isinstance(report.actions_taken, list)


@pytest.mark.asyncio
async def test_autonomous_loop_taste_update():
    """L3 Loop: Taste Genome更新が発生"""
    models = [{"id": "model-1", "capability_score": 80}]
    genome = {"version": 1, "quality_score": 75}

    report = await run_autonomous_loop(
        model_registry_data=models,
        current_genome=genome,
    )

    assert report.taste_genome_updated is True
    assert any("taste_genome_updated" in a for a in report.actions_taken)
