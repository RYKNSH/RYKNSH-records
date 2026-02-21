"""Shared test fixtures for Velie QA Agent tests."""

import os

import pytest

# Set env vars BEFORE any module imports that trigger get_settings()
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
os.environ.setdefault("GITHUB_TOKEN", "ghp_test_token")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret-123")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear the lru_cache of get_settings between tests."""
    from server.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
