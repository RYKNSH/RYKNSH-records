"""CyrusState — State that flows through the LangGraph growth engine."""

from __future__ import annotations

from typing import Any, TypedDict


class CyrusState(TypedDict, total=False):
    """State flowing through the Cyrus LangGraph pipeline.

    Each layer reads from and writes to this shared state.
    """

    # --- Blueprint (input) ---
    blueprint: dict[str, Any]
    tenant_id: str

    # --- Intelligence Layer outputs ---
    market_data: dict[str, Any]
    icp_profiles: list[dict[str, Any]]
    detected_signals: list[dict[str, Any]]

    # --- Acquisition Layer outputs ---
    generated_content: list[dict[str, Any]]
    qualified_leads: list[dict[str, Any]]

    # --- Conversion Layer outputs ---
    trust_scores: dict[str, float]
    pipeline_results: list[dict[str, Any]]

    # --- Evolution Layer outputs ---
    performance_metrics: dict[str, Any]
    optimization_actions: list[dict[str, Any]]

    # --- Meta ---
    current_layer: str
    current_node: str
    node_metrics: list[dict[str, Any]]
    errors: list[str]
