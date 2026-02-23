"""Lumina API Server — FastAPI Production

Whitepaper Section 12: FastAPI エンドポイント
全ノード統合版 Graph 対応。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.models.state import AssetType, GenerationStatus, LuminaState, QualityTier
from src.registry.client import ModelRegistryClient
from src.config import config
from src.graph.lumina_graph import build_lumina_graph, get_graph_spec
from src.marketplace.style_packs import StylePackMarketplace

app = FastAPI(
    title="Lumina API",
    description="AI Creative Production — 世界最高峰のクリエイティブを全自動で",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルインスタンス
registry = ModelRegistryClient()
marketplace = StylePackMarketplace()

# Static files (Dashboard UI)
import pathlib
_static_dir = pathlib.Path(__file__).parent.parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def root():
    """Landing Page"""
    lp = _static_dir / "lp" / "index.html"
    if lp.exists():
        return FileResponse(str(lp))
    return {"message": "Lumina API — /docs for API documentation"}


@app.get("/lp/")
async def landing_page():
    """Landing Page (alias)"""
    lp = _static_dir / "lp" / "index.html"
    if lp.exists():
        return FileResponse(str(lp))
    return {"message": "LP not found"}


@app.get("/dashboard/")
async def dashboard():
    """SaaS Dashboard"""
    dash = _static_dir / "dashboard" / "index.html"
    if dash.exists():
        return FileResponse(str(dash))
    return {"message": "Dashboard not found"}


# ===============================
# Request / Response Models
# ===============================

class GenerateRequest(BaseModel):
    """生成リクエスト"""
    brief: str = Field(..., description="自然言語のクリエイティブブリーフ")
    quality_tier: str = Field(default="standard", description="品質ティア: preview/standard/premium/masterpiece")
    asset_type: str = Field(default="image", description="アセット種別: image/video/audio")
    tenant_id: str = Field(default="", description="テナントID")
    style_pack_id: Optional[str] = Field(default=None, description="適用するStylePackのID")


class GenerateResponse(BaseModel):
    """生成レスポンス"""
    request_id: str
    status: str
    asset_url: str = ""
    deliverable_url: str = ""
    model_used: str = ""
    quality_tier: str = ""
    taste_score: Optional[float] = None
    error: str = ""


class StylePackResponse(BaseModel):
    """StylePack レスポンス"""
    id: str
    name: str
    genre: str
    price: float
    downloads: int
    taste_score: float


# ===============================
# Endpoints
# ===============================

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """クリエイティブアセットを生成する

    全ノード統合パイプライン:
    Brief → Model Selection → Generation → Enhancement →
    Quality Check → Delivery
    """
    # バリデーション
    try:
        quality_tier = QualityTier(request.quality_tier)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効な品質ティア: {request.quality_tier}。有効値: preview/standard/premium/masterpiece",
        )

    try:
        asset_type = AssetType(request.asset_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効なアセット種別: {request.asset_type}。有効値: image/video/audio",
        )

    # StylePack 適用
    brief = request.brief
    if request.style_pack_id:
        pack_result = await marketplace.apply_pack(request.style_pack_id, brief)
        if "error" not in pack_result:
            brief = pack_result["prompt"]

    # ティア別閾値
    threshold_map = {
        QualityTier.PREVIEW: config.quality_threshold_preview,
        QualityTier.STANDARD: config.quality_threshold_standard,
        QualityTier.PREMIUM: config.quality_threshold_premium,
        QualityTier.MASTERPIECE: config.quality_threshold_masterpiece,
    }
    retry_map = {
        QualityTier.PREVIEW: config.retry_limit_preview,
        QualityTier.STANDARD: config.retry_limit_standard,
        QualityTier.PREMIUM: config.retry_limit_premium,
        QualityTier.MASTERPIECE: config.retry_limit_masterpiece,
    }

    initial_state = LuminaState(
        brief=brief,
        quality_tier=quality_tier,
        asset_type=asset_type,
        tenant_id=request.tenant_id,
        max_retries=retry_map[quality_tier],
        quality_threshold=float(threshold_map[quality_tier]),
    )

    # Graph実行（LangGraphが利用可能な場合のみ）
    try:
        graph = build_lumina_graph()
        if hasattr(graph, "ainvoke"):
            result = await graph.ainvoke(initial_state.model_dump())
        else:
            # LangGraph未インストール → ノード直接実行
            result = await _run_pipeline_direct(initial_state)
    except Exception as e:
        result = await _run_pipeline_direct(initial_state)

    taste_score = None
    if result.get("taste_score"):
        ts = result["taste_score"]
        taste_score = ts.aggregated if hasattr(ts, "aggregated") else ts.get("aggregated")

    return GenerateResponse(
        request_id=result.get("request_id", initial_state.request_id),
        status=result.get("status", "unknown").value if hasattr(result.get("status", ""), "value") else str(result.get("status", "unknown")),
        asset_url=result.get("generated_asset_url", ""),
        deliverable_url=result.get("deliverable_url", ""),
        model_used=result.get("generated_asset_metadata", {}).get("model_used", ""),
        quality_tier=request.quality_tier,
        taste_score=taste_score,
        error=result.get("error", ""),
    )


async def _run_pipeline_direct(state: LuminaState) -> dict:
    """LangGraph不在時のフォールバック: ノードを直接実行"""
    from src.graph.nodes.creation.brief_interpreter import brief_interpreter
    from src.graph.nodes.creation.model_selector import model_selector
    from src.graph.nodes.creation.generator import generator
    from src.graph.nodes.creation.enhancer_pipeline import enhancer_pipeline
    from src.graph.nodes.creation.multi_model_compositor import multi_model_compositor
    from src.graph.nodes.quality.taste_engine import taste_engine
    from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
    from src.graph.nodes.delivery.delivery_nodes import (
        format_optimizer, asset_packager, brand_consistency_check,
    )

    # Creation
    r = await brief_interpreter(state)
    state = state.model_copy(update=r)
    if state.status == GenerationStatus.FAILED:
        return state.model_dump()

    r = await model_selector(state, registry=registry)
    state = state.model_copy(update=r)

    r = await generator(state)
    state = state.model_copy(update=r)

    # Premium/Masterpiece → マルチモデル合成
    if state.quality_tier in (QualityTier.PREMIUM, QualityTier.MASTERPIECE):
        r = await multi_model_compositor(state)
        state = state.model_copy(update=r)

    r = await enhancer_pipeline(state)
    state = state.model_copy(update=r)

    # Quality
    r = await taste_engine(state)
    state = state.model_copy(update=r)

    r = await quality_score_cascade(state)
    state = state.model_copy(update=r)

    # Delivery (if passed quality)
    if state.status == GenerationStatus.DELIVERING:
        r = await format_optimizer(state)
        state = state.model_copy(update=r)
        r = await asset_packager(state)
        state = state.model_copy(update=r)
        r = await brand_consistency_check(state)
        state = state.model_copy(update=r)

    return state.model_dump()


@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "lumina",
        "version": "1.0.0",
        "api_mode": "real" if config.use_real_api else "stub",
        "providers": config.get_available_providers(),
    }


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


@app.get("/graph/spec")
async def graph_spec():
    """グラフ仕様を返す"""
    return get_graph_spec()


@app.get("/marketplace/packs")
async def list_style_packs(genre: Optional[str] = None):
    """StylePack一覧"""
    if genre:
        packs = await marketplace.list_packs(genre=genre)
    else:
        packs = await marketplace.list_packs()
    return {
        "packs": [
            StylePackResponse(
                id=p.id, name=p.name, genre=p.genre,
                price=p.price, downloads=p.downloads, taste_score=p.taste_score,
            ).model_dump()
            for p in packs
        ]
    }


@app.get("/config/status")
async def config_status():
    """API接続状態"""
    return {
        "supabase": config.has_supabase,
        "ada_api": config.has_ada,
        "openai": config.has_openai,
        "stability_ai": config.has_stability,
        "black_forest_labs": config.has_bfl,
        "use_real_api": config.use_real_api,
        "available_providers": config.get_available_providers(),
    }
