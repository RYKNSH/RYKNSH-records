"""Intelligence Layer ノード — 🔵 (MS6)

sota_watchdog, style_frontier_tracker, model_benchmarker は
Evolution Layerのモジュールとして実装済み。
Intelligence Layer はそれらを週次スケジュールで呼び出すオーケストレーター。
"""

from __future__ import annotations

from typing import Any

from src.graph.nodes.evolution.evolution_nodes import (
    model_benchmarker,
    sota_watchdog,
    style_frontier_tracker,
)


async def run_intelligence_cycle(
    model_registry_data: list[dict],
) -> dict[str, Any]:
    """Intelligence Layerの週次サイクルを実行

    1. SOTA Watchdog: 新モデル検出
    2. Style Frontier Tracker: トレンド検出 + Cross-Validation
    3. Model Benchmarker: 全モデル再評価
    """
    watchdog_results = await sota_watchdog()
    validated_trends = await style_frontier_tracker()
    benchmark_results = await model_benchmarker(model_registry_data)

    return {
        "watchdog": watchdog_results,
        "trends": [t.model_dump() for t in validated_trends],
        "benchmarks": benchmark_results,
    }
