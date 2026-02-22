"""Tests for StrategistNode.

Covers:
- Input complexity analysis
- Temperature control
- CoT decision
- Quality tier determination
- StrategistNode integration
"""

import pytest

from agent.nodes.strategist import (
    StrategistNode,
    strategist_node,
    analyze_complexity,
    determine_temperature,
    should_use_cot,
    determine_quality_tier,
)


class TestAnalyzeComplexity:
    """Test input complexity analysis."""

    def test_empty_messages(self):
        result = analyze_complexity([])
        assert result["score"] == 0.0

    def test_simple_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = analyze_complexity(messages)
        assert result["score"] < 0.3

    def test_complex_technical_message(self):
        messages = [
            {"role": "user", "content": (
                "Analyze and compare these two implementations. "
                "Review the code for bugs, explain why the second approach "
                "is better, and provide a step by step refactoring plan."
            )}
        ]
        result = analyze_complexity(messages)
        assert result["score"] > 0.4

    def test_multi_turn_increases_complexity(self):
        single = [{"role": "user", "content": "Hello"}]
        multi = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ] * 5 + [{"role": "user", "content": "Hello"}]
        
        single_result = analyze_complexity(single)
        multi_result = analyze_complexity(multi)
        # Multi-turn should have higher score due to turn factor
        assert multi_result["factors"]["turns"] > single_result["factors"]["turns"]


class TestDetermineTemperature:
    """Test temperature selection."""

    def test_code_request_low_temp(self):
        messages = [{"role": "user", "content": "Write a Python function to sort a list"}]
        assert determine_temperature(messages) == 0.2

    def test_analysis_request_medium_temp(self):
        messages = [{"role": "user", "content": "Analyze the performance of this algorithm"}]
        assert determine_temperature(messages) == 0.4

    def test_general_request_default_temp(self):
        messages = [{"role": "user", "content": "Tell me a story about a cat"}]
        assert determine_temperature(messages) == 0.7

    def test_empty_messages_default_temp(self):
        assert determine_temperature([]) == 0.7


class TestShouldUseCot:
    """Test chain-of-thought decision."""

    def test_high_complexity_triggers_cot(self):
        messages = [{"role": "user", "content": "Hello"}]
        assert should_use_cot(0.6, messages) is True

    def test_low_complexity_no_cot(self):
        messages = [{"role": "user", "content": "Hello"}]
        assert should_use_cot(0.2, messages) is False

    def test_explicit_reasoning_triggers_cot(self):
        messages = [{"role": "user", "content": "Explain why this approach is better"}]
        assert should_use_cot(0.2, messages) is True

    def test_step_by_step_triggers_cot(self):
        messages = [{"role": "user", "content": "Walk me through the process"}]
        assert should_use_cot(0.2, messages) is True


class TestDetermineQualityTier:
    """Test quality tier determination."""

    def test_explicit_config_overrides(self):
        config = {"configurable": {"quality_tier": "full"}}
        assert determine_quality_tier(config, 0.1) == "full"

    def test_low_complexity_light(self):
        assert determine_quality_tier(None, 0.1) == "light"

    def test_medium_complexity_standard(self):
        assert determine_quality_tier(None, 0.4) == "standard"

    def test_high_complexity_full(self):
        assert determine_quality_tier(None, 0.7) == "full"


class TestStrategistNode:
    """Test the StrategistNode."""

    def test_singleton_exists(self):
        assert strategist_node is not None
        assert strategist_node.name == "strategist"

    @pytest.mark.asyncio
    async def test_basic_strategy(self):
        """Basic message should produce a valid strategy."""
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": None,
            "temperature": None,
        }
        result = await strategist_node.process(state)
        assert "selected_model" in result
        assert "quality_tier" in result
        assert "use_cot" in result
        assert "complexity_score" in result
        assert result["quality_tier"] in ("light", "standard", "full")

    @pytest.mark.asyncio
    async def test_cot_injection(self):
        """Complex query should trigger CoT system prompt."""
        state = {
            "messages": [{"role": "user", "content": "Explain step by step why Python is popular"}],
            "model": None,
            "temperature": None,
            "system_prompt_enriched": "You are an expert.",
        }
        result = await strategist_node.process(state)
        assert result["use_cot"] is True
        # CoT suffix should be in the system message
        system_msg = result["langchain_messages"][0]
        assert "step by step" in system_msg.content.lower()
