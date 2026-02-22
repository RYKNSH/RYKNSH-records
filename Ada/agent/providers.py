"""Ada Core API — LLM Provider Registry.

Manages multiple LLM providers (Anthropic, OpenAI) with automatic fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelSpec:
    """Specification for a single LLM model."""

    model_id: str
    provider: str  # "anthropic" or "openai"
    display_name: str
    context_window: int
    max_output_tokens: int
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float  # USD
    tags: tuple[str, ...] = ()  # e.g. ("reasoning", "fast", "general")


# --- Model Registry ---

MODELS: dict[str, ModelSpec] = {
    "claude-sonnet-4-20250514": ModelSpec(
        model_id="claude-sonnet-4-20250514",
        provider="anthropic",
        display_name="Claude Sonnet 4",
        context_window=200_000,
        max_output_tokens=16_384,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        tags=("reasoning", "code", "long-context"),
    ),
    "gpt-4o": ModelSpec(
        model_id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        context_window=128_000,
        max_output_tokens=16_384,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        tags=("general", "multimodal", "fast"),
    ),
    "gpt-4o-mini": ModelSpec(
        model_id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        context_window=128_000,
        max_output_tokens=16_384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        tags=("fast", "cheap"),
    ),
}

# Fallback chain: if primary fails, try next
FALLBACK_CHAIN: dict[str, str] = {
    "claude-sonnet-4-20250514": "gpt-4o",
    "gpt-4o": "claude-sonnet-4-20250514",
    "gpt-4o-mini": "gpt-4o",
}


def get_model_spec(model_id: str) -> ModelSpec | None:
    """Get the spec for a model, or None if unknown."""
    return MODELS.get(model_id)


def list_models() -> list[dict[str, Any]]:
    """List all available models in OpenAI-compatible format."""
    return [
        {
            "id": spec.model_id,
            "object": "model",
            "owned_by": spec.provider,
            "display_name": spec.display_name,
            "context_window": spec.context_window,
            "max_output_tokens": spec.max_output_tokens,
        }
        for spec in MODELS.values()
    ]


def get_fallback(model_id: str) -> str | None:
    """Get the fallback model for a given model."""
    return FALLBACK_CHAIN.get(model_id)


async def invoke_model(
    model_id: str,
    messages: list[BaseMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    anthropic_api_key: str = "",
    openai_api_key: str = "",
    tools: list | None = None,
) -> dict[str, Any]:
    """Invoke an LLM model and return the response.

    Returns:
        dict with keys: content, model, usage (input_tokens, output_tokens),
        and optionally tool_calls (list of dicts with name, args, id)
    """
    spec = MODELS.get(model_id)
    if spec is None:
        raise ValueError(f"Unknown model: {model_id}")

    effective_max = max_tokens or spec.max_output_tokens

    if spec.provider == "anthropic":
        return await _invoke_anthropic(
            spec, messages, temperature, effective_max, anthropic_api_key, tools
        )
    elif spec.provider == "openai":
        return await _invoke_openai(
            spec, messages, temperature, effective_max, openai_api_key, tools
        )
    else:
        raise ValueError(f"Unknown provider: {spec.provider}")


async def _invoke_anthropic(
    spec: ModelSpec,
    messages: list[BaseMessage],
    temperature: float,
    max_tokens: int,
    api_key: str,
    tools: list | None = None,
) -> dict[str, Any]:
    """Invoke Anthropic Claude model."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(
        model=spec.model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )

    if tools:
        llm = llm.bind_tools(tools)

    response = await llm.ainvoke(messages)

    usage = response.usage_metadata or {}
    result: dict[str, Any] = {
        "content": response.content if isinstance(response.content, str) else "",
        "model": spec.model_id,
        "usage": {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
    }

    # Extract tool calls if present
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        result["tool_calls"] = [
            {"name": tc["name"], "args": tc["args"], "id": tc.get("id", "")}
            for tc in tool_calls
        ]
        # When LLM makes tool calls, content may be list or empty
        if not result["content"] and isinstance(response.content, list):
            text_parts = [b["text"] for b in response.content if isinstance(b, dict) and b.get("type") == "text"]
            result["content"] = "\n".join(text_parts)

    return result


async def _invoke_openai(
    spec: ModelSpec,
    messages: list[BaseMessage],
    temperature: float,
    max_tokens: int,
    api_key: str,
    tools: list | None = None,
) -> dict[str, Any]:
    """Invoke OpenAI GPT model."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=spec.model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )

    if tools:
        llm = llm.bind_tools(tools)

    response = await llm.ainvoke(messages)

    usage = response.usage_metadata or {}
    result: dict[str, Any] = {
        "content": response.content if isinstance(response.content, str) else "",
        "model": spec.model_id,
        "usage": {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
    }

    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        result["tool_calls"] = [
            {"name": tc["name"], "args": tc["args"], "id": tc.get("id", "")}
            for tc in tool_calls
        ]

    return result


async def stream_model(
    model_id: str,
    messages: list[BaseMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    anthropic_api_key: str = "",
    openai_api_key: str = "",
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream LLM tokens one at a time.

    Yields:
        dict with either:
        - {"type": "token", "content": "..."} for each token chunk
        - {"type": "done", "model": "...", "usage": {...}} at the end
    """
    spec = MODELS.get(model_id)
    if spec is None:
        raise ValueError(f"Unknown model: {model_id}")

    effective_max = max_tokens or spec.max_output_tokens

    if spec.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=spec.model_id,
            temperature=temperature,
            max_tokens=effective_max,
            api_key=anthropic_api_key,
        )
    elif spec.provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=spec.model_id,
            temperature=temperature,
            max_tokens=effective_max,
            api_key=openai_api_key,
        )
    else:
        raise ValueError(f"Unknown provider: {spec.provider}")

    total_content = ""
    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            total_content += token
            yield {"type": "token", "content": token}

    yield {
        "type": "done",
        "model": spec.model_id,
        "content": total_content,
        "usage": {
            "input_tokens": 0,  # Streaming doesn't always provide usage
            "output_tokens": 0,
        },
    }

