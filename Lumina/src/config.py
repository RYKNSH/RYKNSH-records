"""Lumina - AI Creative Production

世界最高峰のクリエイティブを、人間のデザイナー0名で、無限にスケールさせる自律型AIプロダクション。
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LuminaConfig:
    """Lumina全体の設定"""

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Ada Core API (LLM)
    ada_api_url: str = os.getenv("ADA_API_URL", "http://localhost:8000")
    ada_api_key: str = os.getenv("ADA_API_KEY", "")

    # Image Generation APIs
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    bfl_api_key: str = os.getenv("BFL_API_KEY", "")  # Black Forest Labs (Flux)

    # Quality thresholds (Taste Genome defaults)
    quality_threshold_preview: int = 0
    quality_threshold_standard: int = 75
    quality_threshold_premium: int = 85
    quality_threshold_masterpiece: int = 92

    # Retry limits by tier
    retry_limit_preview: int = 0
    retry_limit_standard: int = 3
    retry_limit_premium: int = 5
    retry_limit_masterpiece: int = 10

    # Tenant
    tenant_id: Optional[str] = None

    # Feature flags
    use_real_api: bool = os.getenv("LUMINA_USE_REAL_API", "false").lower() == "true"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_stability(self) -> bool:
        return bool(self.stability_api_key)

    @property
    def has_bfl(self) -> bool:
        return bool(self.bfl_api_key)

    @property
    def has_ada(self) -> bool:
        return bool(self.ada_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    def get_available_providers(self) -> list[str]:
        """利用可能なプロバイダーのリストを返す"""
        providers = []
        if self.has_bfl:
            providers.append("black-forest-labs")
        if self.has_openai:
            providers.append("openai")
        if self.has_stability:
            providers.append("stability-ai")
        return providers or ["stub"]  # APIキーなし → スタブモード


config = LuminaConfig()
