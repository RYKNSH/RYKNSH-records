"""Ada Core API — LangGraph LLM Router Graph.

Execution Layer pipeline:
- sentinel → select_model → invoke_llm → [tools?] → log_usage

Sentinel blocks dangerous inputs before any LLM processing.
"""

import logging
import uuid
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.tools import StructuredTool
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

    # Sentinel (gate check)
    sentinel_passed: bool
    sentinel_reason: str
    sentinel_risk_score: float

    # Context loader (RAG + system prompt)
    rag_context: list[dict[str, Any]]
    rag_query: str
    system_prompt_enriched: str | None

    # Internal
    selected_model: str
    langchain_messages: list[BaseMessage]

    # Tool support (ReAct pattern)
    tool_calls: list[dict[str, Any]]  # Pending tool calls from LLM
    tool_results: list[BaseMessage]  # Tool execution results

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

    # Inject enriched system prompt (from context_loader: system + RAG)
    system_prompt = state.get("system_prompt_enriched")
    if system_prompt:
        lc_messages.insert(0, SystemMessage(content=system_prompt))
        logger.info("Enriched system prompt injected (includes RAG context)")

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
    """Invoke the selected LLM provider with automatic fallback.

    Supports tool binding: if tools are provided via config, the LLM
    may return tool_calls instead of a direct response.
    """
    from agent.providers import get_fallback, invoke_model
    from server.config import get_settings

    cfg = get_settings()
    model_id = state["selected_model"]
    messages = list(state["langchain_messages"])
    temperature = state.get("temperature", 0.7)
    max_tokens = state.get("max_tokens")

    # Append tool results from previous iteration (ReAct loop)
    tool_results = state.get("tool_results", [])
    if tool_results:
        messages.extend(tool_results)

    # Get tools from config (if any)
    tools = None
    if config and "configurable" in config:
        tools = config["configurable"].get("tools")

    try:
        result = await invoke_model(
            model_id,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=cfg.anthropic_api_key,
            openai_api_key=cfg.openai_api_key,
            tools=tools,
        )

        output: dict[str, Any] = {
            "response_content": result["content"],
            "response_model": result["model"],
            "usage": result["usage"],
            "tool_calls": result.get("tool_calls", []),
            "tool_results": [],  # Reset for next iteration
        }
        return output

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
                    tools=tools,
                )
                output = {
                    "response_content": result["content"],
                    "response_model": result["model"],
                    "usage": result["usage"],
                    "tool_calls": result.get("tool_calls", []),
                    "tool_results": [],
                }
                return output
            except Exception as fallback_err:
                logger.error("Fallback model %s also failed: %s", fallback_id, fallback_err)
                raise fallback_err from primary_err

        raise


def should_use_tools(state: RouterState) -> str:
    """Conditional edge: route to tool execution or logging."""
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        return "execute_tools"
    return "log_usage"


async def execute_tools(state: RouterState, config: RunnableConfig | None = None) -> dict:
    """Execute pending tool calls and return results.

    Looks up tools from config and executes each tool_call.
    Results are stored as ToolMessages for the next LLM invocation.
    """
    from langchain_core.messages import ToolMessage

    tool_calls = state.get("tool_calls", [])
    tools_map: dict[str, StructuredTool] = {}

    if config and "configurable" in config:
        lc_tools = config["configurable"].get("tools", [])
        tools_map = {t.name: t for t in (lc_tools or [])}

    results: list[BaseMessage] = []

    for tc in tool_calls:
        tool_name = tc.get("name", "")
        tool_args = tc.get("args", {})
        tool_id = tc.get("id", str(uuid.uuid4()))

        if tool_name in tools_map:
            try:
                tool = tools_map[tool_name]
                result = await tool.ainvoke(tool_args)
                results.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id,
                ))
                logger.info("Tool executed: %s -> %d chars", tool_name, len(str(result)))
            except Exception:
                logger.exception("Tool execution failed: %s", tool_name)
                results.append(ToolMessage(
                    content=f"Error executing tool {tool_name}",
                    tool_call_id=tool_id,
                ))
        else:
            logger.warning("Tool not found: %s", tool_name)
            results.append(ToolMessage(
                content=f"Tool not found: {tool_name}",
                tool_call_id=tool_id,
            ))

    return {
        "tool_results": results,
        "tool_calls": [],  # Clear pending calls
    }


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

def _sentinel_blocked_response(state: RouterState) -> dict:
    """Generate an error response when sentinel blocks a request."""
    return {
        "response_content": (
            "Your request was blocked by our safety system. "
            "Please rephrase your message and try again."
        ),
        "response_model": "sentinel",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "request_id": state.get("request_id", str(uuid.uuid4())),
    }


def _should_proceed_after_sentinel(state: RouterState) -> str:
    """Conditional edge: proceed to context_loader or block."""
    if state.get("sentinel_passed", True):
        return "context_loader"
    return "sentinel_blocked"


def build_router_graph(
    checkpointer: AsyncPostgresSaver | None = None,
    tools: list[StructuredTool] | None = None,
) -> StateGraph:
    """Build the LLM router graph.

    Pipeline: sentinel → context_loader → select_model → invoke_llm → [tools?] → log_usage → END
    If sentinel blocks: sentinel → sentinel_blocked → END

    Args:
        checkpointer: Optional AsyncPostgresSaver for stateful persistence.
        tools: Optional list of LangChain StructuredTools for ReAct pattern.
    """
    from agent.nodes.sentinel import sentinel_node
    from agent.nodes.context_loader import context_loader_node

    graph = StateGraph(RouterState)

    # Sentinel gate
    graph.add_node("sentinel", sentinel_node.as_graph_node())
    graph.add_node("sentinel_blocked", _sentinel_blocked_response)

    # Context enrichment (RAG + system prompt)
    graph.add_node("context_loader", context_loader_node.as_graph_node())

    # Core nodes
    graph.add_node("select_model", select_model)
    graph.add_node("invoke_llm", invoke_llm)
    graph.add_node("log_usage", log_usage)

    # Entry: sentinel first
    graph.set_entry_point("sentinel")
    graph.add_conditional_edges(
        "sentinel",
        _should_proceed_after_sentinel,
        {"context_loader": "context_loader", "sentinel_blocked": "sentinel_blocked"},
    )
    graph.add_edge("sentinel_blocked", END)

    # context_loader → select_model
    graph.add_edge("context_loader", "select_model")
    graph.add_edge("select_model", "invoke_llm")

    if tools:
        # ReAct pattern: invoke_llm may return tool_calls
        graph.add_node("execute_tools", execute_tools)
        graph.add_conditional_edges(
            "invoke_llm",
            should_use_tools,
            {"execute_tools": "execute_tools", "log_usage": "log_usage"},
        )
        graph.add_edge("execute_tools", "invoke_llm")  # Loop back
    else:
        # Simple linear flow (backward compatible)
        graph.add_edge("invoke_llm", "log_usage")

    graph.add_edge("log_usage", END)

    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer

    return graph.compile(**compile_kwargs)


# Compiled graph — starts stateless, rebuilt with checkpointer via lifespan
router_graph = build_router_graph()


def rebuild_with_checkpointer(
    checkpointer: AsyncPostgresSaver | None,
    tools: list[StructuredTool] | None = None,
) -> None:
    """Rebuild the global router_graph with a checkpointer (called during lifespan)."""
    global router_graph
    if checkpointer:
        router_graph = build_router_graph(checkpointer, tools=tools)
        logger.info("Router graph rebuilt with checkpointer (tools=%d)", len(tools or []))
