"""Tests for resilient HTTP client and Supabase DB module."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from agent.db import get_client, is_supabase_available
from agent.resilient import (
    CircuitOpenError,
    _get_circuit,
    _check_circuit,
    _record_failure,
    _record_success,
    _circuit_state,
    get_circuit_status,
    reset_circuit,
    _CIRCUIT_THRESHOLD,
)


class TestSupabaseClient:
    """Test Supabase client module."""

    def test_no_env_returns_none(self):
        with patch.dict("os.environ", {}, clear=True):
            import importlib
            import agent.db as db_mod
            db_mod._initialized = False
            db_mod._client = None
            result = db_mod.get_client()
            assert result is None

    def test_is_supabase_available_no_config(self):
        with patch("agent.db.get_client", return_value=None):
            assert not is_supabase_available()

    def test_is_supabase_available_with_client(self):
        with patch("agent.db.get_client", return_value=MagicMock()):
            assert is_supabase_available()


class TestCircuitBreaker:
    """Test circuit breaker logic."""

    def setup_method(self):
        _circuit_state.clear()

    def test_initial_state_closed(self):
        circuit = _get_circuit("test")
        assert circuit["state"] == "closed"
        assert circuit["failures"] == 0

    def test_check_closed_circuit_passes(self):
        _check_circuit("test")  # should not raise

    def test_record_failures_opens_circuit(self):
        for _ in range(_CIRCUIT_THRESHOLD):
            _record_failure("test")
        circuit = _get_circuit("test")
        assert circuit["state"] == "open"

    def test_open_circuit_raises(self):
        for _ in range(_CIRCUIT_THRESHOLD):
            _record_failure("test")
        with pytest.raises(CircuitOpenError):
            _check_circuit("test")

    def test_success_resets_circuit(self):
        for _ in range(3):
            _record_failure("test")
        _record_success("test")
        circuit = _get_circuit("test")
        assert circuit["state"] == "closed"
        assert circuit["failures"] == 0

    def test_get_circuit_status(self):
        _record_failure("api-a")
        _record_failure("api-b")
        status = get_circuit_status()
        assert "api-a" in status
        assert "api-b" in status
        assert status["api-a"]["failures"] == 1

    def test_reset_circuit(self):
        for _ in range(_CIRCUIT_THRESHOLD):
            _record_failure("test")
        assert _get_circuit("test")["state"] == "open"
        reset_circuit("test")
        assert _get_circuit("test")["state"] == "closed"

    def test_half_open_after_timeout(self):
        import time
        for _ in range(_CIRCUIT_THRESHOLD):
            _record_failure("test")
        circuit = _get_circuit("test")
        circuit["last_failure"] = time.time() - 120  # simulate 120s ago
        _check_circuit("test")  # should not raise, transitions to half-open
        assert circuit["state"] == "half-open"
