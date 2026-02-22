"""Ada Core API — Debater Node.

Generates pro/con arguments for design decisions through persona-based debate.
Part of the Lifecycle pipeline: researcher → debater → architect.

WHITEPAPER ref: Section 2 — debater, Round 6-9 debate methodology
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# Persona templates for different task types
PERSONA_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "code": [
        {"name": "Pragmatist", "stance": "Ship fast, iterate later. Simple > clever."},
        {"name": "Perfectionist", "stance": "Code quality is non-negotiable. Tests first."},
        {"name": "Security", "stance": "Every input is hostile. Defense in depth."},
    ],
    "analysis": [
        {"name": "Data Scientist", "stance": "Let the data speak. Statistical rigor."},
        {"name": "Domain Expert", "stance": "Context matters more than numbers."},
        {"name": "Skeptic", "stance": "Correlation ≠ causation. Question assumptions."},
    ],
    "creative": [
        {"name": "Innovator", "stance": "Break conventions. Surprise the audience."},
        {"name": "Traditionalist", "stance": "Classic structures work. Don't reinvent."},
        {"name": "Audience Advocate", "stance": "What does the reader/user actually need?"},
    ],
    "qa": [
        {"name": "Teacher", "stance": "Clarity and accuracy above all."},
        {"name": "Expert", "stance": "Depth and nuance matter. Don't oversimplify."},
        {"name": "Beginner", "stance": "If I can't understand it, it's not good enough."},
    ],
}


def select_personas(
    task_type: str,
    goal_text: str = "",
) -> list[dict[str, str]]:
    """Auto-select debate personas based on task type."""
    personas = PERSONA_TEMPLATES.get(task_type, PERSONA_TEMPLATES["qa"])
    return personas


def generate_arguments(
    goal_result: dict[str, Any],
    research_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate pro/con arguments for each persona.

    This is a simplified heuristic version. Full LLM-based
    debate will be added in M3+ with multi-turn exchanges.
    """
    task_type = goal_result.get("task_type", "qa")
    goal_text = goal_result.get("goal_text", "")
    personas = select_personas(task_type, goal_text)
    quality_tier = goal_result.get("quality_tier", "standard")

    arguments: list[dict[str, Any]] = []

    for persona in personas:
        # Generate stance-based recommendations
        argument = {
            "persona": persona["name"],
            "stance": persona["stance"],
            "recommendations": _derive_recommendations(
                persona, task_type, quality_tier,
            ),
            "priority_bias": _derive_priority_bias(persona["name"]),
        }
        arguments.append(argument)

    return arguments


def _derive_recommendations(
    persona: dict[str, str],
    task_type: str,
    quality_tier: str,
) -> list[str]:
    """Derive recommendations from persona stance."""
    name = persona["name"]
    recommendations = {
        "Pragmatist": ["Use proven patterns", "Minimize dependencies", "Ship incrementally"],
        "Perfectionist": ["Write tests first", "Full documentation", "Code review required"],
        "Security": ["Input validation", "Output sanitization", "Least privilege"],
        "Data Scientist": ["Validate data quality", "Use appropriate metrics", "Reproducibility"],
        "Domain Expert": ["Consider edge cases", "Real-world constraints", "User context"],
        "Skeptic": ["Question assumptions", "Verify sources", "Consider alternatives"],
        "Innovator": ["Try unconventional approaches", "Experiment freely", "Break constraints"],
        "Traditionalist": ["Follow established patterns", "Consistency matters", "Standards compliance"],
        "Audience Advocate": ["User-first design", "Clear communication", "Accessibility"],
        "Teacher": ["Step-by-step explanation", "Use examples", "Build on fundamentals"],
        "Expert": ["Provide depth", "Reference primary sources", "Nuanced analysis"],
        "Beginner": ["Simple language", "Visual aids", "Practical examples"],
    }
    return recommendations.get(name, ["Apply best practices"])


def _derive_priority_bias(persona_name: str) -> dict[str, float]:
    """Map persona to Priority Weights bias."""
    biases = {
        "Pragmatist": {"quality": 0.2, "efficiency": 0.4, "speed": 0.3, "cost": 0.1},
        "Perfectionist": {"quality": 0.6, "efficiency": 0.2, "speed": 0.1, "cost": 0.1},
        "Security": {"quality": 0.5, "efficiency": 0.3, "speed": 0.1, "cost": 0.1},
        "Innovator": {"quality": 0.3, "efficiency": 0.2, "speed": 0.4, "cost": 0.1},
        "Traditionalist": {"quality": 0.4, "efficiency": 0.3, "speed": 0.2, "cost": 0.1},
    }
    return biases.get(persona_name, {"quality": 0.4, "efficiency": 0.3, "speed": 0.2, "cost": 0.1})


def calculate_consensus(arguments: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate consensus from debate arguments.

    Returns merged priority weights and agreement score.
    """
    if not arguments:
        return {
            "consensus_score": 0.0,
            "merged_weights": {"quality": 0.4, "efficiency": 0.3, "speed": 0.2, "cost": 0.1},
            "merged_recommendations": [],
        }

    # Average priority weights across personas
    merged = {"quality": 0.0, "efficiency": 0.0, "speed": 0.0, "cost": 0.0}
    all_recs: list[str] = []

    for arg in arguments:
        bias = arg.get("priority_bias", {})
        for key in merged:
            merged[key] += bias.get(key, 0.25)
        all_recs.extend(arg.get("recommendations", []))

    n = len(arguments)
    for key in merged:
        merged[key] = round(merged[key] / n, 3)

    # Deduplicate recommendations
    unique_recs = list(dict.fromkeys(all_recs))

    # Consensus score = how similar the priority biases are
    variance = sum(
        sum((arg.get("priority_bias", {}).get(k, 0.25) - merged[k]) ** 2 for k in merged)
        for arg in arguments
    ) / n
    consensus = max(0.0, 1.0 - variance * 10)

    return {
        "consensus_score": round(consensus, 3),
        "merged_weights": merged,
        "merged_recommendations": unique_recs,
    }


def debate(
    goal_result: dict[str, Any],
    research_result: dict[str, Any],
) -> dict[str, Any]:
    """Execute a debate session for a goal.

    Returns debate results including arguments and consensus.
    """
    arguments = generate_arguments(goal_result, research_result)
    consensus = calculate_consensus(arguments)

    result = {
        "arguments": arguments,
        "consensus": consensus,
        "persona_count": len(arguments),
    }

    logger.info(
        "Debate: %d personas, consensus=%.3f",
        len(arguments), consensus["consensus_score"],
    )

    return result
