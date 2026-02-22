"""L3: Performance Benchmarks — レイテンシ・安定性

World-Class Test Patterns > L3: Performance Benchmarks
各コンポーネントにms単位の上限を設定し、安定性を100回反復で検証。
"""

import time

import pytest

from src.models.state import BriefParams, LuminaState, ModelSelection, QualityTier
from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.graph.nodes.creation.model_selector import model_selector
from src.graph.nodes.creation.generator import generator
from src.graph.nodes.quality.taste_engine import taste_engine
from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
from src.graph.nodes.evolution.evolution_nodes import (
    style_frontier_tracker,
    predictive_qc,
    taste_calibrator,
    TrendSignal,
)
from src.marketplace.style_packs import StylePackMarketplace
from src.registry.client import ModelRegistryClient


# === 閾値定義 ===
FAST_NODE_MAX_MS = 5.0  # 軽量ノード
NORMAL_NODE_MAX_MS = 20.0  # 標準ノード
STABILITY_ITERATIONS = 100


async def _measure(func, *args, iterations=10, **kwargs):
    """関数を複数回実行し、平均/最大レイテンシをms単位で返す"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return sum(times) / len(times), max(times)


# =========================
# Creation Layer Performance
# =========================

class TestCreationPerformance:
    """Creation Layer ノードのレイテンシ"""

    @pytest.mark.asyncio
    async def test_brief_interpreter_latency(self):
        state = LuminaState(brief="サイバーパンクな東京の夜景、ネオン輝くビル群")
        avg, max_ms = await _measure(brief_interpreter, state)
        assert avg < FAST_NODE_MAX_MS, f"Avg {avg:.3f}ms > {FAST_NODE_MAX_MS}ms"

    @pytest.mark.asyncio
    async def test_model_selector_latency(self):
        state = LuminaState(
            brief="test",
            brief_params=BriefParams(prompt="test", style="general"),
        )
        registry = ModelRegistryClient()
        avg, _ = await _measure(model_selector, state, registry=registry)
        assert avg < FAST_NODE_MAX_MS, f"Avg {avg:.3f}ms > {FAST_NODE_MAX_MS}ms"

    @pytest.mark.asyncio
    async def test_generator_latency(self):
        state = LuminaState(
            brief="test",
            brief_params=BriefParams(prompt="test prompt"),
            model_selection=ModelSelection(
                model_id="flux", model_name="Flux", provider="black-forest-labs",
                capability_score=90, cost_per_call=0.04, selection_reason="test",
            ),
        )
        avg, _ = await _measure(generator, state)
        assert avg < FAST_NODE_MAX_MS, f"Avg {avg:.3f}ms > {FAST_NODE_MAX_MS}ms"


# =========================
# Quality Fortress Performance
# =========================

class TestQualityPerformance:
    """Quality Fortress ノードのレイテンシ"""

    @pytest.mark.asyncio
    async def test_taste_engine_latency(self):
        state = LuminaState(
            brief="test",
            brief_params=BriefParams(prompt="dramatic neon cyberpunk"),
            generated_asset_url="https://example.com/test.png",
        )
        avg, _ = await _measure(taste_engine, state)
        assert avg < NORMAL_NODE_MAX_MS, f"Avg {avg:.3f}ms > {NORMAL_NODE_MAX_MS}ms"


# =========================
# Evolution Performance
# =========================

class TestEvolutionPerformance:
    """Evolution Layer ノードのレイテンシ"""

    @pytest.mark.asyncio
    async def test_cross_validation_latency(self):
        avg, _ = await _measure(style_frontier_tracker)
        assert avg < FAST_NODE_MAX_MS, f"Avg {avg:.3f}ms > {FAST_NODE_MAX_MS}ms"

    @pytest.mark.asyncio
    async def test_predictive_qc_latency(self):
        scores = [85.0] * 30
        avg, _ = await _measure(predictive_qc, scores)
        assert avg < FAST_NODE_MAX_MS, f"Avg {avg:.3f}ms > {FAST_NODE_MAX_MS}ms"


# =========================
# Stability Under Load
# =========================

class TestStabilityUnderLoad:
    """100回反復で結果が一貫するか"""

    @pytest.mark.asyncio
    async def test_brief_interpreter_100_iterations(self):
        state = LuminaState(brief="水彩画風の風景")
        results = []
        for _ in range(STABILITY_ITERATIONS):
            r = await brief_interpreter(state)
            results.append(r["brief_params"].style)
        assert all(s == "watercolor" for s in results), "Inconsistent across 100 runs"

    @pytest.mark.asyncio
    async def test_model_selector_100_iterations(self):
        state = LuminaState(
            brief="test",
            brief_params=BriefParams(prompt="test", style="general"),
        )
        registry = ModelRegistryClient()
        model_ids = []
        for _ in range(STABILITY_ITERATIONS):
            r = await model_selector(state, registry=registry)
            model_ids.append(r["model_selection"].model_id)
        assert all(m == model_ids[0] for m in model_ids), "Inconsistent model selection"

    @pytest.mark.asyncio
    async def test_quality_cascade_100_iterations(self):
        """品質判定が100回一貫するか"""
        from src.models.state import TasteScore
        state = LuminaState(
            brief="test",
            taste_score=TasteScore(aggregated=80.0),
            quality_threshold=75.0,
            quality_tier=QualityTier.STANDARD,
        )
        results = []
        for _ in range(STABILITY_ITERATIONS):
            r = await quality_score_cascade(state)
            results.append(r["status"])
        from src.models.state import GenerationStatus
        assert all(r == GenerationStatus.DELIVERING for r in results)

    @pytest.mark.asyncio
    async def test_marketplace_100_iterations(self):
        """マーケットプレイス操作が100回一貫するか"""
        mp = StylePackMarketplace()
        packs = await mp.list_packs()
        pack_id = packs[0].id

        for _ in range(STABILITY_ITERATIONS):
            result = await mp.apply_pack(pack_id, "a warrior")
            assert "warrior" in result["prompt"]
