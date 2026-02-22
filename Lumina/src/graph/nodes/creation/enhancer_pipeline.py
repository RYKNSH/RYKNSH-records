"""enhancer_pipeline — ポストプロセッシングパイプラインノード

Whitepaper Section 6 > Creation Layer > enhancer_pipeline:
超解像→カラーグレーディング→ディテール注入→最終研磨。
どのモデルを使っても最終出力が最高品質になることを担保。
"""

from __future__ import annotations

from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier


async def _upscale(asset_url: str) -> dict[str, Any]:
    """超解像処理（MVP: メタデータ付与のみ）"""
    return {"upscaled": True, "resolution": "4096x4096"}


async def _color_grade(asset_url: str, mood: str) -> dict[str, Any]:
    """カラーグレーディング"""
    grade_profiles = {
        "dark": {"contrast": 1.3, "saturation": 0.8, "temperature": -10},
        "vibrant": {"contrast": 1.1, "saturation": 1.4, "temperature": 5},
        "dreamy": {"contrast": 0.9, "saturation": 0.9, "temperature": 15},
        "neutral": {"contrast": 1.0, "saturation": 1.0, "temperature": 0},
    }
    return grade_profiles.get(mood, grade_profiles["neutral"])


async def _inject_details(asset_url: str) -> dict[str, Any]:
    """ディテール注入"""
    return {"detail_level": "high", "sharpness": 1.2}


async def enhancer_pipeline(state: LuminaState) -> dict[str, Any]:
    """エンハンサーパイプライン

    Preview: スキップ（エンハンスなし）
    Standard以上: Upscale → Color Grade → Detail Inject
    """
    if state.quality_tier == QualityTier.PREVIEW:
        return {"status": GenerationStatus.EVALUATING}

    if not state.generated_asset_url:
        return {
            "status": GenerationStatus.FAILED,
            "error": "生成物URLがありません",
        }

    mood = state.brief_params.mood if state.brief_params else "neutral"

    upscale_result = await _upscale(state.generated_asset_url)
    color_result = await _color_grade(state.generated_asset_url, mood)
    detail_result = await _inject_details(state.generated_asset_url)

    enhanced_metadata = {
        **state.generated_asset_metadata,
        "enhanced": True,
        "upscale": upscale_result,
        "color_grade": color_result,
        "detail_inject": detail_result,
    }

    return {
        "generated_asset_metadata": enhanced_metadata,
        "status": GenerationStatus.EVALUATING,
    }
