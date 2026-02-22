"""Ada Core API — FastAPI REST API Server."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agent.checkpointer import close_checkpointer, init_checkpointer
from agent.graph import router_graph, rebuild_with_checkpointer, RouterState
from agent.providers import list_models, stream_model
from agent.tenant import TenantConfig, build_thread_id, resolve_tenant_by_api_key
from server.config import get_settings
from server.queue import close_queue, enqueue, init_queue
from worker.consumer import consumer_loop

logger = logging.getLogger(__name__)

# Background worker task
_worker_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    global _worker_task

    # Startup
    checkpointer = await init_checkpointer()
    rebuild_with_checkpointer(checkpointer)

    has_redis = await init_queue()
    if has_redis:
        _worker_task = asyncio.create_task(consumer_loop())
        logger.info("Worker consumer task started")

    logger.info("Ada Core API v0.1.0 started")
    yield

    # Shutdown
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

    await close_queue()
    await close_checkpointer()
    logger.info("Ada Core API stopped")


app = FastAPI(
    title="Ada Core API",
    description="AI R&D Central Hub — LLM Routing API for RYKNSH records",
    version="0.1.0",
    lifespan=lifespan,
)

# Static files (LP)
import pathlib
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_static_dir = pathlib.Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------

async def verify_api_key(
    authorization: str | None = Header(None),
) -> TenantConfig:
    """Extract and verify API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Support "Bearer <key>" format
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    else:
        api_key = authorization

    if not api_key:
        raise HTTPException(status_code=401, detail="Empty API key")

    tenant = await resolve_tenant_by_api_key(api_key)
    return tenant


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    stream: bool = False


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: UsageInfo


class RouteRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None


class RouteResponse(BaseModel):
    recommended_model: str
    reason: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from agent.checkpointer import get_checkpointer
    from server.queue import _redis

    has_checkpointer = get_checkpointer() is not None
    has_redis = _redis is not None
    return {
        "status": "ok",
        "service": "ada-core-api",
        "version": "0.1.0",
        "stateful": has_checkpointer,
        "queue": "redis" if has_redis else "memory",
    }


@app.get("/v1/models")
async def get_models(tenant: TenantConfig = Depends(verify_api_key)):
    """List available models (OpenAI-compatible)."""
    all_models = list_models()
    # Filter by tenant's allowed models
    allowed = set(tenant.allowed_models)
    filtered = [m for m in all_models if m["id"] in allowed]
    return {"object": "list", "data": filtered}


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantConfig = Depends(verify_api_key),
):
    """OpenAI-compatible chat completions endpoint."""
    from server.rate_limit import rate_limiter
    from agent.graph import _convert_messages, select_model
    from server.stripe_billing import stripe_billing

    # Rate limit check
    allowed, retry_after = rate_limiter.check(
        str(tenant.tenant_id), tenant.rate_limit_rpm
    )
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    # Quota check (billing)
    quota = stripe_billing.check_quota(str(tenant.tenant_id))
    if not quota["has_quota"]:
        return JSONResponse(
            status_code=429,
            content={"error": {
                "message": f"Monthly quota exhausted ({quota['request_limit']} requests). Upgrade your plan at /v1/dashboard/billing.",
                "type": "quota_exceeded",
            }},
        )

    # Validate model if specified
    if request.model and request.model not in tenant.allowed_models:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' not allowed for this tenant. "
                   f"Allowed: {list(tenant.allowed_models)}",
        )

    request_id = str(uuid.uuid4())

    # --- Streaming mode ---
    if request.stream:
        # Increment usage before streaming starts
        background_tasks.add_task(stripe_billing.increment_usage, str(tenant.tenant_id))
        return await _handle_streaming(request, tenant, request_id)

    # --- Non-streaming mode ---
    state: RouterState = {
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "model": request.model,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "tenant_id": str(tenant.tenant_id),
        "selected_model": "",
        "langchain_messages": [],
        "response_content": "",
        "response_model": "",
        "usage": {},
        "request_id": request_id,
    }

    thread_id = build_thread_id(tenant.tenant_id, request_id)
    config = {
        "configurable": {
            "thread_id": thread_id,
            "tenant_id": str(tenant.tenant_id),
            "default_model": tenant.default_model,
            "allowed_models": list(tenant.allowed_models),
            "system_prompt_override": tenant.system_prompt_override,
        }
    }

    try:
        result = await router_graph.ainvoke(state, config=config)
    except Exception:
        logger.exception("LLM invocation failed for request %s", request_id)
        raise HTTPException(status_code=502, detail="LLM invocation failed")

    # Increment usage after successful invocation
    background_tasks.add_task(stripe_billing.increment_usage, str(tenant.tenant_id))

    usage = result.get("usage", {})
    return ChatCompletionResponse(
        id=f"chatcmpl-{request_id}",
        created=int(time.time()),
        model=result.get("response_model", "unknown"),
        choices=[
            ChatChoice(
                message=ChatMessage(
                    role="assistant",
                    content=result.get("response_content", ""),
                ),
            )
        ],
        usage=UsageInfo(
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        ),
    )


async def _handle_streaming(
    request: ChatCompletionRequest,
    tenant: TenantConfig,
    request_id: str,
) -> StreamingResponse:
    """Handle streaming chat completions with SSE."""
    from agent.graph import _convert_messages
    from agent.providers import MODELS, get_model_spec
    from server.config import get_settings

    cfg = get_settings()

    # Select model (simplified — no graph, direct selection)
    model_id = request.model or tenant.default_model
    if model_id not in MODELS:
        model_id = tenant.default_model

    # Convert messages
    lc_messages = _convert_messages(
        [{"role": m.role, "content": m.content} for m in request.messages]
    )

    async def sse_generator():
        created = int(time.time())
        try:
            async for chunk in stream_model(
                model_id,
                lc_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                anthropic_api_key=cfg.anthropic_api_key,
                openai_api_key=cfg.openai_api_key,
            ):
                if chunk["type"] == "token":
                    data = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model_id,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk["content"]},
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                elif chunk["type"] == "done":
                    # Final chunk with finish_reason
                    data = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": chunk.get("model", model_id),
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop",
                        }],
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("Streaming error for request %s", request_id)
            error_data = {"error": {"message": str(e), "type": "server_error"}}
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/v1/route")
async def route_model(
    request: RouteRequest,
    tenant: TenantConfig = Depends(verify_api_key),
):
    """Recommend the optimal model without executing (routing-only)."""
    from agent.providers import MODELS

    # Simple heuristic: analyze message length and complexity
    total_chars = sum(len(m.content) for m in request.messages)
    has_code = any(
        keyword in m.content.lower()
        for m in request.messages
        for keyword in ("```", "def ", "function ", "class ", "import ")
    )

    if request.model and request.model in tenant.allowed_models:
        recommended = request.model
        reason = "Explicitly requested model"
    elif has_code or total_chars > 10_000:
        # Long context or code → Claude Sonnet
        recommended = "claude-sonnet-4-20250514"
        reason = "Code analysis or long context detected — Claude Sonnet recommended"
    elif total_chars < 500:
        # Short messages → GPT-4o Mini (cost-efficient)
        recommended = "gpt-4o-mini"
        reason = "Short message — GPT-4o Mini recommended for cost efficiency"
    else:
        recommended = tenant.default_model
        reason = f"Tenant default model ({tenant.default_model})"

    # Ensure recommended model is allowed
    if recommended not in tenant.allowed_models:
        recommended = tenant.default_model
        reason = f"Fallback to tenant default ({tenant.default_model})"

    return RouteResponse(recommended_model=recommended, reason=reason)


# ---------------------------------------------------------------------------
# Landing Page
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def landing_page():
    """Serve the landing page."""
    lp = _static_dir / "index.html"
    if lp.exists():
        return FileResponse(str(lp))
    return {"message": "Ada Core API", "docs": "/docs"}


# ---------------------------------------------------------------------------
# Platform API (Signup, Dashboard, Webhook)
# ---------------------------------------------------------------------------

@app.post("/v1/auth/signup")
async def auth_signup(request_body: dict):
    """New tenant signup."""
    from server.onboarding import signup, SignupRequest
    req = SignupRequest(**request_body)
    return await signup(req)


@app.get("/v1/dashboard/usage")
async def dashboard_usage(tenant: TenantConfig = Depends(verify_api_key)):
    """Get usage stats."""
    from server.dashboard import get_usage
    return await get_usage(tenant.tenant_id)


@app.get("/v1/dashboard/keys")
async def dashboard_keys(tenant: TenantConfig = Depends(verify_api_key)):
    """List API keys."""
    from server.dashboard import list_keys
    return await list_keys(tenant.tenant_id)


@app.post("/v1/dashboard/keys")
async def dashboard_create_key(request_body: dict, tenant: TenantConfig = Depends(verify_api_key)):
    """Create a new API key."""
    from server.dashboard import create_key, KeyCreateRequest
    req = KeyCreateRequest(**request_body)
    return await create_key(tenant.tenant_id, req)


@app.get("/v1/dashboard/billing")
async def dashboard_billing(tenant: TenantConfig = Depends(verify_api_key)):
    """Get billing info."""
    from server.dashboard import get_billing
    return await get_billing(tenant.tenant_id)


@app.get("/v1/catalog")
async def catalog():
    """Get node set catalog (public)."""
    from server.dashboard import get_catalog_api
    return await get_catalog_api()


@app.post("/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    from server.stripe_billing import stripe_billing
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    return await stripe_billing.handle_webhook(payload, sig)
