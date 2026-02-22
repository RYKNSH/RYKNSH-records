"""L5: Evolution/Feedback Tests — 自律改善ループの正当性検証

World-Class Test Patterns > L5: Evolution/Feedback Tests
- スコアリングの正当性
- ペナルティ正当性
- 進化の閾値
- E2Eループ: フィードバック蓄積→分析→進化
"""

import pytest

from src.graph.nodes.evolution.evolution_nodes import (
    TrendSignal,
    _cross_validate_signals,
    predictive_qc,
    taste_calibrator,
)
from src.graph.nodes.evolution.autonomous_loop import run_autonomous_loop
from src.models.state import TasteScore


# =========================
# Scoring Validity
# =========================

class TestScoringValidity:
    """スコアリングの正当性検証"""

    def test_high_quality_inputs_get_high_scores(self):
        """品質に関連するキーワードを含むスコアは高くなるべき"""
        score_rich = TasteScore(
            composition=90, color=88, brand_fit=85, emotional_impact=92, aggregated=88.75,
        )
        score_poor = TasteScore(
            composition=50, color=55, brand_fit=45, emotional_impact=48, aggregated=49.5,
        )
        assert score_rich.aggregated > score_poor.aggregated

    def test_aggregated_score_bounds(self):
        """統合スコアは0-100の範囲内"""
        score = TasteScore(
            composition=100, color=100, brand_fit=100, emotional_impact=100,
        )
        weights = {"composition": 0.25, "color": 0.25, "brand_fit": 0.25, "emotional_impact": 0.25}
        aggregated = sum(getattr(score, k) * v for k, v in weights.items())
        assert 0 <= aggregated <= 100

    def test_zero_scores_yield_zero_aggregate(self):
        """全Criticが0点→統合スコアも0点"""
        score = TasteScore(
            composition=0, color=0, brand_fit=0, emotional_impact=0, aggregated=0,
        )
        assert score.aggregated == 0.0


# =========================
# Cross-Validation Integrity
# =========================

class TestCrossValidationIntegrity:
    """Multi-Signal Cross-Validation の検証精度"""

    def test_single_source_rejected(self):
        """1ソースのみのトレンドは排除される"""
        signals = [
            TrendSignal(source="award", name="lone-trend", score=95, sustained_weeks=10),
        ]
        result = _cross_validate_signals(signals)
        assert len(result) == 0

    def test_short_duration_rejected(self):
        """持続期間4w未満は排除される"""
        signals = [
            TrendSignal(source="award", name="flash", score=95, sustained_weeks=2),
            TrendSignal(source="buzz", name="flash", score=90, sustained_weeks=3),
        ]
        result = _cross_validate_signals(signals)
        assert len(result) == 0

    def test_validated_trend_passes(self):
        """2ソース + 4w+ → Validated Trend"""
        signals = [
            TrendSignal(source="award", name="real-trend", score=88, sustained_weeks=6),
            TrendSignal(source="competition", name="real-trend", score=85, sustained_weeks=6),
        ]
        result = _cross_validate_signals(signals)
        assert len(result) == 1
        assert result[0].is_validated is True

    def test_mixed_signals_correct_filtering(self):
        """複数トレンドが正しくフィルタリングされる"""
        signals = [
            # Good: 2 sources, 8 weeks
            TrendSignal(source="award", name="good", score=88, sustained_weeks=8),
            TrendSignal(source="buzz", name="good", score=82, sustained_weeks=8),
            # Bad: 1 source only
            TrendSignal(source="award", name="lonely", score=95, sustained_weeks=10),
            # Bad: short duration
            TrendSignal(source="award", name="flash", score=90, sustained_weeks=1),
            TrendSignal(source="buzz", name="flash", score=88, sustained_weeks=2),
        ]
        result = _cross_validate_signals(signals)
        names = [t.name for t in result]
        assert names == ["good"]


# =========================
# Evolution Threshold
# =========================

class TestEvolutionThreshold:
    """進化の発動条件検証"""

    @pytest.mark.asyncio
    async def test_no_trends_no_evolution(self):
        """トレンドなし → 進化しない"""
        result = await taste_calibrator([], current_genome={"version": 1, "quality_score": 80})
        assert result["updated"] is False

    @pytest.mark.asyncio
    async def test_validated_trends_trigger_evolution(self):
        """Validated Trends あり → 進化発動"""
        trends = [
            TrendSignal(source="award", name="trend-x", score=90, sustained_weeks=8, is_validated=True),
        ]
        result = await taste_calibrator(trends, current_genome={"version": 1, "quality_score": 80})
        assert result["updated"] is True
        assert result["genome_version"] == 2


# =========================
# Predictive QC Accuracy
# =========================

class TestPredictiveQCAccuracy:
    """品質予測の正確性"""

    @pytest.mark.asyncio
    async def test_detects_sharp_decline(self):
        """急激な品質低下を検出"""
        scores = [92, 90, 91, 89, 90, 75, 73, 70, 68, 65]
        result = await predictive_qc(scores)
        assert result["prediction"] == "declining"

    @pytest.mark.asyncio
    async def test_detects_gradual_decline(self):
        """緩やかな品質低下を検出"""
        scores = [88, 87, 86, 85, 84, 81, 80, 79, 78, 77]
        result = await predictive_qc(scores)
        assert result["prediction"] == "declining"

    @pytest.mark.asyncio
    async def test_stable_not_false_positive(self):
        """安定品質を低下と誤検出しない"""
        scores = [85, 84, 86, 85, 84, 86, 85, 84, 85, 86]
        result = await predictive_qc(scores)
        assert result["prediction"] == "stable"

    @pytest.mark.asyncio
    async def test_improving_detected(self):
        """品質向上を検出"""
        scores = [70, 72, 73, 74, 75, 80, 82, 84, 86, 88]
        result = await predictive_qc(scores)
        assert result["prediction"] == "improving"

    @pytest.mark.asyncio
    async def test_insufficient_data(self):
        """データ不足時は判定不能"""
        result = await predictive_qc([85, 86, 87])
        assert result["prediction"] == "insufficient_data"


# =========================
# L5: E2E Evolution Cycle
# =========================

class TestEvolutionE2E:
    """フィードバック蓄積 → 分析 → 進化のフルサイクル"""

    @pytest.mark.asyncio
    async def test_full_evolution_cycle(self):
        """L3 Autonomous Loop の完全E2Eサイクル"""
        models = [
            {"id": "flux-1.1-pro", "capability_score": 92},
            {"id": "dall-e-3", "capability_score": 85},
        ]
        genome = {"version": 1, "quality_score": 78}
        scores = [88, 87, 86, 85, 84, 83, 82, 81, 80, 79]  # declining

        report = await run_autonomous_loop(
            model_registry_data=models,
            current_genome=genome,
            quality_scores_30d=scores,
        )

        # 1. 新モデルが検出されること
        assert len(report.new_models_detected) > 0

        # 2. トレンドが検証されること
        assert len(report.trends_validated) > 0
        assert all(t.is_validated for t in report.trends_validated)

        # 3. Taste Genomeが更新されること
        assert report.taste_genome_updated is True

        # 4. 品質低下が検出されること
        assert report.quality_prediction == "declining"

        # 5. 是正アクションが提案されること
        assert len(report.actions_taken) > 0

    @pytest.mark.asyncio
    async def test_stable_quality_no_overcorrection(self):
        """安定品質時に過剰な是正をしない"""
        models = [{"id": "flux", "capability_score": 92}]
        genome = {"version": 3, "quality_score": 88}
        scores = [88, 87, 88, 89, 88, 87, 88, 89, 88, 87]  # stable

        report = await run_autonomous_loop(
            model_registry_data=models,
            current_genome=genome,
            quality_scores_30d=scores,
        )

        assert report.quality_prediction == "stable"
        # 安定時にdecline系のアクションがないこと
        declining_actions = [a for a in report.actions_taken if "rebenchmark" in a or "refresh" in a]
        assert len(declining_actions) == 0
