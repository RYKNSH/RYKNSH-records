"""Velie QA Agent — Server Configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic
    anthropic_api_key: str

    # GitHub (PAT — optional if using GitHub App)
    github_token: str | None = None
    github_webhook_secret: str

    # GitHub App (Optional — PAT fallback if not set)
    github_app_id: int | None = None
    github_app_private_key: str | None = None

    # Supabase (Optional — stateless mode if not set)
    supabase_db_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    # Redis (Optional — in-memory queue if not set)
    redis_url: str | None = None

    # Server
    port: int = 8000
    log_level: str = "info"
    velie_env: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Lazy-loaded settings singleton. Safe for testing with monkeypatch."""
    return Settings()
