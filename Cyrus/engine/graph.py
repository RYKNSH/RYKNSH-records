"""Cyrus LangGraph — Full pipeline graph definition.

Sprint 1: Intelligence Layer (3 nodes)
Sprint 2: + Trust Engine + Outbound + Inbound (3 nodes)
Sprint 3: + Content + Campaign + Viral + Ads (4 nodes)

Full Pipeline (10 nodes):
  market_scanner → icp_profiler → signal_detector
    → trust_engine → outbound_personalizer → inbound_magnet
    → content_architect → viral_engineer → campaign_orchestrator → ad_optimizer
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
from nodes.acquisition.content_architect import content_architect
from nodes.acquisition.campaign_orchestrator import campaign_orchestrator
from nodes.acquisition.viral_engineer import viral_engineer
from nodes.acquisition.ad_optimizer import ad_optimizer

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
    """Build the full growth pipeline graph (Sprint 3).

    10-node sequential pipeline:
    Intelligence → Trust → Outbound → Inbound → Content → Viral → Campaign → Ads → END
    """
    graph = StateGraph(CyrusState)

    # Intelligence Layer (Sprint 1)
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)

    # Trust Engine (Sprint 2)
    graph.add_node("trust_engine", trust_engine)

    # Acquisition Layer (Sprint 2)
    graph.add_node("outbound_personalizer", outbound_personalizer)
    graph.add_node("inbound_magnet", inbound_magnet)

    # Content & Campaign (Sprint 3)
    graph.add_node("content_architect", content_architect)
    graph.add_node("viral_engineer", viral_engineer)
    graph.add_node("campaign_orchestrator", campaign_orchestrator)
    graph.add_node("ad_optimizer", ad_optimizer)

    # Sequential pipeline
    graph.set_entry_point("market_scanner")
    graph.add_edge("market_scanner", "icp_profiler")
    graph.add_edge("icp_profiler", "signal_detector")
    graph.add_edge("signal_detector", "trust_engine")
    graph.add_edge("trust_engine", "outbound_personalizer")
    graph.add_edge("outbound_personalizer", "inbound_magnet")
    graph.add_edge("inbound_magnet", "content_architect")
    graph.add_edge("content_architect", "viral_engineer")
    graph.add_edge("viral_engineer", "campaign_orchestrator")
    graph.add_edge("campaign_orchestrator", "ad_optimizer")
    graph.add_edge("ad_optimizer", END)

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
    """Execute the full growth pipeline (10 nodes)."""
    initial_state: CyrusState = {
        "blueprint": blueprint,
        "tenant_id": blueprint.get("tenant_id", ""),
        "current_layer": "intelligence",
        "current_node": "",
        "node_metrics": [],
        "errors": [],
    }
    return await growth_graph.ainvoke(initial_state)
