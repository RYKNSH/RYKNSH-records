"""generator ノードのテスト"""

import pytest

from src.graph.nodes.creation.generator import generator
from src.models.state import (
    BriefParams,
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
)


@pytest.mark.asyncio
async def test_generator_basic():
    """基本的な生成"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(
            subject="test", style="general", mood="neutral", prompt="A cyberpunk city"
        ),
        model_selection=ModelSelection(
            model_id="flux-1.1-pro",
            model_name="Flux 1.1 Pro",
            provider="black-forest-labs",
            capability_score=92,
            cost_per_call=0.04,
            selection_reason="test",
        ),
    )

    result = await generator(state)

    assert result["status"] == GenerationStatus.COMPLETED
    assert result["generated_asset_url"] != ""
    assert result["generated_asset_metadata"]["provider"] == "black-forest-labs"


@pytest.mark.asyncio
async def test_generator_openai():
    """OpenAI プロバイダーでの生成"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(prompt="test prompt"),
        model_selection=ModelSelection(
            model_id="dall-e-3",
            model_name="DALL-E 3",
            provider="openai",
            capability_score=85,
            cost_per_call=0.04,
            selection_reason="test",
        ),
    )

    result = await generator(state)
    assert result["status"] == GenerationStatus.COMPLETED
    assert result["generated_asset_metadata"]["provider"] == "openai"


@pytest.mark.asyncio
async def test_generator_no_model_selection():
    """モデル未選択はエラー"""
    state = LuminaState(brief="test", model_selection=None)
    result = await generator(state)
    assert result["status"] == GenerationStatus.FAILED


@pytest.mark.asyncio
async def test_generator_unknown_provider():
    """未知のプロバイダーはエラー"""
    state = LuminaState(
        brief="test",
        brief_params=BriefParams(prompt="test"),
        model_selection=ModelSelection(
            model_id="unknown",
            model_name="Unknown",
            provider="nonexistent-provider",
            capability_score=0,
            cost_per_call=0,
            selection_reason="test",
        ),
    )

    result = await generator(state)
    assert result["status"] == GenerationStatus.FAILED
