"""Ada Core API — Server Configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Supabase (Optional — stateless mode if not set)
    supabase_db_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    # Redis (Optional — in-memory queue if not set)
    redis_url: str | None = None

    # Ada API Authentication
    ada_api_key: str = ""

    # Stripe (Optional — free tier if not set)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""
    stripe_price_id_enterprise: str = ""

    # App
    app_url: str = "http://localhost:8000"

    # Server
    port: int = 8000
    log_level: str = "info"
    ada_env: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Lazy-loaded settings singleton. Safe for testing with monkeypatch."""
    return Settings()
