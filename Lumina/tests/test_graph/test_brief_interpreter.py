"""brief_interpreter ノードのテスト"""

import pytest

from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.models.state import AssetType, GenerationStatus, LuminaState, QualityTier


@pytest.mark.asyncio
async def test_brief_interpreter_basic():
    """基本的なブリーフ解析"""
    state = LuminaState(
        brief="サイバーパンクな東京の夜景、ネオン輝くビル群",
        quality_tier=QualityTier.STANDARD,
    )
    result = await brief_interpreter(state)

    assert result["status"] == GenerationStatus.SELECTING
    assert result["brief_params"] is not None
    assert result["brief_params"].style == "cyberpunk"
    assert result["brief_params"].prompt != ""


@pytest.mark.asyncio
async def test_brief_interpreter_empty_brief():
    """空のブリーフはエラー"""
    state = LuminaState(brief="")
    result = await brief_interpreter(state)

    assert result["status"] == GenerationStatus.FAILED
    assert "error" in result


@pytest.mark.asyncio
async def test_brief_interpreter_japanese_keywords():
    """日本語キーワードでのスタイル検出"""
    test_cases = [
        ("水彩画風の風景", "watercolor"),
        ("アニメ風のキャラクター", "anime"),
        ("写実的なポートレート", "photorealistic"),
        ("レトロな雰囲気のポスター", "retro"),
        ("ミニマルなロゴデザイン", "minimalist"),
    ]

    for brief, expected_style in test_cases:
        state = LuminaState(brief=brief)
        result = await brief_interpreter(state)
        assert result["brief_params"].style == expected_style, f"Failed for: {brief}"


@pytest.mark.asyncio
async def test_brief_interpreter_mood_detection():
    """ムード検出"""
    state = LuminaState(brief="ダークで幻想的な森の風景")
    result = await brief_interpreter(state)

    assert result["brief_params"].mood == "dark"
