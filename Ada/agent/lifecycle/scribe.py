"""Ada Core API — Scribe Node.

Final node in the Lifecycle pipeline. Converts all upstream results
into an AgentBlueprint and persists to storage.

Pipeline: goal_intake → researcher → debater → architect → scribe

WHITEPAPER ref: Section 2 — scribe永続化
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from agent.lifecycle.blueprint import AgentBlueprint, PriorityWeights
from agent.lifecycle.blueprint_store import blueprint_store

logger = logging.getLogger(__name__)


async def generate_blueprint(
    tenant_id: str,
    goal_result: dict[str, Any],
    research_result: dict[str, Any],
    debate_result: dict[str, Any],
    architect_result: dict[str, Any],
    name: str = "default",
) -> AgentBlueprint:
    """Generate an AgentBlueprint from all lifecycle stage results.

    This is the culmination of the Lifecycle pipeline.
    """
    weights = architect_result.get("priority_weights", PriorityWeights())
    if isinstance(weights, dict):
        weights = PriorityWeights(**weights)

    blueprint = AgentBlueprint(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        persona=_build_persona(goal_result, debate_result),
        system_prompt=architect_result.get("system_prompt", ""),
        priority_weights=weights,
        allowed_models=architect_result.get("allowed_models", []),
        default_model=architect_result.get("default_model", "claude-sonnet-4-20250514"),
        temperature=architect_result.get("temperature", 0.7),
        tools=architect_result.get("tools", []),
        quality_tier=architect_result.get("quality_tier", "standard"),
        rag_enabled=architect_result.get("rag_enabled", True),
        metadata={
            "task_type": goal_result.get("task_type", "qa"),
            "required_skills": goal_result.get("required_skills", []),
            "consensus_score": debate_result.get("consensus", {}).get("consensus_score", 0.0),
            "research_count": research_result.get("unique_count", 0),
        },
    )

    logger.info(
        "Blueprint generated: %s (tenant=%s, model=%s, tier=%s)",
        blueprint.name, tenant_id, blueprint.default_model, blueprint.quality_tier,
    )

    return blueprint


def _build_persona(
    goal_result: dict[str, Any],
    debate_result: dict[str, Any],
) -> str:
    """Build persona description from goal and debate results."""
    task_type = goal_result.get("task_type", "qa")
    consensus = debate_result.get("consensus", {})
    recs = consensus.get("merged_recommendations", [])

    persona_bases = {
        "code": "Expert software engineer focused on clean, secure, production-quality code.",
        "analysis": "Analytical thinker providing evidence-based insights.",
        "creative": "Creative professional with a distinctive, engaging voice.",
        "qa": "Knowledgeable assistant committed to accurate, clear answers.",
    }

    persona = persona_bases.get(task_type, persona_bases["qa"])
    if recs:
        persona += " Values: " + ", ".join(recs[:3]).lower() + "."

    return persona


async def scribe(
    tenant_id: str,
    goal_result: dict[str, Any],
    research_result: dict[str, Any],
    debate_result: dict[str, Any],
    architect_result: dict[str, Any],
    name: str = "default",
    persist: bool = True,
) -> AgentBlueprint:
    """Execute the scribe: generate and optionally persist a blueprint.

    This is the main entry point for the scribe node.
    """
    blueprint = await generate_blueprint(
        tenant_id=tenant_id,
        goal_result=goal_result,
        research_result=research_result,
        debate_result=debate_result,
        architect_result=architect_result,
        name=name,
    )

    if persist:
        blueprint = await blueprint_store.save(blueprint)
        logger.info("Blueprint persisted: %s v%d", blueprint.name, blueprint.version)

    return blueprint
