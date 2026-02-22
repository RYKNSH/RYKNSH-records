"""Cyrus LangGraph — Full pipeline graph definition.

Sprint 1: Intelligence Layer only
Sprint 2: + Trust Engine + Outbound + Inbound

Pipeline:
  market_scanner → icp_profiler → signal_detector
    → trust_engine → outbound_personalizer
                   → inbound_magnet
    → END
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from engine.state import CyrusState
from nodes.intelligence.market_scanner import market_scanner
from nodes.intelligence.icp_profiler import icp_profiler
from nodes.intelligence.signal_detector import signal_detector
from nodes.conversion.trust_engine import trust_engine
from nodes.acquisition.outbound_personalizer import outbound_personalizer
from nodes.acquisition.inbound_magnet import inbound_magnet

logger = logging.getLogger(__name__)


def build_intelligence_graph() -> StateGraph:
    """Build the Intelligence Layer graph (Sprint 1).

    Pipeline: market_scanner → icp_profiler → signal_detector → END
    """
    graph = StateGraph(CyrusState)
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)

    graph.set_entry_point("market_scanner")
    graph.add_edge("market_scanner", "icp_profiler")
    graph.add_edge("icp_profiler", "signal_detector")
    graph.add_edge("signal_detector", END)

    return graph


def build_growth_graph() -> StateGraph:
    """Build the full growth pipeline graph (Sprint 2+).

    Pipeline:
      market_scanner → icp_profiler → signal_detector
        → trust_engine → outbound_personalizer → inbound_magnet → END
    """
    graph = StateGraph(CyrusState)

    # Intelligence Layer
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)

    # Trust Engine (Conversion cross-layer)
    graph.add_node("trust_engine", trust_engine)

    # Acquisition Layer
    graph.add_node("outbound_personalizer", outbound_personalizer)
    graph.add_node("inbound_magnet", inbound_magnet)

    # Intelligence pipeline
    graph.set_entry_point("market_scanner")
    graph.add_edge("market_scanner", "icp_profiler")
    graph.add_edge("icp_profiler", "signal_detector")

    # Intelligence → Trust Engine → Acquisition (sequential)
    graph.add_edge("signal_detector", "trust_engine")
    graph.add_edge("trust_engine", "outbound_personalizer")
    graph.add_edge("outbound_personalizer", "inbound_magnet")
    graph.add_edge("inbound_magnet", END)

    return graph


# Compiled graphs
intelligence_graph = build_intelligence_graph().compile()
growth_graph = build_growth_graph().compile()


async def run_intelligence(blueprint: dict) -> CyrusState:
    """Execute Intelligence Layer only."""
    initial_state: CyrusState = {
        "blueprint": blueprint,
        "tenant_id": blueprint.get("tenant_id", ""),
        "current_layer": "intelligence",
        "current_node": "",
        "node_metrics": [],
        "errors": [],
    }
    return await intelligence_graph.ainvoke(initial_state)


async def run_growth(blueprint: dict) -> CyrusState:
    """Execute the full growth pipeline (Intelligence + Trust + Acquisition)."""
    initial_state: CyrusState = {
        "blueprint": blueprint,
        "tenant_id": blueprint.get("tenant_id", ""),
        "current_layer": "intelligence",
        "current_node": "",
        "node_metrics": [],
        "errors": [],
    }
    return await growth_graph.ainvoke(initial_state)
