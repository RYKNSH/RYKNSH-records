"""Ada Core API — Test Configuration."""

import os

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set required environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ADA_API_KEY", "ada-test-key")

    # Clear settings cache
    from server.config import get_settings
    get_settings.cache_clear()
