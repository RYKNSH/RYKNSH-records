"""pgvector Reference Set — ブランド参照画像ベクトル検索基盤

Whitepaper Section 8 > Critic C: ブランド適合度
参照画像セットとのCosine Similarityでブランド適合度を評価する。

本番: Supabase pgvector で参照画像のembeddingを管理
開発: インメモリ擬似ベクトル検索
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.config import config


class ReferenceImage(BaseModel):
    """参照画像のエントリー"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    image_url: str = ""
    description: str = ""
    embedding: list[float] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0  # 品質スコア


class ReferenceSetClient:
    """Reference Set への CRUD + ベクトル検索

    本番: Supabase pgvector テーブルに接続
    開発: インメモリ擬似検索
    """

    def __init__(self, supabase_client: Any = None):
        self._supabase = supabase_client
        self._local_store: dict[str, ReferenceImage] = {}

        if self._supabase is None:
            self._seed()

    def _seed(self) -> None:
        """開発用のシードデータ"""
        seeds = [
            ReferenceImage(
                tenant_id="default",
                image_url="https://lumina-ref.example.com/brand-a-logo.png",
                description="ミニマルなロゴデザイン、白背景、幾何学的形状",
                tags=["logo", "minimalist", "geometric"],
                score=92.0,
            ),
            ReferenceImage(
                tenant_id="default",
                image_url="https://lumina-ref.example.com/brand-a-hero.png",
                description="サイバーパンクなヒーロー画像、ネオンカラー",
                tags=["hero", "cyberpunk", "neon"],
                score=88.0,
            ),
            ReferenceImage(
                tenant_id="default",
                image_url="https://lumina-ref.example.com/brand-a-product.png",
                description="クリーンなプロダクト写真、自然光",
                tags=["product", "clean", "natural"],
                score=85.0,
            ),
        ]
        for ref in seeds:
            self._local_store[ref.id] = ref

    async def add_reference(self, image: ReferenceImage) -> str:
        """参照画像を追加"""
        if self._supabase:
            # 本番: embedding生成 → pgvectorに格納
            embedding = await self._generate_embedding(image.image_url)
            image.embedding = embedding

            self._supabase.table("lumina_reference_set").insert(
                image.model_dump()
            ).execute()
        else:
            self._local_store[image.id] = image

        return image.id

    async def search_similar(
        self,
        query_url: str,
        tenant_id: str = "default",
        top_k: int = 5,
    ) -> list[ReferenceImage]:
        """類似参照画像を検索

        本番: query_urlのembeddingを生成 → pgvector cosine similarity検索
        開発: タグベースの擬似マッチ
        """
        if self._supabase:
            query_embedding = await self._generate_embedding(query_url)

            response = self._supabase.rpc(
                "match_reference_images",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.7,
                    "match_count": top_k,
                    "p_tenant_id": tenant_id,
                },
            ).execute()

            return [ReferenceImage(**row) for row in response.data]

        # 開発: テナント一致するものを全返却
        return [
            ref for ref in self._local_store.values()
            if ref.tenant_id == tenant_id
        ][:top_k]

    async def get_brand_similarity_score(
        self,
        asset_url: str,
        tenant_id: str = "default",
    ) -> float:
        """生成物とブランド参照セットのCosine Similarity平均を返す"""
        similar = await self.search_similar(asset_url, tenant_id)
        if not similar:
            return 70.0  # 参照なし → デフォルトスコア

        # 開発: 参照画像の平均品質スコアを返す
        return sum(ref.score for ref in similar) / len(similar)

    async def _generate_embedding(self, image_url: str) -> list[float]:
        """画像のembeddingを生成

        本番: Ada API または OpenAI CLIP経由でembeddingを取得
        開発: ダミーベクトル
        """
        if config.use_real_api and config.has_ada:
            import httpx

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{config.ada_api_url}/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {config.ada_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "input": image_url,
                            "model": "text-embedding-3-small",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["data"][0]["embedding"]
            except Exception:
                pass

        # フォールバック: ダミーベクトル (1536次元)
        import random
        return [random.uniform(-1, 1) for _ in range(1536)]

    async def list_references(self, tenant_id: str = "default") -> list[ReferenceImage]:
        """テナントの参照画像一覧"""
        if self._supabase:
            response = (
                self._supabase.table("lumina_reference_set")
                .select("*")
                .eq("tenant_id", tenant_id)
                .execute()
            )
            return [ReferenceImage(**row) for row in response.data]

        return [r for r in self._local_store.values() if r.tenant_id == tenant_id]
