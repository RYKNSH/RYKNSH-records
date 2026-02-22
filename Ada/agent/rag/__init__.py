"""Ada Core API — RAG Package.

Retrieval-Augmented Generation pipeline for context enrichment.
"""

from agent.rag.embeddings import embed_text, embed_texts
from agent.rag.retriever import retrieve

__all__ = ["embed_text", "embed_texts", "retrieve"]
