"""Cyrus LangGraph — Full pipeline graph definition.

Sprint 1: Intelligence Layer (3 nodes)
Sprint 2: + Trust Engine + Outbound + Inbound (3 nodes)
Sprint 3: + Content + Campaign + Viral + Ads (4 nodes)
Sprint 4: + Conversion Pipelines (B2B: 4, B2C: 3, C2C: 3)

Dynamic pipeline selection based on conversion_mode in blueprint:
- b2b: nurture → proposal → meeting → close
- b2c: activation → retention → monetization
- c2c: onboarding → trust_builder → marketplace_growth
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
# B2B Pipeline
from nodes.conversion.nurture_sequencer import nurture_sequencer
from nodes.conversion.proposal_generator import proposal_generator
from nodes.conversion.meeting_setter import meeting_setter
from nodes.conversion.close_advisor import close_advisor
# B2C Pipeline
from nodes.conversion.activation_optimizer import activation_optimizer
from nodes.conversion.retention_looper import retention_looper
from nodes.conversion.monetization_trigger import monetization_trigger
# C2C Pipeline
from nodes.conversion.onboarding_sequencer import onboarding_sequencer
from nodes.conversion.trust_builder import trust_builder
from nodes.conversion.marketplace_growth_driver import marketplace_growth_driver

logger = logging.getLogger(__name__)


def build_intelligence_graph() -> StateGraph:
    """Build the Intelligence Layer graph (Sprint 1)."""
    graph = StateGraph(CyrusState)
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)
    graph.set_entry_point("market_scanner")
    graph.add_edge("market_scanner", "icp_profiler")
    graph.add_edge("icp_profiler", "signal_detector")
    graph.add_edge("signal_detector", END)
    return graph


def _get_conversion_mode(state: CyrusState) -> str:
    """Determine which conversion pipeline to use."""
    blueprint = state.get("blueprint", {})
    conversion_config = blueprint.get("conversion_config", {})
    mode = conversion_config.get("mode", blueprint.get("business_model", "b2b"))
    # B2C high deal_complexity → use B2B pipeline
    if mode == "b2c" and blueprint.get("deal_complexity") == "high":
        return "b2b"
    return mode


def build_growth_graph() -> StateGraph:
    """Build the full growth pipeline with dynamic conversion routing.

    Sprint 1-3: Intelligence → Trust → Acquisition (10 nodes)
    Sprint 4: → Dynamic Conversion Pipeline (3-4 nodes based on mode)
    """
    graph = StateGraph(CyrusState)

    # Intelligence Layer (Sprint 1)
    graph.add_node("market_scanner", market_scanner)
    graph.add_node("icp_profiler", icp_profiler)
    graph.add_node("signal_detector", signal_detector)

    # Trust Engine (Sprint 2)
    graph.add_node("trust_engine", trust_engine)

    # Acquisition Layer (Sprint 2+3)
    graph.add_node("outbound_personalizer", outbound_personalizer)
    graph.add_node("inbound_magnet", inbound_magnet)
    graph.add_node("content_architect", content_architect)
    graph.add_node("viral_engineer", viral_engineer)
    graph.add_node("campaign_orchestrator", campaign_orchestrator)
    graph.add_node("ad_optimizer", ad_optimizer)

    # B2B Conversion Pipeline (Sprint 4)
    graph.add_node("nurture_sequencer", nurture_sequencer)
    graph.add_node("proposal_generator", proposal_generator)
    graph.add_node("meeting_setter", meeting_setter)
    graph.add_node("close_advisor", close_advisor)

    # B2C Conversion Pipeline (Sprint 4)
    graph.add_node("activation_optimizer", activation_optimizer)
    graph.add_node("retention_looper", retention_looper)
    graph.add_node("monetization_trigger", monetization_trigger)

    # C2C Conversion Pipeline (Sprint 4)
    graph.add_node("onboarding_sequencer", onboarding_sequencer)
    graph.add_node("trust_builder", trust_builder)
    graph.add_node("marketplace_growth_driver", marketplace_growth_driver)

    # Intelligence → Trust → Acquisition (sequential)
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

    # Dynamic routing: ad_optimizer → conversion pipeline based on mode
    graph.add_conditional_edges(
        "ad_optimizer",
        _get_conversion_mode,
        {
            "b2b": "nurture_sequencer",
            "b2c": "activation_optimizer",
            "c2c": "onboarding_sequencer",
        },
    )

    # B2B Pipeline edges
    graph.add_edge("nurture_sequencer", "proposal_generator")
    graph.add_edge("proposal_generator", "meeting_setter")
    graph.add_edge("meeting_setter", "close_advisor")
    graph.add_edge("close_advisor", END)

    # B2C Pipeline edges
    graph.add_edge("activation_optimizer", "retention_looper")
    graph.add_edge("retention_looper", "monetization_trigger")
    graph.add_edge("monetization_trigger", END)

    # C2C Pipeline edges
    graph.add_edge("onboarding_sequencer", "trust_builder")
    graph.add_edge("trust_builder", "marketplace_growth_driver")
    graph.add_edge("marketplace_growth_driver", END)

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
    """Execute the full growth pipeline with dynamic conversion routing."""
    initial_state: CyrusState = {
        "blueprint": blueprint,
        "tenant_id": blueprint.get("tenant_id", ""),
        "current_layer": "intelligence",
        "current_node": "",
        "node_metrics": [],
        "errors": [],
    }
    return await growth_graph.ainvoke(initial_state)
