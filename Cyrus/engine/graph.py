"""Cyrus LangGraph — Intelligence Layer graph definition.

Pipeline: market_scanner → icp_profiler → signal_detector → END
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from engine.state import CyrusState
from nodes.intelligence.market_scanner import market_scanner
from nodes.intelligence.icp_profiler import icp_profiler
from nodes.intelligence.signal_detector import signal_detector

logger = logging.getLogger(__name__)


def build_intelligence_graph() -> StateGraph:
    """Build the Intelligence Layer graph.

    Pipeline: market_scanner → icp_profiler → signal_detector → END

    This graph takes a GrowthBlueprint as input and produces:
    - market_data: Market trends, competitors, opportunities
    - icp_profiles: Ideal customer/consumer/creator profiles
    - detected_signals: Actionable purchase/engagement signals
    """
    graph = StateGraph(CyrusState)

    # Add nodes
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)

    # Define edges (linear pipeline for Intelligence Layer)
    graph.set_entry_point("market_scanner")
    graph.add_edge("market_scanner", "icp_profiler")
    graph.add_edge("icp_profiler", "signal_detector")
    graph.add_edge("signal_detector", END)

    return graph


# Pre-compiled graph (stateless — no checkpointer for now)
intelligence_graph = build_intelligence_graph().compile()


async def run_intelligence(blueprint: dict) -> CyrusState:
    """Execute the Intelligence Layer pipeline.

    Args:
        blueprint: GrowthBlueprint dict defining the growth strategy.

    Returns:
        Final CyrusState with market_data, icp_profiles, detected_signals.
    """
    initial_state: CyrusState = {
        "blueprint": blueprint,
        "tenant_id": blueprint.get("tenant_id", ""),
        "current_layer": "intelligence",
        "current_node": "",
        "node_metrics": [],
        "errors": [],
    }

    result = await intelligence_graph.ainvoke(initial_state)
    return result
