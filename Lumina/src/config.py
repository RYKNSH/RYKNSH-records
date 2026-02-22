"""Lumina - AI Creative Production

世界最高峰のクリエイティブを、人間のデザイナー0名で、無限にスケールさせる自律型AIプロダクション。
"""

import os
from dataclasses import dataclass
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


config = LuminaConfig()
