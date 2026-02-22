# Ada Core API

> AI R&D Central Hub — LLM Routing API for RYKNSH records

## Overview

Ada is the intelligent LLM routing layer that powers all RYKNSH subsidiaries. It provides OpenAI-compatible endpoints with multi-provider support, automatic fallback, per-tenant rate limiting, and SSE streaming.

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uv run python main.py

# Run tests
uv run pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat (streaming supported) |
| `POST` | `/v1/route` | Model recommendation without execution |
| `GET`  | `/v1/models` | List available models |
| `GET`  | `/health` | Health check |

## Authentication

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $ADA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## Streaming

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $ADA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

## Supported Models

| Model | Provider | Best For |
|-------|----------|----------|
| `claude-sonnet-4-20250514` | Anthropic | Reasoning, code, long context |
| `gpt-4o` | OpenAI | General, multimodal |
| `gpt-4o-mini` | OpenAI | Fast, cost-efficient |

## Architecture

```
Client → FastAPI (app.py) → Rate Limiter → LangGraph Router → LLM Provider
                                                    ↓
                                              Supabase (usage logs)
```

## Project Structure

```
Ada/
├── agent/          # LLM routing graph, providers, tenant resolution
├── server/         # FastAPI app, config, queue, rate limiting
├── worker/         # Async job consumer
├── tests/          # 52 tests
├── supabase/       # Database migrations
└── main.py         # Entry point
```

## Environment Variables

See [.env.example](.env.example) for all required variables.

## License

Proprietary — RYKNSH records Inc.
