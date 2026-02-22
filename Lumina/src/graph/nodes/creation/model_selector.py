"""model_selector — モデル選択ノード

タスクの性質 × 品質ティア × コスト制約から最適モデルを動的に選択する。
Model Registry のcapability_scoreベース。

Whitepaper Section 6 > Creation Layer > model_selector:
「タスク性質（リアリスティック/アート/アニメ）× 品質ティア × コスト制約から
 最適なモデルを動的に選択。Model Registryのcapability_scoreベース」
"""

from __future__ import annotations

from typing import Any

from src.models.state import (
    GenerationStatus,
    LuminaState,
    ModelSelection,
    QualityTier,
)
from src.registry.client import ModelRegistryClient


# 品質ティアごとのコスト上限
TIER_COST_LIMITS = {
    QualityTier.PREVIEW: 0.02,
    QualityTier.STANDARD: 0.10,
    QualityTier.PREMIUM: None,  # 制限なし
    QualityTier.MASTERPIECE: None,
}

# スタイル→タスクスタイルのマッピング
STYLE_TO_TASK_STYLE = {
    "photorealistic": "photorealistic",
    "写実": "photorealistic",
    "anime": "anime",
    "アニメ": "anime",
    "artistic": "artistic",
    "watercolor": "artistic",
    "cyberpunk": "artistic",
    "minimalist": "general",
    "retro": "artistic",
    "general": "general",
}


async def model_selector(
    state: LuminaState,
    registry: ModelRegistryClient | None = None,
) -> dict[str, Any]:
    """最適なモデルを選択する

    brief_interpreter で解析されたスタイル情報と
    品質ティアからModel Registryの最適モデルを選択。
    """
    if state.brief_params is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": "ブリーフパラメータが未設定です（brief_interpreterを先に実行）",
        }

    if registry is None:
        registry = ModelRegistryClient()

    # スタイルからタスクスタイルを決定
    task_style = STYLE_TO_TASK_STYLE.get(state.brief_params.style, "general")

    # コスト上限
    max_cost = TIER_COST_LIMITS.get(state.quality_tier)

    # Model Registry から最適モデルを取得
    best_model = await registry.get_best_model(
        model_type=state.asset_type.value,
        task_style=task_style,
        max_cost=max_cost,
    )

    if best_model is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": f"条件に合うモデルが見つかりません（type={state.asset_type}, style={task_style}）",
        }

    selection = ModelSelection(
        model_id=best_model.id,
        model_name=best_model.model_name,
        provider=best_model.provider,
        capability_score=best_model.capability_score,
        cost_per_call=best_model.cost_per_call,
        selection_reason=(
            f"task_style={task_style}, "
            f"tier={state.quality_tier.value}, "
            f"score={best_model.capability_score}"
        ),
    )

    return {
        "model_selection": selection,
        "status": GenerationStatus.GENERATING,
    }
