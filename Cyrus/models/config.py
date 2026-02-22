"""Cyrus Engine — Core configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ada Core API
    ada_api_url: str = "http://localhost:8000"
    ada_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    # External Data Sources
    clay_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
