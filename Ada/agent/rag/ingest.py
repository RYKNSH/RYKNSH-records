"""Ada Core API — Document Ingestion Pipeline.

Ingests documents into the Supabase pgvector store for RAG retrieval.
Pipeline: text → chunk → embed → insert.

WHITEPAPER ref: Section 3 — context_loader
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx

from agent.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)

# Default chunking config
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks.

    Simple character-based splitting with overlap for context continuity.

    Args:
        text: The text to split.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the end
            for boundary in [". ", ".\n", "! ", "!\n", "? ", "?\n", "\n\n"]:
                last_boundary = text[start:end].rfind(boundary)
                if last_boundary > chunk_size * 0.5:
                    end = start + last_boundary + len(boundary)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


async def ingest_document(
    content: str,
    metadata: dict[str, Any],
    tenant_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """Ingest a document into the vector store.

    Pipeline: text → chunk → embed → insert into Supabase.

    Args:
        content: The full document text.
        metadata: Document metadata (title, source, etc.).
        tenant_id: Tenant ID for RLS.
        chunk_size: Characters per chunk.

    Returns:
        Number of chunks inserted.

    Raises:
        ValueError: If Supabase is not configured.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY required for ingestion")

    # Chunk the document
    chunks = chunk_text(content, chunk_size=chunk_size)
    if not chunks:
        logger.warning("No chunks generated from document")
        return 0

    # Generate embeddings for all chunks
    vectors = await embed_texts(chunks)

    # Prepare rows for Supabase insert
    doc_id = str(uuid.uuid4())
    rows = [
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "tenant_id": tenant_id,
            "content": chunk,
            "embedding": vector,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        }
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    # Insert into Supabase
    url = f"{supabase_url}/rest/v1/ada_documents"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=rows)
        resp.raise_for_status()

    logger.info(
        "Ingested document: %d chunks (doc_id=%s, tenant=%s)",
        len(chunks), doc_id, tenant_id,
    )
    return len(chunks)
