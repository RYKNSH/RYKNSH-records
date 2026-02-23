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

    # --- Trust Engine outputs ---
    trust_scores: dict[str, Any]
    trust_engine_output: dict[str, Any]

    # --- Acquisition Layer outputs ---
    outbound_messages: list[dict[str, Any]]
    outbound_status: str
    defer_reason: str
    inbound_magnets: list[dict[str, Any]]
    inbound_schedule: dict[str, Any]
    content_plan: list[dict[str, Any]]
    content_calendar: dict[str, Any]
    campaign: dict[str, Any]
    viral_strategies: list[dict[str, Any]]
    trend_signals: list[dict[str, Any]]
    ad_plan: dict[str, Any]
    generated_content: list[dict[str, Any]]
    qualified_leads: list[dict[str, Any]]

    # --- Conversion Layer outputs ---
    # B2B Pipeline
    nurture_sequence: dict[str, Any]
    proposal: dict[str, Any]
    meeting: dict[str, Any]
    close_strategy: dict[str, Any]
    # B2C Pipeline
    activation: dict[str, Any]
    retention_plan: dict[str, Any]
    monetization: dict[str, Any]
    # C2C Pipeline
    onboarding: dict[str, Any]
    trust_building: dict[str, Any]
    marketplace_strategy: dict[str, Any]
    pipeline_results: list[dict[str, Any]]

    # --- Evolution Layer outputs ---
    performance_metrics: dict[str, Any]
    optimization_actions: list[dict[str, Any]]

    # --- Meta ---
    current_layer: str
    current_node: str
    node_metrics: list[dict[str, Any]]
    errors: list[str]

