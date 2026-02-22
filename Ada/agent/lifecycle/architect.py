"""Ada Core API — Architect Node.

Makes design decisions based on debate consensus, applying priority weights
and selecting tools/models for the execution plan.

Part of the Lifecycle pipeline: debater → architect → scribe.

WHITEPAPER ref: Section 2 — architect, Section 4 — Priority Weights
"""

from __future__ import annotations

import logging
from typing import Any

from agent.lifecycle.blueprint import PriorityWeights

logger = logging.getLogger(__name__)


# Model recommendations by task type
MODEL_RECOMMENDATIONS: dict[str, str] = {
    "code": "claude-sonnet-4-20250514",
    "analysis": "gpt-4o",
    "creative": "claude-sonnet-4-20250514",
    "qa": "gpt-4o-mini",
}

# Temperature recommendations by task type
TEMP_RECOMMENDATIONS: dict[str, float] = {
    "code": 0.2,
    "analysis": 0.4,
    "creative": 0.8,
    "qa": 0.5,
}

# Tool recommendations by skill
TOOL_RECOMMENDATIONS: dict[str, list[str]] = {
    "programming": ["code_executor", "linter"],
    "web_development": ["code_executor", "browser"],
    "data_analysis": ["code_executor", "data_tools"],
    "research": ["web_search", "rag"],
    "writing": ["grammar_check"],
    "design": ["diagram_generator"],
}


def design_execution_plan(
    goal_result: dict[str, Any],
    debate_result: dict[str, Any],
) -> dict[str, Any]:
    """Create an execution plan from goal analysis and debate consensus.

    Returns a complete design specification for the scribe to convert
    into an AgentBlueprint.
    """
    task_type = goal_result.get("task_type", "qa")
    skills = goal_result.get("required_skills", [])
    consensus = debate_result.get("consensus", {})
    merged_weights = consensus.get("merged_weights", {})
    recommendations = consensus.get("merged_recommendations", [])

    # 1. Apply priority weights
    weights = PriorityWeights(
        quality=merged_weights.get("quality", 0.4),
        efficiency=merged_weights.get("efficiency", 0.3),
        speed=merged_weights.get("speed", 0.2),
        cost=merged_weights.get("cost", 0.1),
    )

    # 2. Select model
    default_model = MODEL_RECOMMENDATIONS.get(task_type, "claude-sonnet-4-20250514")

    # Adjust model based on priority weights
    if weights.cost > 0.3:
        default_model = "gpt-4o-mini"  # Cost-optimized
    elif weights.quality > 0.5:
        default_model = "claude-sonnet-4-20250514"  # Quality-optimized

    # 3. Set temperature
    temperature = TEMP_RECOMMENDATIONS.get(task_type, 0.5)

    # 4. Select tools
    tools: list[str] = []
    for skill in skills:
        skill_tools = TOOL_RECOMMENDATIONS.get(skill, [])
        tools.extend(t for t in skill_tools if t not in tools)

    # 5. Determine quality tier
    quality_tier = goal_result.get("quality_tier", "standard")

    # 6. RAG decision
    rag_enabled = "research" in skills or task_type in ("qa", "analysis")

    # 7. Generate system prompt based on task type and recommendations
    system_prompt = _generate_system_prompt(
        task_type, recommendations, quality_tier,
    )

    plan = {
        "priority_weights": weights,
        "default_model": default_model,
        "allowed_models": ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"],
        "temperature": temperature,
        "tools": tools,
        "quality_tier": quality_tier,
        "rag_enabled": rag_enabled,
        "system_prompt": system_prompt,
        "recommendations": recommendations,
    }

    logger.info(
        "Architect: model=%s, temp=%.1f, tools=%d, tier=%s, rag=%s",
        default_model, temperature, len(tools), quality_tier, rag_enabled,
    )

    return plan


def _generate_system_prompt(
    task_type: str,
    recommendations: list[str],
    quality_tier: str,
) -> str:
    """Generate a task-specific system prompt."""
    base_prompts = {
        "code": "You are an expert software engineer. Write clean, well-tested, production-quality code.",
        "analysis": "You are a data analyst. Provide thorough, evidence-based analysis with clear conclusions.",
        "creative": "You are a creative writer. Craft engaging, original content with a distinctive voice.",
        "qa": "You are a knowledgeable assistant. Provide accurate, clear, and helpful answers.",
    }

    prompt = base_prompts.get(task_type, base_prompts["qa"])

    # Add quality tier context
    tier_additions = {
        "light": "\nKeep responses concise and focused.",
        "standard": "\nProvide balanced depth and clarity.",
        "full": "\nProvide comprehensive, detailed responses with thorough coverage.",
    }
    prompt += tier_additions.get(quality_tier, "")

    # Add top recommendations as guidelines
    if recommendations:
        top_recs = recommendations[:5]
        prompt += "\n\nGuidelines:\n" + "\n".join(f"- {r}" for r in top_recs)

    return prompt
