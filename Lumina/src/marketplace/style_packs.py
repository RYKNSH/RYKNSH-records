"""C2C Style Pack — スタイルパックマーケットプレイス (MS7)

Whitepaper Section 4 / Round 4:
クリエイターが自分の美学をパッケージ化して売れる。
プロンプトテンプレート + パラメータセット + 参照画像。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StylePack(BaseModel):
    """AIスタイルパック — C2Cの売買対象"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str = ""
    name: str = ""
    description: str = ""
    genre: str = ""
    prompt_template: str = ""
    parameter_set: dict[str, Any] = Field(default_factory=dict)
    reference_image_urls: list[str] = Field(default_factory=list)
    taste_score: float = 0.0  # min 80 to publish
    price: float = 0.0
    royalty_rate: float = 0.30
    downloads: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StylePackMarketplace:
    """スタイルパックマーケットプレイス

    Noah（コミュニティPF）との連携で
    マーケットプレイスUIを提供。
    Luminaはスタイルパックの生成・実行基盤を提供。
    """

    def __init__(self):
        self._packs: dict[str, StylePack] = {}
        self._seed()

    def _seed(self):
        packs = [
            StylePack(
                name="Cyberpunk Tokyo",
                creator_id="creator-001",
                genre="cyberpunk",
                prompt_template="{subject} in a neon-lit Tokyo street, cyberpunk aesthetic, rain reflections",
                parameter_set={"style": "cyberpunk", "mood": "dark", "color_palette": ["#FF00FF", "#00FFFF"]},
                taste_score=88.0,
                price=500,
            ),
            StylePack(
                name="Organic Minimalism",
                creator_id="creator-002",
                genre="minimalist",
                prompt_template="{subject}, organic shapes, earth tones, minimalist composition",
                parameter_set={"style": "minimalist", "mood": "calm", "color_palette": ["#E8D5B7", "#2C3E50"]},
                taste_score=92.0,
                price=800,
            ),
        ]
        for p in packs:
            self._packs[p.id] = p

    async def list_packs(self, genre: Optional[str] = None) -> list[StylePack]:
        packs = list(self._packs.values())
        if genre:
            packs = [p for p in packs if p.genre == genre]
        return sorted(packs, key=lambda p: p.downloads, reverse=True)

    async def get_pack(self, pack_id: str) -> Optional[StylePack]:
        return self._packs.get(pack_id)

    async def publish_pack(self, pack: StylePack) -> dict[str, Any]:
        if pack.taste_score < 80.0:
            return {"published": False, "error": f"Taste score {pack.taste_score} < 80.0 minimum"}
        self._packs[pack.id] = pack
        return {"published": True, "pack_id": pack.id}

    async def apply_pack(self, pack_id: str, subject: str) -> dict[str, Any]:
        pack = self._packs.get(pack_id)
        if not pack:
            return {"error": f"Pack {pack_id} not found"}

        prompt = pack.prompt_template.replace("{subject}", subject)
        pack.downloads += 1

        return {
            "prompt": prompt,
            "parameters": pack.parameter_set,
            "pack_name": pack.name,
            "creator_id": pack.creator_id,
            "royalty": pack.price * pack.royalty_rate,
        }
