"""Velie QA Agent — Server Configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic
    anthropic_api_key: str

    # GitHub
    github_token: str
    github_webhook_secret: str

    # Server
    port: int = 8000
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Lazy-loaded settings singleton. Safe for testing with monkeypatch."""
    return Settings()
