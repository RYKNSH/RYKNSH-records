"""Evolution Layer ノード (MS6)

sota_watchdog / style_frontier_tracker / model_benchmarker /
taste_calibrator / predictive_qc / sota_updater
Whitepaper Section 6 > 🔴 EVOLUTION + Round 8: Autonomous Taste Calibration
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrendSignal(BaseModel):
    """Market Signal Collector が収集するシグナル"""
    source: str  # award / buzz / competition / style
    name: str
    score: float
    sustained_weeks: int = 0
    is_validated: bool = False


class EvolutionReport(BaseModel):
    """Evolution Layerの実行レポート"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    new_models_detected: list[dict[str, Any]] = Field(default_factory=list)
    trends_validated: list[TrendSignal] = Field(default_factory=list)
    taste_genome_updated: bool = False
    quality_prediction: str = "stable"
    actions_taken: list[str] = Field(default_factory=list)


async def sota_watchdog() -> dict[str, Any]:
    """SOTA Watchdog — 最新技術監視犬

    arXiv/HuggingFace/主要AIサービスの新モデルを自動スキャン。
    """
    # MVP: シミュレーション
    detected_models = [
        {"name": "Flux 1.2", "source": "huggingface", "type": "image", "estimated_score": 94},
        {"name": "Sora v2.1", "source": "openai", "type": "video", "estimated_score": 90},
    ]

    return {
        "new_models": detected_models,
        "scan_date": datetime.utcnow().isoformat(),
    }


async def style_frontier_tracker() -> list[TrendSignal]:
    """Style Frontier Tracker — スタイル最前線追跡

    Behance/Dribbble/Pinterest のトレンド分析。
    Multi-Signal Cross-Validation で一過性バズを排除。
    """
    raw_signals = [
        TrendSignal(source="award", name="neo-brutalism", score=88, sustained_weeks=8),
        TrendSignal(source="buzz", name="ai-slop-trend", score=95, sustained_weeks=1),  # 一過性
        TrendSignal(source="award", name="organic-3d", score=82, sustained_weeks=6),
        TrendSignal(source="competition", name="neo-brutalism", score=85, sustained_weeks=8),
    ]

    # Multi-Signal Cross-Validation
    validated = _cross_validate_signals(raw_signals)
    return validated


def _cross_validate_signals(signals: list[TrendSignal]) -> list[TrendSignal]:
    """Multi-Signal Cross-Validation

    Award × Buzz × 競合採用 × 持続期間4w+ の交差点のみ採用。
    """
    # 名前でグループ化
    by_name: dict[str, list[TrendSignal]] = {}
    for s in signals:
        by_name.setdefault(s.name, []).append(s)

    validated = []
    for name, group in by_name.items():
        sources = {s.source for s in group}
        max_weeks = max(s.sustained_weeks for s in group)

        # 持続期間 < 4w → 一過性バズ、排除
        if max_weeks < 4:
            continue

        # 2つ以上のソースで確認 → Validated Trend
        if len(sources) >= 2:
            best = max(group, key=lambda s: s.score)
            best.is_validated = True
            validated.append(best)

    return validated


async def model_benchmarker(model_registry_data: list[dict]) -> list[dict[str, Any]]:
    """Model Benchmarker — 全モデルの定期ベンチマーク

    Model Registryの全モデルを参照セットで評価し、capability_scoreを更新。
    """
    results = []
    for model in model_registry_data:
        benchmark_score = model.get("capability_score", 50) + random.uniform(-3, 3)
        results.append({
            "model_id": model.get("id", ""),
            "previous_score": model.get("capability_score", 0),
            "new_score": round(benchmark_score, 1),
            "degraded": benchmark_score < model.get("capability_score", 0) - 5,
        })
    return results


async def taste_calibrator(
    validated_trends: list[TrendSignal],
    current_genome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Taste Calibrator — Autonomous Taste Calibration

    Round 8: Market Signal → Cross-Validation → Auto-Update → Self-Validation
    """
    if not validated_trends:
        return {"updated": False, "reason": "no_validated_trends"}

    # Taste Genome Auto-Update
    new_references = [t.name for t in validated_trends if t.is_validated]

    # Self-Validation Gate（A/Bテスト）
    old_score = current_genome.get("quality_score", 80) if current_genome else 80
    new_score = old_score + len(new_references) * 0.5  # 改善シミュレーション

    if new_score <= old_score:
        return {
            "updated": False,
            "reason": "self_validation_failed",
            "action": "rollback",
        }

    return {
        "updated": True,
        "new_references_added": new_references,
        "quality_score_delta": round(new_score - old_score, 2),
        "genome_version": (current_genome.get("version", 0) + 1) if current_genome else 1,
    }


async def predictive_qc(
    quality_scores_30d: list[float],
) -> dict[str, Any]:
    """Predictive QC — 予測的品質管理

    品質スコアの下降トレンドを検出→原因分析→自動是正。
    """
    if len(quality_scores_30d) < 5:
        return {"prediction": "insufficient_data"}

    recent = quality_scores_30d[-5:]
    older = quality_scores_30d[-10:-5] if len(quality_scores_30d) >= 10 else quality_scores_30d[:5]

    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    trend = avg_recent - avg_older

    if trend < -3:
        return {
            "prediction": "declining",
            "avg_recent": round(avg_recent, 1),
            "avg_older": round(avg_older, 1),
            "delta": round(trend, 1),
            "recommended_actions": [
                "model_registry_rebenchmark",
                "reference_set_refresh",
                "critic_weight_recalibrate",
            ],
        }
    elif trend > 3:
        return {
            "prediction": "improving",
            "avg_recent": round(avg_recent, 1),
            "delta": round(trend, 1),
        }

    return {
        "prediction": "stable",
        "avg_recent": round(avg_recent, 1),
        "delta": round(trend, 1),
    }


async def sota_updater(
    watchdog_results: dict[str, Any],
    benchmark_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """SOTA Updater — Model Registry自動更新

    SOTA WatchdogとBenchmarkerの結果をModel Registryに自動反映。
    """
    actions = []

    # 新モデル候補
    for model in watchdog_results.get("new_models", []):
        if model.get("estimated_score", 0) > 85:
            actions.append(f"register_candidate: {model['name']} (score: {model['estimated_score']})")

    # 劣化モデル
    for result in benchmark_results:
        if result.get("degraded"):
            actions.append(f"flag_degraded: {result['model_id']}")

    return {
        "actions": actions,
        "models_to_register": len([m for m in watchdog_results.get("new_models", []) if m.get("estimated_score", 0) > 85]),
        "models_degraded": len([r for r in benchmark_results if r.get("degraded")]),
    }
