"""Ada Core API — LangGraph LLM Router Graph.

The core loop: select_model → invoke_llm → log_usage
"""

import logging
import uuid
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class RouterState(TypedDict):
    """State that flows through the LLM router graph."""

    # Input
    messages: list[dict[str, str]]  # OpenAI-compatible message format
    model: str | None  # Requested model (None = auto-select)
    temperature: float
    max_tokens: int | None
    tenant_id: str

    # Internal
    selected_model: str
    langchain_messages: list[BaseMessage]

    # Output
    response_content: str
    response_model: str
    usage: dict[str, int]
    request_id: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def select_model(state: RouterState, config: RunnableConfig | None = None) -> dict:
    """Select the optimal LLM model based on request and tenant config.

    Priority:
    1. Explicitly requested model (if in allowed_models)
    2. Tenant's default_model
    3. Fallback to claude-sonnet-4-20250514
    """
    from agent.providers import MODELS, get_fallback

    requested = state.get("model")
    tenant_default = "claude-sonnet-4-20250514"

    # Extract tenant config from RunnableConfig
    if config and "configurable" in config:
        tenant_default = config["configurable"].get("default_model", tenant_default)
        allowed = config["configurable"].get("allowed_models", list(MODELS.keys()))
    else:
        allowed = list(MODELS.keys())

    # Resolve model
    if requested and requested in MODELS and requested in allowed:
        selected = requested
    elif tenant_default in MODELS:
        selected = tenant_default
    else:
        selected = "claude-sonnet-4-20250514"

    # Convert OpenAI-format messages to LangChain messages
    lc_messages = _convert_messages(state["messages"])

    request_id = str(uuid.uuid4())

    logger.info(
        "Model selected: %s (requested=%s, tenant_default=%s, request=%s)",
        selected, requested, tenant_default, request_id,
    )

    return {
        "selected_model": selected,
        "langchain_messages": lc_messages,
        "request_id": request_id,
    }


async def invoke_llm(state: RouterState, config: RunnableConfig | None = None) -> dict:
    """Invoke the selected LLM provider with automatic fallback."""
    from agent.providers import get_fallback, invoke_model
    from server.config import get_settings

    cfg = get_settings()
    model_id = state["selected_model"]
    messages = state["langchain_messages"]
    temperature = state.get("temperature", 0.7)
    max_tokens = state.get("max_tokens")

    try:
        result = await invoke_model(
            model_id,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=cfg.anthropic_api_key,
            openai_api_key=cfg.openai_api_key,
        )
        return {
            "response_content": result["content"],
            "response_model": result["model"],
            "usage": result["usage"],
        }

    except Exception as primary_err:
        # Automatic fallback
        fallback_id = get_fallback(model_id)
        if fallback_id:
            logger.warning(
                "Primary model %s failed, falling back to %s: %s",
                model_id, fallback_id, primary_err,
            )
            try:
                result = await invoke_model(
                    fallback_id,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    anthropic_api_key=cfg.anthropic_api_key,
                    openai_api_key=cfg.openai_api_key,
                )
                return {
                    "response_content": result["content"],
                    "response_model": result["model"],
                    "usage": result["usage"],
                }
            except Exception as fallback_err:
                logger.error("Fallback model %s also failed: %s", fallback_id, fallback_err)
                raise fallback_err from primary_err

        raise


async def log_usage(state: RouterState) -> dict:
    """Log usage metrics to Supabase for billing and analytics."""
    from server.config import get_settings

    cfg = get_settings()
    usage = state.get("usage", {})
    tenant_id = state.get("tenant_id", "unknown")
    model = state.get("response_model", "unknown")
    request_id = state.get("request_id", "unknown")

    logger.info(
        "Usage: tenant=%s model=%s input=%d output=%d request=%s",
        tenant_id, model,
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
        request_id,
    )

    # Persist to Supabase if configured
    if cfg.supabase_url and cfg.supabase_anon_key:
        try:
            url = f"{cfg.supabase_url}/rest/v1/ada_usage_logs"
            headers = {
                "apikey": cfg.supabase_anon_key,
                "Authorization": f"Bearer {cfg.supabase_anon_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
            payload = {
                "tenant_id": tenant_id,
                "model": model,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "request_id": request_id,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()

            logger.debug("Usage logged to Supabase for request %s", request_id)
        except Exception:
            logger.warning("Failed to log usage to Supabase (non-fatal)", exc_info=True)

    return {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _convert_messages(messages: list[dict[str, str]]) -> list[BaseMessage]:
    """Convert OpenAI-format messages to LangChain message objects."""
    converted: list[BaseMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

def build_router_graph(checkpointer: AsyncPostgresSaver | None = None) -> StateGraph:
    """Build the LLM router graph: select_model → invoke_llm → log_usage.

    Args:
        checkpointer: Optional AsyncPostgresSaver for stateful persistence.
                      If None, the graph runs in stateless mode.
    """
    graph = StateGraph(RouterState)

    graph.add_node("select_model", select_model)
    graph.add_node("invoke_llm", invoke_llm)
    graph.add_node("log_usage", log_usage)

    graph.set_entry_point("select_model")
    graph.add_edge("select_model", "invoke_llm")
    graph.add_edge("invoke_llm", "log_usage")
    graph.add_edge("log_usage", END)

    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer

    return graph.compile(**compile_kwargs)


# Compiled graph — starts stateless, rebuilt with checkpointer via lifespan
router_graph = build_router_graph()


def rebuild_with_checkpointer(checkpointer: AsyncPostgresSaver | None) -> None:
    """Rebuild the global router_graph with a checkpointer (called during lifespan)."""
    global router_graph
    if checkpointer:
        router_graph = build_router_graph(checkpointer)
        logger.info("Router graph rebuilt with checkpointer")
