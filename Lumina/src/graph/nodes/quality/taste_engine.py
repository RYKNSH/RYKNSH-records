"""taste_engine — Multi-Critic Ensemble 審美評価ノード

Whitepaper Section 8: Taste Engine 詳細
4つのCritic（構図/色彩/ブランド適合/感情インパクト）を並列実行し、
重み付き統合スコアを算出する。Masterpieceティアでは追加2 Criticが有効化。
"""

from __future__ import annotations

import random
from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier, TasteScore


# デフォルトのCritic重み
DEFAULT_CRITIC_WEIGHTS = {
    "composition": 0.25,
    "color": 0.25,
    "brand_fit": 0.25,
    "emotional_impact": 0.25,
}

# Masterpieceティアの拡張Critic重み（6 Critic）
MASTERPIECE_CRITIC_WEIGHTS = {
    "composition": 0.20,
    "color": 0.15,
    "brand_fit": 0.20,
    "emotional_impact": 0.15,
    "ip_worldview": 0.15,
    "fan_expectation": 0.15,
}


async def _critic_composition(asset_url: str, prompt: str) -> float:
    """Critic A: 構図・レイアウト評価

    本番: Vision LLM で構図分析
    MVP: プロンプトの構図指示の有無からスコアリング
    """
    composition_keywords = [
        "centered", "symmetr", "rule of thirds", "golden ratio",
        "panoram", "close-up", "wide shot", "aerial",
        "中央", "対称", "パノラマ", "クローズアップ",
    ]
    base_score = 70.0
    for kw in composition_keywords:
        if kw in prompt.lower():
            base_score += 5.0
    return min(base_score + random.uniform(-5, 10), 100.0)


async def _critic_color(asset_url: str, prompt: str) -> float:
    """Critic B: 色彩・トーン評価

    本番: カラーヒストグラム分析 + Vision LLM
    MVP: プロンプトの色彩指示からスコアリング
    """
    color_keywords = [
        "vibrant", "neon", "pastel", "monochrome", "gradient",
        "warm", "cool", "contrast", "鮮やか", "ネオン", "グラデーション",
    ]
    base_score = 72.0
    for kw in color_keywords:
        if kw in prompt.lower():
            base_score += 4.0
    return min(base_score + random.uniform(-5, 10), 100.0)


async def _critic_brand_fit(asset_url: str, prompt: str, reference_context: str = "") -> float:
    """Critic C: ブランド適合度評価

    本番: Reference Set (pgvector) との Cosine Similarity
    MVP: 参照コンテキストの有無からスコアリング
    """
    base_score = 68.0
    if reference_context:
        base_score += 15.0
    return min(base_score + random.uniform(-3, 8), 100.0)


async def _critic_emotional_impact(asset_url: str, prompt: str) -> float:
    """Critic D: 感情インパクト評価

    本番: Vision LLM による感情分析 + A/Bテストデータ
    MVP: プロンプトの感情的要素からスコアリング
    """
    emotion_keywords = [
        "dramatic", "epic", "haunting", "serene", "powerful",
        "mysterious", "joyful", "ドラマチック", "壮大", "幻想的",
    ]
    base_score = 70.0
    for kw in emotion_keywords:
        if kw in prompt.lower():
            base_score += 5.0
    return min(base_score + random.uniform(-5, 12), 100.0)


async def _critic_ip_worldview(asset_url: str, prompt: str) -> float:
    """Critic E: IP世界観適合度（Masterpieceティアのみ）"""
    return 75.0 + random.uniform(-5, 15)


async def _critic_fan_expectation(asset_url: str, prompt: str) -> float:
    """Critic F: ファン期待値（Masterpieceティアのみ）"""
    return 73.0 + random.uniform(-5, 15)


async def taste_engine(state: LuminaState) -> dict[str, Any]:
    """Multi-Critic Ensemble 審美評価

    全Criticを並列実行し、品質ティアに応じた重みで統合スコアを算出。
    """
    if not state.generated_asset_url:
        return {
            "status": GenerationStatus.FAILED,
            "error": "生成物URLがありません（generatorを先に実行）",
        }

    prompt = state.brief_params.prompt if state.brief_params else state.brief
    reference_context = state.brief_params.reference_context if state.brief_params else ""

    # 4 Critic を並列実行（MVP: 擬似並列）
    composition_score = await _critic_composition(state.generated_asset_url, prompt)
    color_score = await _critic_color(state.generated_asset_url, prompt)
    brand_score = await _critic_brand_fit(state.generated_asset_url, prompt, reference_context)
    impact_score = await _critic_emotional_impact(state.generated_asset_url, prompt)

    taste_score = TasteScore(
        composition=round(composition_score, 1),
        color=round(color_score, 1),
        brand_fit=round(brand_score, 1),
        emotional_impact=round(impact_score, 1),
    )

    # Masterpieceティア: 追加2 Critic
    if state.quality_tier == QualityTier.MASTERPIECE:
        weights = MASTERPIECE_CRITIC_WEIGHTS
        taste_score.ip_worldview = round(await _critic_ip_worldview(state.generated_asset_url, prompt), 1)
        taste_score.fan_expectation = round(await _critic_fan_expectation(state.generated_asset_url, prompt), 1)

        taste_score.aggregated = round(
            taste_score.composition * weights["composition"]
            + taste_score.color * weights["color"]
            + taste_score.brand_fit * weights["brand_fit"]
            + taste_score.emotional_impact * weights["emotional_impact"]
            + taste_score.ip_worldview * weights["ip_worldview"]
            + taste_score.fan_expectation * weights["fan_expectation"],
            1,
        )
    else:
        weights = DEFAULT_CRITIC_WEIGHTS
        taste_score.aggregated = round(
            taste_score.composition * weights["composition"]
            + taste_score.color * weights["color"]
            + taste_score.brand_fit * weights["brand_fit"]
            + taste_score.emotional_impact * weights["emotional_impact"],
            1,
        )

    return {
        "taste_score": taste_score,
        "status": GenerationStatus.EVALUATING,
    }
