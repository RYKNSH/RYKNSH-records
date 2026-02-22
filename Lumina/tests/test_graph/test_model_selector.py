"""model_selector ノードのテスト"""

import pytest

from src.graph.nodes.creation.model_selector import model_selector
from src.models.state import (
    AssetType,
    BriefParams,
    GenerationStatus,
    LuminaState,
    QualityTier,
)
from src.registry.client import ModelRegistryClient


@pytest.mark.asyncio
async def test_model_selector_basic():
    """基本的なモデル選択"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(
            subject="test", style="general", mood="neutral", prompt="test prompt"
        ),
        quality_tier=QualityTier.STANDARD,
    )
    registry = ModelRegistryClient()  # seed データ使用

    result = await model_selector(state, registry=registry)

    assert result["status"] == GenerationStatus.GENERATING
    assert result["model_selection"] is not None
    assert result["model_selection"].model_id != ""
    assert result["model_selection"].capability_score > 0


@pytest.mark.asyncio
async def test_model_selector_preview_cost_limit():
    """Previewティアはコスト制限あり"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(
            subject="test", style="general", mood="neutral", prompt="test prompt"
        ),
        quality_tier=QualityTier.PREVIEW,
    )
    registry = ModelRegistryClient()

    result = await model_selector(state, registry=registry)

    assert result["status"] == GenerationStatus.GENERATING
    assert result["model_selection"].cost_per_call <= 0.02


@pytest.mark.asyncio
async def test_model_selector_artistic_style():
    """アーティスティックスタイルの最適モデル選択"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(
            subject="test", style="artistic", mood="neutral", prompt="test prompt"
        ),
        quality_tier=QualityTier.PREMIUM,
    )
    registry = ModelRegistryClient()

    result = await model_selector(state, registry=registry)

    assert result["status"] == GenerationStatus.GENERATING
    assert result["model_selection"] is not None


@pytest.mark.asyncio
async def test_model_selector_no_brief_params():
    """BriefParams未設定はエラー"""
    state = LuminaState(brief="test", brief_params=None)
    registry = ModelRegistryClient()

    result = await model_selector(state, registry=registry)

    assert result["status"] == GenerationStatus.FAILED
