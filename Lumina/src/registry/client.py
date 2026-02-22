"""Model Registry Client — Whitepaper Section 7

全AIモデルをSupabase上のレジストリで一元管理。
model_selector ノードがこのクライアントを通じて最適モデルを動的に選択する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field


class ModelCapabilities(BaseModel):
    """モデルの得意分野スコア (0.0-1.0)"""

    composition: float = 0.5
    text_rendering: float = 0.5
    photorealism: float = 0.5
    artistic: float = 0.5
    anime: float = 0.5
    video_quality: float = 0.0
    consistency: float = 0.5


class RegisteredModel(BaseModel):
    """レジストリに登録されたモデル"""

    id: str
    model_name: str
    model_type: str  # image / video / audio / composite
    provider: str
    api_endpoint: str = ""
    capability_score: float = 0.0
    cost_per_call: float = 0.0
    strengths: ModelCapabilities = Field(default_factory=ModelCapabilities)
    is_active: bool = True


class ModelRegistryClient:
    """Model Registry への CRUD 操作

    本番: Supabase の lumina_model_registry テーブルに接続
    開発/テスト: インメモリの seed データで動作
    """

    def __init__(self, supabase_client: Any = None):
        self._supabase = supabase_client
        self._local_registry: dict[str, RegisteredModel] = {}

        if self._supabase is None:
            self._seed_local_registry()

    def _seed_local_registry(self) -> None:
        """開発用のシードデータ"""
        seeds = [
            RegisteredModel(
                id="flux-1.1-pro",
                model_name="Flux 1.1 Pro",
                model_type="image",
                provider="black-forest-labs",
                capability_score=92,
                cost_per_call=0.04,
                strengths=ModelCapabilities(
                    composition=0.9,
                    photorealism=0.85,
                    artistic=0.8,
                    text_rendering=0.6,
                ),
            ),
            RegisteredModel(
                id="dall-e-3",
                model_name="DALL-E 3",
                model_type="image",
                provider="openai",
                capability_score=85,
                cost_per_call=0.04,
                strengths=ModelCapabilities(
                    composition=0.8,
                    text_rendering=0.9,
                    photorealism=0.7,
                    artistic=0.75,
                ),
            ),
            RegisteredModel(
                id="sd-xl-turbo",
                model_name="Stable Diffusion XL Turbo",
                model_type="image",
                provider="stability-ai",
                capability_score=78,
                cost_per_call=0.01,
                strengths=ModelCapabilities(
                    composition=0.7,
                    artistic=0.85,
                    photorealism=0.6,
                    text_rendering=0.3,
                ),
            ),
        ]
        for model in seeds:
            self._local_registry[model.id] = model

    async def get_active_models(
        self, model_type: str = "image"
    ) -> list[RegisteredModel]:
        """アクティブなモデル一覧を取得"""
        if self._supabase:
            response = (
                self._supabase.table("lumina_model_registry")
                .select("*")
                .eq("is_active", True)
                .eq("model_type", model_type)
                .order("capability_score", desc=True)
                .execute()
            )
            return [RegisteredModel(**row) for row in response.data]

        return [
            m
            for m in self._local_registry.values()
            if m.is_active and m.model_type == model_type
        ]

    async def get_model(self, model_id: str) -> Optional[RegisteredModel]:
        """特定モデルの情報を取得"""
        if self._supabase:
            response = (
                self._supabase.table("lumina_model_registry")
                .select("*")
                .eq("id", model_id)
                .single()
                .execute()
            )
            return RegisteredModel(**response.data) if response.data else None

        return self._local_registry.get(model_id)

    async def get_best_model(
        self,
        model_type: str = "image",
        task_style: str = "general",
        max_cost: Optional[float] = None,
    ) -> Optional[RegisteredModel]:
        """タスクに最適なモデルを返す

        model_selector ノードが使用するメインAPI。
        """
        models = await self.get_active_models(model_type)

        if max_cost is not None:
            models = [m for m in models if m.cost_per_call <= max_cost]

        if not models:
            return None

        # タスクスタイルに応じてスコアリング
        style_weight_map: dict[str, str] = {
            "photorealistic": "photorealism",
            "artistic": "artistic",
            "anime": "anime",
            "text_heavy": "text_rendering",
            "general": "",
        }

        weight_field = style_weight_map.get(task_style, "")

        if weight_field:
            models.sort(
                key=lambda m: getattr(m.strengths, weight_field, 0.0),
                reverse=True,
            )
        else:
            models.sort(key=lambda m: m.capability_score, reverse=True)

        return models[0]

    async def register_model(self, model: RegisteredModel) -> None:
        """モデルをレジストリに追加"""
        if self._supabase:
            self._supabase.table("lumina_model_registry").upsert(
                model.model_dump()
            ).execute()
        else:
            self._local_registry[model.id] = model

    async def deactivate_model(self, model_id: str) -> None:
        """モデルを無効化"""
        if self._supabase:
            self._supabase.table("lumina_model_registry").update(
                {"is_active": False}
            ).eq("id", model_id).execute()
        else:
            if model_id in self._local_registry:
                self._local_registry[model_id].is_active = False
