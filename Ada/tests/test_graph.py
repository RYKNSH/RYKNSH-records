"""Tests for agent.graph — LLM Router Graph."""

from unittest.mock import AsyncMock, patch

import pytest

from agent.graph import _convert_messages, select_model, RouterState


class TestConvertMessages:
    """Test OpenAI-format to LangChain message conversion."""

    def test_system_message(self):
        msgs = [{"role": "system", "content": "You are helpful"}]
        result = _convert_messages(msgs)
        assert len(result) == 1
        assert result[0].content == "You are helpful"
        assert result[0].__class__.__name__ == "SystemMessage"

    def test_user_message(self):
        msgs = [{"role": "user", "content": "Hello"}]
        result = _convert_messages(msgs)
        assert result[0].__class__.__name__ == "HumanMessage"

    def test_assistant_message(self):
        msgs = [{"role": "assistant", "content": "Hi there"}]
        result = _convert_messages(msgs)
        assert result[0].__class__.__name__ == "AIMessage"

    def test_multi_turn(self):
        msgs = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
        ]
        result = _convert_messages(msgs)
        assert len(result) == 4

    def test_empty_messages(self):
        result = _convert_messages([])
        assert result == []


class TestSelectModel:
    """Test model selection logic."""

    def _make_state(self, model=None) -> RouterState:
        return {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": model,
            "temperature": 0.7,
            "max_tokens": None,
            "tenant_id": "test-tenant",
            "selected_model": "",
            "langchain_messages": [],
            "response_content": "",
            "response_model": "",
            "usage": {},
            "request_id": "",
        }

    def test_explicit_model(self):
        state = self._make_state(model="gpt-4o")
        config = {
            "configurable": {
                "default_model": "claude-sonnet-4-20250514",
                "allowed_models": ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"],
            }
        }
        result = select_model(state, config)
        assert result["selected_model"] == "gpt-4o"

    def test_tenant_default_model(self):
        state = self._make_state(model=None)
        config = {
            "configurable": {
                "default_model": "gpt-4o-mini",
                "allowed_models": ["gpt-4o-mini", "gpt-4o"],
            }
        }
        result = select_model(state, config)
        assert result["selected_model"] == "gpt-4o-mini"

    def test_fallback_to_claude(self):
        state = self._make_state(model=None)
        result = select_model(state, None)
        assert result["selected_model"] == "claude-sonnet-4-20250514"

    def test_generates_request_id(self):
        state = self._make_state()
        result = select_model(state, None)
        assert result["request_id"]
        assert len(result["request_id"]) > 0

    def test_converts_messages(self):
        state = self._make_state()
        result = select_model(state, None)
        assert len(result["langchain_messages"]) == 1
