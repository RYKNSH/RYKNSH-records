"""Ada Core API — Embeddings Generation.

Generates vector embeddings for text using OpenAI's embedding models.
Used by both the ingest pipeline (document registration) and
the retriever (query embedding).

WHITEPAPER ref: Section 3 — context_loader, Section 11 — Supabase pgvector
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Model config
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
OPENAI_EMBEDDING_URL = "https://api.openai.com/v1/embeddings"


async def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a single text.

    Args:
        text: The text to embed.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
        httpx.HTTPStatusError: If the API call fails.
    """
    vectors = await embed_texts([text])
    return vectors[0]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for multiple texts (batch).

    Args:
        texts: List of texts to embed.

    Returns:
        List of embedding vectors, one per input text.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required for embeddings")

    if not texts:
        return []

    # Clean inputs — OpenAI rejects empty strings
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    cleaned = [t if t else " " for t in cleaned]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            OPENAI_EMBEDDING_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": cleaned,
                "model": EMBEDDING_MODEL,
                "dimensions": EMBEDDING_DIMENSIONS,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Sort by index to ensure order matches input
    embeddings = sorted(data["data"], key=lambda x: x["index"])
    vectors = [e["embedding"] for e in embeddings]

    logger.debug("Generated %d embeddings (model=%s)", len(vectors), EMBEDDING_MODEL)
    return vectors
