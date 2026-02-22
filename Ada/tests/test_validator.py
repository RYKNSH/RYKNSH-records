"""Tests for ValidatorNode.

Covers:
- Empty response detection
- Format validation (JSON, list)
- Grounding check
- Refusal leak detection
- ValidatorNode integration
- Graph retry logic
"""

import pytest

from agent.nodes.validator import (
    ValidatorNode,
    validator_node,
    check_empty_response,
    check_format,
    check_grounding,
    check_refusal_leak,
)


class TestCheckEmptyResponse:
    """Test empty/short response detection."""

    def test_empty_string_fails(self):
        result = check_empty_response("")
        assert result is not None
        assert result["passed"] is False

    def test_whitespace_only_fails(self):
        result = check_empty_response("   \n  ")
        assert result is not None
        assert result["passed"] is False

    def test_very_short_fails(self):
        result = check_empty_response("Hi")
        assert result is not None
        assert result["passed"] is False

    def test_normal_response_passes(self):
        result = check_empty_response("This is a normal response with enough content.")
        assert result is None  # None means passed


class TestCheckFormat:
    """Test format validation."""

    def test_no_expected_format_passes(self):
        assert check_format("anything", None) is None

    def test_valid_json_passes(self):
        assert check_format('{"key": "value"}', "json") is None

    def test_json_in_code_block_passes(self):
        content = '```json\n{"key": "value"}\n```'
        assert check_format(content, "json") is None

    def test_invalid_json_fails(self):
        result = check_format("not json at all", "json")
        assert result is not None
        assert result["passed"] is False

    def test_valid_list_passes(self):
        content = "- Item 1\n- Item 2\n- Item 3"
        assert check_format(content, "list") is None

    def test_numbered_list_passes(self):
        content = "1. First item\n2. Second item"
        assert check_format(content, "list") is None

    def test_no_list_fails(self):
        result = check_format("Just a paragraph of text.", "list")
        assert result is not None
        assert result["passed"] is False


class TestCheckGrounding:
    """Test grounding validation."""

    def test_no_rag_context_skips(self):
        assert check_grounding("any response", []) is None

    def test_grounded_response_passes(self):
        rag_context = [
            {"content": "Python is a programming language created by Guido van Rossum."}
        ]
        response = "Python is a language created by Guido van Rossum."
        assert check_grounding(response, rag_context) is None

    def test_ungrounded_long_response_fails(self):
        rag_context = [
            {"content": "This document discusses quantum computing algorithms and qubits."}
        ]
        response = "Basketball is a sport played by teams of five players. " * 5
        result = check_grounding(response, rag_context)
        assert result is not None
        assert result["passed"] is False


class TestCheckRefusalLeak:
    """Test refusal pattern detection."""

    def test_normal_response_passes(self):
        assert check_refusal_leak("Here is the information you requested.") is None

    def test_ai_model_reference_fails(self):
        result = check_refusal_leak("As an AI language model, I cannot do that.")
        assert result is not None
        assert result["passed"] is False

    def test_training_data_reference_fails(self):
        result = check_refusal_leak("Based on my training data, I can say...")
        assert result is not None
        assert result["passed"] is False

    def test_ability_disclaimer_fails(self):
        result = check_refusal_leak("I'm not able to access the internet.")
        assert result is not None
        assert result["passed"] is False


class TestValidatorNode:
    """Test the ValidatorNode."""

    def test_singleton_exists(self):
        assert validator_node is not None
        assert validator_node.name == "validator"

    @pytest.mark.asyncio
    async def test_good_response_passes(self):
        state = {
            "response_content": "Here is a helpful and detailed response to your question.",
            "rag_context": [],
            "retry_count": 0,
        }
        result = await validator_node.process(state)
        assert result["validation_passed"] is True
        assert result["validation_score"] == 1.0

    @pytest.mark.asyncio
    async def test_empty_response_fails(self):
        state = {
            "response_content": "",
            "rag_context": [],
            "retry_count": 0,
        }
        result = await validator_node.process(state)
        assert result["validation_passed"] is False
        assert "empty" in result["validation_reason"].lower()

    @pytest.mark.asyncio
    async def test_refusal_leak_fails(self):
        state = {
            "response_content": "As an AI language model, I cannot help with that request.",
            "rag_context": [],
            "retry_count": 0,
        }
        result = await validator_node.process(state)
        assert result["validation_passed"] is False

    @pytest.mark.asyncio
    async def test_validation_score_partial(self):
        """Score should reflect partial failures."""
        state = {
            "response_content": "As an AI model, here is a response.",
            "rag_context": [],
            "retry_count": 0,
        }
        result = await validator_node.process(state)
        assert result["validation_score"] < 1.0


class TestGraphRetryLogic:
    """Test validator retry logic in the graph."""

    def test_graph_builds_with_validator(self):
        from agent.graph import build_router_graph
        graph = build_router_graph()
        assert graph is not None

    def test_should_retry_passes_through(self):
        from agent.graph import _should_retry_after_validation
        state = {"validation_passed": True}
        assert _should_retry_after_validation(state) == "log_usage"

    def test_should_retry_on_failure(self):
        from agent.graph import _should_retry_after_validation
        state = {"validation_passed": False, "retry_count": 0}
        assert _should_retry_after_validation(state) == "invoke_llm"

    def test_should_not_retry_after_max(self):
        from agent.graph import _should_retry_after_validation
        state = {"validation_passed": False, "retry_count": 1}
        assert _should_retry_after_validation(state) == "log_usage"

    def test_default_validation_passes(self):
        from agent.graph import _should_retry_after_validation
        state = {}
        assert _should_retry_after_validation(state) == "log_usage"
