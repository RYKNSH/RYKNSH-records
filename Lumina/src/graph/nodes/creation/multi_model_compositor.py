"""multi_model_compositor — マルチモデル合成ノード (MS5)

Whitepaper Section 6 / Round 3:
単一モデルの天井をマルチモデルの合成で突破する。
Premiumティア以上で有効。
"""

from __future__ import annotations

import uuid
from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier


async def multi_model_compositor(state: LuminaState) -> dict[str, Any]:
    """マルチモデル合成

    Premium/Masterpiece のみ実行。
    複数モデルの出力をレイヤー合成して天井を突破する。
    """
    if state.quality_tier not in (QualityTier.PREMIUM, QualityTier.MASTERPIECE):
        return {}  # Standard以下はスキップ

    if not state.generated_asset_url:
        return {
            "status": GenerationStatus.FAILED,
            "error": "ベース生成物がありません",
        }

    # マルチモデル合成シミュレーション
    composite_layers = {
        "base": {"model": state.model_selection.model_name if state.model_selection else "unknown", "role": "composition"},
        "detail": {"model": "SD XL Turbo", "role": "texture_detail"},
        "text": {"model": "DALL-E 3", "role": "text_rendering"},
    }

    composite_url = f"https://lumina-assets.example.com/composite/{uuid.uuid4()}.png"

    return {
        "generated_asset_url": composite_url,
        "generated_asset_metadata": {
            **state.generated_asset_metadata,
            "multi_model": True,
            "composite_layers": composite_layers,
        },
    }
