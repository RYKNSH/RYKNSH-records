"""Quality Fortress ノードのテスト"""

import pytest

from src.graph.nodes.quality.taste_engine import taste_engine
from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
from src.graph.nodes.quality.ai_escalation_chain import ai_escalation_chain
from src.models.state import (
    BriefParams,
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
    TasteScore,
)


# --- taste_engine ---

@pytest.mark.asyncio
async def test_taste_engine_basic():
    """基本的な審美評価"""
    state = LuminaState(
        brief="dramatic cyberpunk city",
        brief_params=BriefParams(prompt="dramatic cyberpunk city with neon lights"),
        generated_asset_url="https://example.com/test.png",
    )
    result = await taste_engine(state)

    assert result["status"] == GenerationStatus.EVALUATING
    assert result["taste_score"] is not None
    assert 0 <= result["taste_score"].aggregated <= 100
    assert result["taste_score"].composition > 0
    assert result["taste_score"].color > 0


@pytest.mark.asyncio
async def test_taste_engine_masterpiece_6_critics():
    """Masterpieceティアは6 Critic"""
    state = LuminaState(
        brief="masterpiece test",
        brief_params=BriefParams(prompt="epic dramatic masterpiece"),
        generated_asset_url="https://example.com/test.png",
        quality_tier=QualityTier.MASTERPIECE,
    )
    result = await taste_engine(state)

    assert result["taste_score"].ip_worldview > 0
    assert result["taste_score"].fan_expectation > 0


@pytest.mark.asyncio
async def test_taste_engine_no_asset():
    """生成物なしはエラー"""
    state = LuminaState(brief="test", generated_asset_url="")
    result = await taste_engine(state)
    assert result["status"] == GenerationStatus.FAILED


# --- quality_score_cascade ---

@pytest.mark.asyncio
async def test_cascade_pass():
    """品質基準を満たす場合→DELIVERING"""
    state = LuminaState(
        brief="test",
        taste_score=TasteScore(aggregated=90.0),
        quality_threshold=75.0,
        quality_tier=QualityTier.STANDARD,
    )
    result = await quality_score_cascade(state)
    assert result["status"] == GenerationStatus.DELIVERING


@pytest.mark.asyncio
async def test_cascade_fail_retry():
    """品質基準未達+リトライ可能→RETRYING"""
    state = LuminaState(
        brief="test",
        taste_score=TasteScore(aggregated=60.0),
        quality_threshold=75.0,
        quality_tier=QualityTier.STANDARD,
        retry_count=0,
        max_retries=3,
    )
    result = await quality_score_cascade(state)
    assert result["status"] == GenerationStatus.RETRYING
    assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_cascade_fail_escalate():
    """品質基準未達+リトライ上限→エスカレーション"""
    state = LuminaState(
        brief="test",
        taste_score=TasteScore(aggregated=60.0),
        quality_threshold=75.0,
        quality_tier=QualityTier.STANDARD,
        retry_count=3,
        max_retries=3,
    )
    result = await quality_score_cascade(state)
    assert result["status"] == GenerationStatus.RETRYING
    assert result["escalation_step"] == 1


@pytest.mark.asyncio
async def test_cascade_preview_always_pass():
    """Previewティアは無条件通過"""
    state = LuminaState(
        brief="test",
        taste_score=TasteScore(aggregated=10.0),
        quality_tier=QualityTier.PREVIEW,
    )
    result = await quality_score_cascade(state)
    assert result["status"] == GenerationStatus.DELIVERING


# --- ai_escalation_chain ---

@pytest.mark.asyncio
async def test_escalation_strategy_shift():
    """Step 1: Strategy Shift"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(prompt="test prompt"),
        taste_score=TasteScore(aggregated=60.0),
        quality_threshold=75.0,
        escalation_step=1,
    )
    result = await ai_escalation_chain(state)
    assert result["status"] == GenerationStatus.GENERATING
    assert result["escalation_step"] == 2


@pytest.mark.asyncio
async def test_escalation_tier_upgrade():
    """Step 2: Multi-Model Escalation（ティア昇格）"""
    state = LuminaState(
        brief="test",
        quality_tier=QualityTier.STANDARD,
        escalation_step=2,
    )
    result = await ai_escalation_chain(state)
    assert result["quality_tier"] == QualityTier.PREMIUM
    assert result["retry_count"] == 0  # リセット


@pytest.mark.asyncio
async def test_escalation_graceful_degradation():
    """Step 4: Graceful Degradation"""
    state = LuminaState(
        brief="test",
        taste_score=TasteScore(aggregated=60.0),
        quality_threshold=92.0,
        escalation_step=4,
    )
    result = await ai_escalation_chain(state)
    assert result["status"] == GenerationStatus.COMPLETED
    assert "alternatives" in result["generated_asset_metadata"]
    assert "message" in result["generated_asset_metadata"]
