"""Lumina API Server — FastAPI

Whitepaper Section 12: FastAPI エンドポイント
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

from src.graph.lumina_graph import compile_lumina_graph
from src.models.state import AssetType, LuminaState, QualityTier
from src.registry.client import ModelRegistryClient

app = FastAPI(
    title="Lumina API",
    description="AI Creative Production — 世界最高峰のクリエイティブを全自動で",
    version="0.1.0",
)

# グローバルインスタンス
registry = ModelRegistryClient()
compiled_graph = compile_lumina_graph(registry)


class GenerateRequest(BaseModel):
    """生成リクエスト"""

    brief: str = Field(..., description="自然言語のクリエイティブブリーフ")
    quality_tier: str = Field(default="standard", description="品質ティア: preview/standard/premium/masterpiece")
    asset_type: str = Field(default="image", description="アセット種別: image/video/audio")
    tenant_id: str = Field(default="", description="テナントID")


class GenerateResponse(BaseModel):
    """生成レスポンス"""

    request_id: str
    status: str
    asset_url: str = ""
    model_used: str = ""
    quality_tier: str = ""
    error: str = ""


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """クリエイティブアセットを生成する

    POST /generate
    {
        "brief": "サイバーパンクな東京の夜景、ネオン輝く",
        "quality_tier": "standard",
        "asset_type": "image"
    }
    """
    try:
        quality_tier = QualityTier(request.quality_tier)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効な品質ティア: {request.quality_tier}. 有効値: preview/standard/premium/masterpiece",
        )

    try:
        asset_type = AssetType(request.asset_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効なアセット種別: {request.asset_type}. 有効値: image/video/audio",
        )

    initial_state = LuminaState(
        brief=request.brief,
        quality_tier=quality_tier,
        asset_type=asset_type,
        tenant_id=request.tenant_id,
        max_retries=LuminaState(quality_tier=quality_tier).get_max_retries_for_tier(),
        quality_threshold=LuminaState(quality_tier=quality_tier).get_quality_threshold_for_tier(),
    )

    result = await compiled_graph.ainvoke(initial_state.model_dump())

    return GenerateResponse(
        request_id=result.get("request_id", ""),
        status=result.get("status", "unknown"),
        asset_url=result.get("generated_asset_url", ""),
        model_used=result.get("generated_asset_metadata", {}).get("model_used", ""),
        quality_tier=request.quality_tier,
        error=result.get("error", ""),
    )


@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok", "service": "lumina", "version": "0.1.0"}


@app.get("/models")
async def list_models():
    """利用可能なモデル一覧"""
    models = await registry.get_active_models()
    return {
        "models": [
            {
                "id": m.id,
                "name": m.model_name,
                "provider": m.provider,
                "capability_score": m.capability_score,
                "cost_per_call": m.cost_per_call,
            }
            for m in models
        ]
    }
