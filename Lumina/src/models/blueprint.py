"""CreativeBlueprint — B2B/B2C/C2C統一設計図

Whitepaper Section 10 に準拠。
全ビジネスモデル（B2B/B2C/C2C）のリクエストを統一フォーマットで表現する。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .state import AssetType, QualityTier


class BusinessModel(str, Enum):
    """ビジネスモデル種別"""

    B2B = "b2b"
    B2C = "b2c"
    C2C = "c2c"
    INTERNAL = "internal"  # 内販（Label 01, Cyrus, Iris, Noah向け）


class EntityType(str, Enum):
    """エンティティ種別"""

    COMPANY = "company"  # B2B: 企業
    CONSUMER = "consumer"  # B2C: 個人クリエイター
    CREATOR = "creator"  # C2C: プロビジュアルアーティスト
    SUBSIDIARY = "subsidiary"  # 内販: RYKNSH子会社


class EntityConfig(BaseModel):
    """エンティティ設定"""

    type: EntityType
    industry: str = ""
    brand_maturity: str = ""  # emerging / established / legacy
    creator_level: str = ""  # indie / pro / studio
    budget_sensitivity: str = "medium"  # low / medium / high


class PipelineConfig(BaseModel):
    """パイプライン設定"""

    model_selection: str = "auto"  # auto / specific model_id
    enhancer: bool = True
    taste_engine: bool = True
    multi_model_synthesis: bool = False
    mad_editor: bool = False  # Masterpieceティアのみ


class OutputSpecs(BaseModel):
    """出力仕様"""

    format: str = "png"
    resolution: str = "1024x1024"
    duration_range: str = ""  # 映像の場合
    style_pack: str = ""  # C2Cスタイルパック指定


class TasteConfig(BaseModel):
    """Taste Engine の Critic 重み設定"""

    composition_weight: float = 0.25
    color_weight: float = 0.25
    brand_weight: float = 0.25
    impact_weight: float = 0.25
    # Masterpieceティアのみ
    ip_worldview_weight: float = 0.0
    fan_expectation_weight: float = 0.0


class StylePackConfig(BaseModel):
    """C2Cスタイルパック設定"""

    prompt_template: bool = True
    parameter_set: bool = True
    reference_images_count: int = 5
    royalty_rate: float = 0.30
    pricing: str = "creator_set"
    min_taste_score: float = 80.0


class CreativeBlueprint(BaseModel):
    """クリエイティブブループリント — 統一設計図

    B2B/B2C/C2C/内販の全てのリクエストを
    この単一のモデルで表現する。
    """

    blueprint_id: str = ""
    business_model: BusinessModel = BusinessModel.B2C

    # Entity
    entity_config: EntityConfig = Field(
        default_factory=lambda: EntityConfig(type=EntityType.CONSUMER)
    )

    # Quality
    quality_tier: QualityTier = QualityTier.STANDARD

    # Pipeline
    pipeline_config: PipelineConfig = Field(default_factory=PipelineConfig)

    # Output
    asset_type: AssetType = AssetType.IMAGE
    deliverables: list[str] = Field(default_factory=list)
    output_specs: OutputSpecs = Field(default_factory=OutputSpecs)

    # Taste
    taste_config: TasteConfig = Field(default_factory=TasteConfig)
    reference_set_id: str = ""

    # C2C
    style_pack_config: Optional[StylePackConfig] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def for_internal(
        cls,
        subsidiary: str,
        deliverables: list[str],
        quality_tier: QualityTier = QualityTier.PREMIUM,
    ) -> CreativeBlueprint:
        """内販向けブループリントを生成"""
        return cls(
            blueprint_id=f"internal-{subsidiary}",
            business_model=BusinessModel.INTERNAL,
            entity_config=EntityConfig(type=EntityType.SUBSIDIARY),
            quality_tier=quality_tier,
            deliverables=deliverables,
            pipeline_config=PipelineConfig(
                enhancer=True,
                taste_engine=True,
                multi_model_synthesis=quality_tier == QualityTier.MASTERPIECE,
                mad_editor=quality_tier == QualityTier.MASTERPIECE,
            ),
        )

    @classmethod
    def for_b2c_mv(cls, style_pack: str = "") -> CreativeBlueprint:
        """B2C MV Factory 向けブループリント"""
        return cls(
            blueprint_id="b2c-mv-factory",
            business_model=BusinessModel.B2C,
            entity_config=EntityConfig(
                type=EntityType.CONSUMER, creator_level="indie_artist"
            ),
            quality_tier=QualityTier.STANDARD,
            asset_type=AssetType.VIDEO,
            deliverables=["music_video_60s", "thumbnail", "social_clips"],
            output_specs=OutputSpecs(
                format="mp4",
                resolution="1080p",
                duration_range="30s-180s",
                style_pack=style_pack or "auto",
            ),
        )
