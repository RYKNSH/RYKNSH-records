"""子会社連携アダプター — Boundary Protocol

Whitepaper Section 10: Boundary Protocol
Cyrus = マーケ戦略・営業フロー → Luminaにクリエイティブ発注
Ada   = LLM推論基盤 → LuminaがVision LLM評価に使用
Iris  = ブランド保護・PR → Luminaの成果物をブランドチェック
Noah  = マッチングPF → Luminaの成果物をコンテンツとして連携
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from src.config import config


class SubsidiaryAdapter:
    """RYKNSH子会社との連携アダプター基底"""

    def __init__(self, name: str, api_url: str = "", api_key: str = ""):
        self.name = name
        self.api_url = api_url
        self.api_key = api_key

    async def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """共通HTTPポスト"""
        if not self.api_url or not config.use_real_api:
            return {"status": "stub", "subsidiary": self.name, "data": data}

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=data,
            )
            response.raise_for_status()
            return response.json()

    async def _get(self, path: str, params: dict[str, Any] = None) -> dict[str, Any]:
        """共通HTTPゲット"""
        if not self.api_url or not config.use_real_api:
            return {"status": "stub", "subsidiary": self.name}

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=params,
            )
            response.raise_for_status()
            return response.json()


class AdaAdapter(SubsidiaryAdapter):
    """Ada Core API — LLM推論基盤

    Luminaが使用するAPI:
    - Vision LLM (taste_engine)
    - Embeddings (reference_set)
    - Text Generation (brief_interpreter LLM版)
    """

    def __init__(self):
        super().__init__(
            name="ada",
            api_url=config.ada_api_url,
            api_key=config.ada_api_key,
        )

    async def chat(self, messages: list[dict], model: str = "claude-sonnet-4-20250514", max_tokens: int = 1000) -> str:
        """テキスト生成"""
        result = await self._post("/v1/chat/completions", {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        })
        if result.get("status") == "stub":
            return "Ada stub response"
        return result.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def embed(self, text: str) -> list[float]:
        """テキスト/画像のembedding"""
        result = await self._post("/v1/embeddings", {
            "input": text,
            "model": "text-embedding-3-small",
        })
        if result.get("status") == "stub":
            import random
            return [random.uniform(-1, 1) for _ in range(1536)]
        return result.get("data", [{}])[0].get("embedding", [])

    async def health(self) -> dict[str, Any]:
        return await self._get("/health")


class CyrusAdapter(SubsidiaryAdapter):
    """Cyrus — マーケ戦略・営業フロー

    Cyrus → Lumina: クリエイティブ発注
    Lumina → Cyrus: 成果物納品通知
    """

    def __init__(self):
        import os
        super().__init__(
            name="cyrus",
            api_url=os.getenv("CYRUS_API_URL", "http://localhost:8001"),
            api_key=os.getenv("CYRUS_API_KEY", ""),
        )

    async def notify_delivery(self, asset_url: str, blueprint_id: str, metadata: dict) -> dict:
        """成果物の納品をCyrusに通知"""
        return await self._post("/api/lumina/delivery", {
            "asset_url": asset_url,
            "blueprint_id": blueprint_id,
            "metadata": metadata,
        })

    async def get_pending_orders(self) -> list[dict]:
        """Cyrusからの未処理のクリエイティブ発注を取得"""
        result = await self._get("/api/lumina/orders", {"status": "pending"})
        return result.get("orders", [])


class IrisAdapter(SubsidiaryAdapter):
    """Iris — ブランド保護・PR

    Lumina → Iris: ブランドチェックリクエスト
    Iris → Lumina: 承認/拒否/修正指示
    """

    def __init__(self):
        import os
        super().__init__(
            name="iris",
            api_url=os.getenv("IRIS_API_URL", "http://localhost:8002"),
            api_key=os.getenv("IRIS_API_KEY", ""),
        )

    async def brand_check(self, asset_url: str, tenant_id: str, brand_guidelines: dict = None) -> dict:
        """ブランドチェックをIrisに依頼"""
        return await self._post("/api/brand/check", {
            "asset_url": asset_url,
            "tenant_id": tenant_id,
            "brand_guidelines": brand_guidelines or {},
        })


class NoahAdapter(SubsidiaryAdapter):
    """Noah — マッチングプラットフォーム

    Lumina → Noah: コンテンツ登録
    """

    def __init__(self):
        import os
        super().__init__(
            name="noah",
            api_url=os.getenv("NOAH_API_URL", "http://localhost:8003"),
            api_key=os.getenv("NOAH_API_KEY", ""),
        )

    async def register_content(self, asset_url: str, metadata: dict) -> dict:
        """生成コンテンツをNoahに登録"""
        return await self._post("/api/content/register", {
            "asset_url": asset_url,
            "metadata": metadata,
        })


# 公開API: 全アダプターを一括取得
def get_adapters() -> dict[str, SubsidiaryAdapter]:
    """全子会社アダプターを返す"""
    return {
        "ada": AdaAdapter(),
        "cyrus": CyrusAdapter(),
        "iris": IrisAdapter(),
        "noah": NoahAdapter(),
    }
