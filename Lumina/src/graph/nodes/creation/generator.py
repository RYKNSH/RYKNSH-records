"""generator — 画像/映像生成ノード（Production版）

選択されたモデルで実際にアセットを生成する。
LUMINA_USE_REAL_API=true の場合は実APIを呼び出し、
false の場合はスタブデータを返す。

対応プロバイダー:
- Black Forest Labs (Flux) — httpx POST to api.bfl.ml
- OpenAI (DALL-E 3) — openai SDK
- Stability AI (SDXL) — stability_sdk
"""

from __future__ import annotations

import base64
import uuid
from typing import Any

from src.models.state import GenerationStatus, LuminaState
from src.config import config


# =========================================
# プロバイダーごとのAPI呼び出し関数
# =========================================

async def _call_flux(prompt: str, model_name: str) -> dict[str, Any]:
    """Black Forest Labs (Flux) API 呼び出し"""
    if not config.use_real_api or not config.has_bfl:
        return _stub_result(prompt, model_name, "black-forest-labs")

    import httpx

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.bfl.ml/v1/flux-pro-1.1",
            headers={
                "Content-Type": "application/json",
                "x-key": config.bfl_api_key,
            },
            json={
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "safety_tolerance": 2,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Flux は非同期生成。request_id で結果をポーリング
        request_id = data.get("id")
        if request_id:
            result_url = await _poll_flux_result(client, request_id)
        else:
            result_url = data.get("sample", data.get("image", ""))

    return {
        "url": result_url,
        "model_used": model_name,
        "provider": "black-forest-labs",
    }


async def _poll_flux_result(client, request_id: str, max_attempts: int = 30) -> str:
    """Flux の非同期結果をポーリング"""
    import asyncio

    for _ in range(max_attempts):
        response = await client.get(
            f"https://api.bfl.ml/v1/get_result?id={request_id}",
            headers={"x-key": config.bfl_api_key},
        )
        data = response.json()
        status = data.get("status")

        if status == "Ready":
            return data.get("result", {}).get("sample", "")
        elif status in ("Error", "Content Moderated"):
            raise RuntimeError(f"Flux generation failed: {status}")

        await asyncio.sleep(2)

    raise TimeoutError("Flux generation timed out")


async def _call_openai(prompt: str, model_name: str) -> dict[str, Any]:
    """OpenAI (DALL-E 3) API 呼び出し"""
    if not config.use_real_api or not config.has_openai:
        return _stub_result(prompt, model_name, "openai")

    import openai

    client = openai.AsyncOpenAI(api_key=config.openai_api_key)
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1,
    )

    return {
        "url": response.data[0].url,
        "model_used": model_name,
        "provider": "openai",
        "revised_prompt": response.data[0].revised_prompt,
    }


async def _call_stability(prompt: str, model_name: str) -> dict[str, Any]:
    """Stability AI (SDXL) API 呼び出し"""
    if not config.use_real_api or not config.has_stability:
        return _stub_result(prompt, model_name, "stability-ai")

    import httpx

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "Authorization": f"Bearer {config.stability_api_key}",
                "Accept": "application/json",
            },
            files={"none": ""},
            data={
                "prompt": prompt,
                "output_format": "png",
                "aspect_ratio": "1:1",
            },
        )
        response.raise_for_status()
        data = response.json()

        # Base64画像をURL形式で返す（本番ではS3/R2にアップロード）
        image_b64 = data.get("image", "")
        # 本番: S3/R2にアップロードしてURLを返す
        url = f"data:image/png;base64,{image_b64[:100]}..."  # 短縮

    return {
        "url": url,
        "model_used": model_name,
        "provider": "stability-ai",
    }


def _stub_result(prompt: str, model_name: str, provider: str) -> dict[str, Any]:
    """テスト/開発用スタブ結果"""
    return {
        "url": f"https://lumina-assets.example.com/generated/{uuid.uuid4()}.png",
        "model_used": model_name,
        "provider": provider,
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
                "api_mode": "real" if config.use_real_api else "stub",
            },
            "status": GenerationStatus.COMPLETED,
        }

    except Exception as e:
        return {
            "status": GenerationStatus.FAILED,
            "error": f"生成エラー: {str(e)}",
        }
