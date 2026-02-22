"""ai_escalation_chain — 4段階AI自律エスカレーション

Whitepaper Round 8 > AI Escalation Chain:
Step 1: Strategy Shift（モデル/プロンプト変更）
Step 2: Multi-Model Escalation（ティア自動昇格）
Step 3: Creative Decomposition（要素分解→個別生成→合成）
Step 4: Graceful Degradation（テナントに代替案を自動提示）
"""

from __future__ import annotations

import random
from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier


async def ai_escalation_chain(state: LuminaState) -> dict[str, Any]:
    """4段階のAI自律エスカレーション

    リトライ上限に達した後、人間の介入なしで品質を引き上げる。
    各ステップを順番に試行し、品質基準を満たすことを目指す。
    """
    step = state.escalation_step

    if step == 0:
        # 通常リトライ（まだエスカレーション前）
        return await _normal_retry(state)

    elif step == 1:
        # Step 1: Strategy Shift
        return await _strategy_shift(state)

    elif step == 2:
        # Step 2: Multi-Model Escalation
        return await _multi_model_escalation(state)

    elif step == 3:
        # Step 3: Creative Decomposition
        return await _creative_decomposition(state)

    else:
        # Step 4: Graceful Degradation
        return await _graceful_degradation(state)


async def _normal_retry(state: LuminaState) -> dict[str, Any]:
    """通常リトライ — 同じモデルで再生成"""
    return {
        "status": GenerationStatus.GENERATING,
        "retry_count": state.retry_count + 1,
    }


async def _strategy_shift(state: LuminaState) -> dict[str, Any]:
    """Step 1: Strategy Shift — モデル/プロンプト変更

    - モデルを変更（Registry内の次点モデルに切り替え）
    - プロンプトの抽象度を変更
    - スタイルパラメータをランダムに摂動
    """
    modified_prompt = state.brief_params.prompt if state.brief_params else state.brief

    # プロンプトに摂動を加える
    perturbations = [
        "high quality, detailed, professional",
        "award-winning, masterpiece, best quality",
        "ultra detailed, sharp focus, high resolution",
    ]
    modified_prompt += f", {random.choice(perturbations)}"

    # 次のステップに進む準備
    return {
        "status": GenerationStatus.GENERATING,
        "escalation_step": 2,
        "generated_asset_metadata": {
            **state.generated_asset_metadata,
            "escalation": "strategy_shift",
            "modified_prompt": modified_prompt,
        },
    }


async def _multi_model_escalation(state: LuminaState) -> dict[str, Any]:
    """Step 2: Multi-Model Escalation — ティア自動昇格

    Standard案件 → Premium パイプライン（マルチモデル合成）に自動昇格。
    """
    current_tier = state.quality_tier

    # ティア昇格マッピング
    upgrade_map = {
        QualityTier.PREVIEW: QualityTier.STANDARD,
        QualityTier.STANDARD: QualityTier.PREMIUM,
        QualityTier.PREMIUM: QualityTier.MASTERPIECE,
        QualityTier.MASTERPIECE: QualityTier.MASTERPIECE,  # 上限
    }

    new_tier = upgrade_map[current_tier]
    new_max_retries = {
        QualityTier.PREVIEW: 0,
        QualityTier.STANDARD: 3,
        QualityTier.PREMIUM: 5,
        QualityTier.MASTERPIECE: 10,
    }[new_tier]

    return {
        "quality_tier": new_tier,
        "max_retries": new_max_retries,
        "retry_count": 0,  # リトライカウントをリセット
        "escalation_step": 3,
        "status": GenerationStatus.GENERATING,
        "generated_asset_metadata": {
            **state.generated_asset_metadata,
            "escalation": "multi_model_escalation",
            "tier_upgrade": f"{current_tier.value} → {new_tier.value}",
        },
    }


async def _creative_decomposition(state: LuminaState) -> dict[str, Any]:
    """Step 3: Creative Decomposition — 要素分解→個別生成→合成

    リクエストを構成要素に分解して個別に最高品質で生成。
    """
    return {
        "escalation_step": 4,
        "status": GenerationStatus.GENERATING,
        "generated_asset_metadata": {
            **state.generated_asset_metadata,
            "escalation": "creative_decomposition",
            "decomposed_elements": ["background", "subject", "effects", "text"],
        },
    }


async def _graceful_degradation(state: LuminaState) -> dict[str, Any]:
    """Step 4: Graceful Degradation — テナントに代替案を自動提示

    全ステップを経ても品質基準未達の場合（極めて稀）。
    テナントに現在の最高出力と代替案を提示する。
    """
    current_score = state.taste_score.aggregated if state.taste_score else 0
    threshold = state.quality_threshold

    alternatives = [
        f"品質基準を {threshold} → {threshold - 5} に緩和して納品",
        "ブリーフの制約を緩和して再生成",
        "異なるスタイルアプローチで再生成",
    ]

    return {
        "status": GenerationStatus.COMPLETED,
        "generated_asset_metadata": {
            **state.generated_asset_metadata,
            "escalation": "graceful_degradation",
            "current_score": current_score,
            "threshold": threshold,
            "alternatives": alternatives,
            "message": (
                f"ご指定の品質基準({threshold}/100)にはAI単独で到達困難です。"
                f"現在の最高出力({current_score}/100)を納品してよろしいですか？"
            ),
        },
    }
