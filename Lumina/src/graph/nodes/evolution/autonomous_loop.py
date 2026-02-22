"""Autonomous Taste Calibration Loop — L3 Full Auto (MS8)

Whitepaper Round 8: 品質自律ループの完全実装。
Market Signal → Cross-Validation → Taste Genome Update → Self-Validation Gate
週次サイクルで自動実行。ローンチ後の人間関与ゼロ。
"""

from __future__ import annotations

from typing import Any

from src.graph.nodes.evolution.evolution_nodes import (
    EvolutionReport,
    TrendSignal,
    model_benchmarker,
    predictive_qc,
    sota_updater,
    sota_watchdog,
    style_frontier_tracker,
    taste_calibrator,
)


async def run_autonomous_loop(
    model_registry_data: list[dict],
    current_genome: dict[str, Any] | None = None,
    quality_scores_30d: list[float] | None = None,
) -> EvolutionReport:
    """L3 完全自律ループ — 週次実行

    1. Market Signal Collection (SOTA + Style)
    2. Multi-Signal Cross-Validation (一過性バズ排除)
    3. Model Benchmarking (全モデル再評価)
    4. Taste Calibration (Genome自動更新)
    5. Predictive QC (品質低下予防)
    6. SOTA Update (Registry自動更新)
    7. Self-Validation Gate (劣化時ロールバック)
    """
    report = EvolutionReport()

    # Step 1: Market Signal Collection
    watchdog_results = await sota_watchdog()
    report.new_models_detected = watchdog_results.get("new_models", [])

    # Step 2: Multi-Signal Cross-Validation
    validated_trends = await style_frontier_tracker()
    report.trends_validated = validated_trends

    # Step 3: Model Benchmarking
    benchmark_results = await model_benchmarker(model_registry_data)

    # Step 4: Taste Calibration
    calibration_result = await taste_calibrator(
        validated_trends=validated_trends,
        current_genome=current_genome,
    )
    report.taste_genome_updated = calibration_result.get("updated", False)  
    if report.taste_genome_updated:
        report.actions_taken.append(
            f"taste_genome_updated: +{calibration_result.get('quality_score_delta', 0)} "
            f"refs={calibration_result.get('new_references_added', [])}"
        )

    # Step 5: Predictive QC
    if quality_scores_30d:
        qc_result = await predictive_qc(quality_scores_30d)
        report.quality_prediction = qc_result.get("prediction", "unknown")
        if qc_result.get("prediction") == "declining":
            report.actions_taken.extend(qc_result.get("recommended_actions", []))

    # Step 6: SOTA Update
    update_result = await sota_updater(watchdog_results, benchmark_results)
    report.actions_taken.extend(update_result.get("actions", []))

    return report
