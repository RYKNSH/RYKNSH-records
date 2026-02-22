"""Lumina State — LangGraphのグラフを流れる状態オブジェクト

全ノードがこの State を読み書きする。
Whitepaper Section 5 (5-Layer Architecture) に準拠。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class QualityTier(str, Enum):
    """品質ティア — Whitepaper Section 9"""

    PREVIEW = "preview"
    STANDARD = "standard"
    PREMIUM = "premium"
    MASTERPIECE = "masterpiece"


class AssetType(str, Enum):
    """生成アセットの種別"""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    COMPOSITE = "composite"


class GenerationStatus(str, Enum):
    """生成パイプラインの状態"""

    PENDING = "pending"
    INTERPRETING = "interpreting"  # brief_interpreter
    SELECTING = "selecting"  # model_selector
    GENERATING = "generating"  # generator
    ENHANCING = "enhancing"  # enhancer_pipeline
    EVALUATING = "evaluating"  # taste_engine
    RETRYING = "retrying"  # ai_escalation_chain
    DELIVERING = "delivering"  # delivery layer
    COMPLETED = "completed"
    FAILED = "failed"


class ModelSelection(BaseModel):
    """Model Selector が選択したモデル情報"""

    model_id: str
    model_name: str
    provider: str
    capability_score: float
    cost_per_call: float
    selection_reason: str


class TasteScore(BaseModel):
    """Taste Engine の評価結果"""

    composition: float = 0.0  # Critic A: 構図
    color: float = 0.0  # Critic B: 色彩
    brand_fit: float = 0.0  # Critic C: ブランド適合
    emotional_impact: float = 0.0  # Critic D: 感情インパクト
    ip_worldview: float = 0.0  # Critic E: IP世界観（Masterpieceのみ）
    fan_expectation: float = 0.0  # Critic F: ファン期待値（Masterpieceのみ）
    aggregated: float = 0.0  # 重み付き統合スコア (0-100)


class BriefParams(BaseModel):
    """brief_interpreter が生成する構造化パラメータ"""

    subject: str = ""
    style: str = ""
    mood: str = ""
    color_palette: list[str] = Field(default_factory=list)
    composition_hints: list[str] = Field(default_factory=list)
    negative_prompts: list[str] = Field(default_factory=list)
    reference_context: str = ""
    prompt: str = ""  # 最終的に生成モデルに渡すプロンプト


class LuminaState(BaseModel):
    """Lumina Graph の状態

    LangGraph の TypedDict の代わりに Pydantic を使用。
    各ノードはこの State を受け取り、更新されたフィールドのみを返す。
    """

    # --- Request ---
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    brief: str = ""  # クライアントからの自然言語ブリーフ
    quality_tier: QualityTier = QualityTier.STANDARD
    asset_type: AssetType = AssetType.IMAGE

    # --- Creation Layer ---
    brief_params: Optional[BriefParams] = None
    model_selection: Optional[ModelSelection] = None
    generated_asset_url: str = ""
    generated_asset_metadata: dict[str, Any] = Field(default_factory=dict)

    # --- Quality Fortress ---
    taste_score: Optional[TasteScore] = None
    quality_threshold: float = 75.0  # テナントの要求水準
    retry_count: int = 0
    max_retries: int = 3  # QualityTier に応じて変動
    escalation_step: int = 0  # AI Escalation Chain の現在ステップ

    # --- Delivery ---
    deliverable_url: str = ""
    delivery_metadata: dict[str, Any] = Field(default_factory=dict)

    # --- Status ---
    status: GenerationStatus = GenerationStatus.PENDING
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_quality_passed(self) -> bool:
        """品質基準を満たしているか"""
        if self.taste_score is None:
            return False
        return self.taste_score.aggregated >= self.quality_threshold

    def can_retry(self) -> bool:
        """リトライ可能か"""
        return self.retry_count < self.max_retries

    def get_max_retries_for_tier(self) -> int:
        """品質ティアに応じたリトライ上限"""
        return {
            QualityTier.PREVIEW: 0,
            QualityTier.STANDARD: 3,
            QualityTier.PREMIUM: 5,
            QualityTier.MASTERPIECE: 10,
        }[self.quality_tier]

    def get_quality_threshold_for_tier(self) -> float:
        """品質ティアに応じた品質閾値"""
        return {
            QualityTier.PREVIEW: 0.0,
            QualityTier.STANDARD: 75.0,
            QualityTier.PREMIUM: 85.0,
            QualityTier.MASTERPIECE: 92.0,
        }[self.quality_tier]
