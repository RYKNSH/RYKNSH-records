"""taste_engine — Multi-Critic Ensemble 審美評価ノード (Production版)

Whitepaper Section 8: Taste Engine 詳細
4つのCritic（構図/色彩/ブランド適合/感情インパクト）を並列実行し、
重み付き統合スコアを算出する。Masterpieceティアでは追加2 Criticが有効化。

Production: Ada Core API (Vision LLM) 経由で審美評価。
Fallback: キーワードベースのルールスコアリング。
"""

from __future__ import annotations

import random
from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier, TasteScore
from src.config import config


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


# =========================================
# Vision LLM 評価 (Ada Core API)
# =========================================

async def _evaluate_via_ada(
    asset_url: str, prompt: str, critic_name: str, reference_context: str = ""
) -> float:
    """Ada Core API の Vision LLM を使って審美評価を実行

    Ada API の /chat エンドポイントに画像URLとPromptを送り、
    0-100のスコアを返させる。
    """
    if not config.use_real_api or not config.has_ada:
        return -1.0  # -1 = フォールバック使用

    import httpx

    evaluation_prompt = _build_critic_prompt(critic_name, prompt, reference_context)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config.ada_api_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.ada_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": asset_url},
                                },
                                {
                                    "type": "text",
                                    "text": evaluation_prompt,
                                },
                            ],
                        }
                    ],
                    "max_tokens": 50,
                },
            )
            response.raise_for_status()
            data = response.json()
            score_text = data["choices"][0]["message"]["content"].strip()

            # 数値部分を抽出
            import re
            match = re.search(r'\d+(?:\.\d+)?', score_text)
            if match:
                score = float(match.group())
                return min(max(score, 0.0), 100.0)

    except Exception:
        pass

    return -1.0  # フォールバック


def _build_critic_prompt(critic_name: str, prompt: str, reference_context: str) -> str:
    """各Criticの評価プロンプトを生成"""
    base = f"この画像を'{prompt}'というリクエストに対する成果物として評価してください。"

    critic_prompts = {
        "composition": f"{base}\n構図・レイアウトの品質を0-100で採点してください。三分割法、黄金比、視覚的バランスを考慮。数値のみ回答。",
        "color": f"{base}\n色彩・トーンの品質を0-100で採点してください。色の調和、コントラスト、雰囲気の適切さを考慮。数値のみ回答。",
        "brand_fit": f"{base}\nブランド適合度を0-100で採点してください。{f'参考: {reference_context}' if reference_context else 'プロフェッショナルな品質基準'}。数値のみ回答。",
        "emotional_impact": f"{base}\n感情的インパクトを0-100で採点してください。視覚的な印象の強さ、記憶に残るか、感情を動かすかを考慮。数値のみ回答。",
        "ip_worldview": f"{base}\nIP世界観との整合性を0-100で採点してください。独自の世界観が表現されているか。数値のみ回答。",
        "fan_expectation": f"{base}\nファン・ターゲット層の期待に応えているかを0-100で採点してください。数値のみ回答。",
    }

    return critic_prompts.get(critic_name, f"{base}\n総合品質を0-100で採点。数値のみ回答。")


# =========================================
# ルールベース評価 (フォールバック)
# =========================================

async def _critic_composition(asset_url: str, prompt: str) -> float:
    """Critic A: 構図・レイアウト評価"""
    # まずVision LLMを試行
    score = await _evaluate_via_ada(asset_url, prompt, "composition")
    if score >= 0:
        return score

    # フォールバック: キーワードベース
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
    """Critic B: 色彩・トーン評価"""
    score = await _evaluate_via_ada(asset_url, prompt, "color")
    if score >= 0:
        return score

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
    """Critic C: ブランド適合度評価"""
    score = await _evaluate_via_ada(asset_url, prompt, "brand_fit", reference_context)
    if score >= 0:
        return score

    base_score = 68.0
    if reference_context:
        base_score += 15.0
    return min(base_score + random.uniform(-3, 8), 100.0)


async def _critic_emotional_impact(asset_url: str, prompt: str) -> float:
    """Critic D: 感情インパクト評価"""
    score = await _evaluate_via_ada(asset_url, prompt, "emotional_impact")
    if score >= 0:
        return score

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
    score = await _evaluate_via_ada(asset_url, prompt, "ip_worldview")
    if score >= 0:
        return score
    return 75.0 + random.uniform(-5, 15)


async def _critic_fan_expectation(asset_url: str, prompt: str) -> float:
    """Critic F: ファン期待値（Masterpieceティアのみ）"""
    score = await _evaluate_via_ada(asset_url, prompt, "fan_expectation")
    if score >= 0:
        return score
    return 73.0 + random.uniform(-5, 15)


# =========================================
# メインエントリーポイント
# =========================================

async def taste_engine(state: LuminaState) -> dict[str, Any]:
    """Multi-Critic Ensemble 審美評価

    全Criticを並列実行し、品質ティアに応じた重みで統合スコアを算出。
    Ada API が利用可能な場合は Vision LLM で評価。
    利用不可の場合はキーワードベースのフォールバック。
    """
    if not state.generated_asset_url:
        return {
            "status": GenerationStatus.FAILED,
            "error": "生成物URLがありません（generatorを先に実行）",
        }

    prompt = state.brief_params.prompt if state.brief_params else state.brief
    reference_context = state.brief_params.reference_context if state.brief_params else ""

    # 4 Critic を実行
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
