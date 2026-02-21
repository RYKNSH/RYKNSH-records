"""Tests for agent.providers — Model registry and provider invocation."""

from agent.providers import (
    MODELS,
    FALLBACK_CHAIN,
    get_fallback,
    get_model_spec,
    list_models,
)


class TestModelRegistry:
    """Test model registry operations."""

    def test_all_models_have_specs(self):
        """All registered models should have complete specs."""
        for model_id, spec in MODELS.items():
            assert spec.model_id == model_id
            assert spec.provider in ("anthropic", "openai")
            assert spec.display_name
            assert spec.context_window > 0
            assert spec.max_output_tokens > 0
            assert spec.cost_per_1k_input >= 0
            assert spec.cost_per_1k_output >= 0

    def test_get_model_spec_valid(self):
        """Should return spec for a known model."""
        spec = get_model_spec("gpt-4o")
        assert spec is not None
        assert spec.provider == "openai"

    def test_get_model_spec_unknown(self):
        """Should return None for unknown model."""
        assert get_model_spec("nonexistent-model") is None

    def test_list_models_format(self):
        """list_models should return OpenAI-compatible format."""
        models = list_models()
        assert len(models) == len(MODELS)
        for m in models:
            assert "id" in m
            assert m["object"] == "model"
            assert "owned_by" in m

    def test_fallback_chain_integrity(self):
        """All fallback targets should be valid models."""
        for src, dst in FALLBACK_CHAIN.items():
            assert src in MODELS, f"Source {src} not in MODELS"
            assert dst in MODELS, f"Fallback {dst} not in MODELS"
            assert src != dst, f"Model {src} falls back to itself"

    def test_get_fallback(self):
        """Should return fallback model or None."""
        fb = get_fallback("claude-sonnet-4-20250514")
        assert fb == "gpt-4o"
        assert get_fallback("nonexistent") is None

    def test_claude_model_exists(self):
        """Claude Sonnet 4 should be registered."""
        spec = get_model_spec("claude-sonnet-4-20250514")
        assert spec is not None
        assert spec.provider == "anthropic"
        assert "reasoning" in spec.tags

    def test_gpt4o_mini_is_cheapest(self):
        """GPT-4o Mini should have the lowest cost."""
        mini = get_model_spec("gpt-4o-mini")
        others = [s for k, s in MODELS.items() if k != "gpt-4o-mini"]
        for other in others:
            assert mini.cost_per_1k_input <= other.cost_per_1k_input
