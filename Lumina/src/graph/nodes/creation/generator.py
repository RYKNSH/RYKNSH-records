"""generator — 画像/映像生成ノード

選択されたモデルで実際にアセットを生成する。
Creation Layer の最終ノード（MS1時点）。

Whitepaper Section 6 > Creation Layer > generator:
「単一モデル生成 or マルチモデル合成。
 Premiumティア以上では複数モデルの出力をレイヤー合成して天井を突破」
"""

from __future__ import annotations

import uuid
from typing import Any

from src.models.state import GenerationStatus, LuminaState


# プロバイダーごとのAPI呼び出し関数（MVP: スタブ実装）
async def _call_openai(prompt: str, model_name: str) -> dict[str, Any]:
    """OpenAI (DALL-E) API 呼び出し"""
    # TODO: 本番実装 — openai.images.generate()
    return {
        "url": f"https://lumina-assets.example.com/generated/{uuid.uuid4()}.png",
        "model_used": model_name,
        "provider": "openai",
    }


async def _call_flux(prompt: str, model_name: str) -> dict[str, Any]:
    """Black Forest Labs (Flux) API 呼び出し"""
    # TODO: 本番実装 — httpx.post() to Flux API
    return {
        "url": f"https://lumina-assets.example.com/generated/{uuid.uuid4()}.png",
        "model_used": model_name,
        "provider": "black-forest-labs",
    }


async def _call_stability(prompt: str, model_name: str) -> dict[str, Any]:
    """Stability AI (SD XL) API 呼び出し"""
    # TODO: 本番実装 — stability_sdk
    return {
        "url": f"https://lumina-assets.example.com/generated/{uuid.uuid4()}.png",
        "model_used": model_name,
        "provider": "stability-ai",
    }


# プロバイダー→呼び出し関数のマッピング
PROVIDER_HANDLERS = {
    "openai": _call_openai,
    "black-forest-labs": _call_flux,
    "stability-ai": _call_stability,
}


async def generator(state: LuminaState) -> dict[str, Any]:
    """選択されたモデルでアセットを生成する

    model_selector で選択されたモデルの provider に応じて
    対応するAPI呼び出し関数を実行。
    """
    if state.model_selection is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": "モデルが未選択です（model_selectorを先に実行）",
        }

    if state.brief_params is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": "ブリーフパラメータが未設定です",
        }

    provider = state.model_selection.provider
    handler = PROVIDER_HANDLERS.get(provider)

    if handler is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": f"未対応のプロバイダー: {provider}",
        }

    try:
        result = await handler(
            prompt=state.brief_params.prompt,
            model_name=state.model_selection.model_name,
        )

        return {
            "generated_asset_url": result["url"],
            "generated_asset_metadata": {
                "model_used": result["model_used"],
                "provider": result["provider"],
                "prompt": state.brief_params.prompt,
                "quality_tier": state.quality_tier.value,
            },
            "status": GenerationStatus.COMPLETED,  # MS1ではQuality Fortress未実装のため直接完了
        }

    except Exception as e:
        return {
            "status": GenerationStatus.FAILED,
            "error": f"生成エラー: {str(e)}",
        }
