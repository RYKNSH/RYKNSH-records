"""Ada Core API — Goal Intake Node.

Structures user goals into actionable task specifications.
First node in the Lifecycle pipeline.

Responsibilities:
1. Task type classification (code/analysis/creative/qa)
2. Required skills estimation
3. Ambiguity detection (for human-in-the-loop)
4. Quality requirement estimation

WHITEPAPER ref: Section 2 — goal_intake
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# Task type patterns
TASK_PATTERNS: dict[str, list[str]] = {
    "code": [
        r"(?i)(write|implement|create|build|develop|code|function|class|api|fix|debug|refactor)",
        r"(?i)(python|javascript|typescript|sql|html|css|react|next\.?js)",
    ],
    "analysis": [
        r"(?i)(analyze|compare|evaluate|review|audit|assess|benchmark|measure)",
        r"(?i)(performance|security|quality|architecture|design|pattern)",
    ],
    "creative": [
        r"(?i)(write|generate|create|compose|draft)\s+(a\s+)?(\w+\s+)?(story|poem|essay|article|blog|copy|song|script)",
        r"(?i)(creative|imaginative|artistic|narrative|fiction)",
    ],
    "qa": [
        r"(?i)(what|how|why|when|where|who|explain|describe|tell me)",
        r"(?i)(difference|between|versus|vs\.?|meaning|definition)",
    ],
}


def classify_task_type(goal: str) -> dict[str, float]:
    """Classify the goal into task type scores.

    Returns scores for each type (0.0-1.0).
    """
    scores: dict[str, float] = {}
    for task_type, patterns in TASK_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, goal))
        scores[task_type] = min(matches / len(patterns), 1.0)
    return scores


def estimate_required_skills(goal: str) -> list[str]:
    """Estimate required skills from the goal description."""
    skills: list[str] = []

    skill_patterns: dict[str, str] = {
        "programming": r"(?i)(code|function|class|implement|debug|api|python|javascript)",
        "data_analysis": r"(?i)(data|analysis|statistics|csv|json|database|sql)",
        "web_development": r"(?i)(web|html|css|react|frontend|backend|api|rest)",
        "writing": r"(?i)(write|draft|compose|article|blog|documentation)",
        "research": r"(?i)(research|find|search|investigate|explore|study)",
        "math": r"(?i)(calculate|math|formula|equation|algorithm|optimize)",
        "design": r"(?i)(design|architecture|pattern|structure|schema|diagram)",
    }

    for skill, pattern in skill_patterns.items():
        if re.search(pattern, goal):
            skills.append(skill)

    return skills or ["general"]


def detect_ambiguity(goal: str) -> list[str]:
    """Detect ambiguous or underspecified aspects of the goal.

    Returns a list of clarification questions.
    """
    questions: list[str] = []

    # Very short goal
    if len(goal.strip()) < 20:
        questions.append("Could you provide more details about what you need?")

    # No specific output format mentioned
    format_patterns = r"(?i)(json|csv|list|table|markdown|code|file|report)"
    if not re.search(format_patterns, goal) and len(goal) > 50:
        questions.append("What output format would you prefer?")

    # No programming language specified for code tasks
    code_pattern = r"(?i)(write|implement|create|build)\s+(a\s+)?(function|class|program|script)"
    lang_pattern = r"(?i)(python|javascript|typescript|java|go|rust|c\+\+|ruby)"
    if re.search(code_pattern, goal) and not re.search(lang_pattern, goal):
        questions.append("Which programming language should be used?")

    return questions


def estimate_quality_requirement(goal: str) -> str:
    """Estimate quality tier based on goal description.

    Returns: light, standard, or full
    """
    high_quality_indicators = [
        r"(?i)(production|enterprise|critical|important|thorough|comprehensive|detailed)",
        r"(?i)(best\s+practice|security|performance|scalable|robust)",
    ]

    low_quality_indicators = [
        r"(?i)(quick|simple|basic|draft|rough|prototype|mvp|sketch)",
        r"(?i)(just|only|briefly|short|fast)",
    ]

    high_matches = sum(1 for p in high_quality_indicators if re.search(p, goal))
    low_matches = sum(1 for p in low_quality_indicators if re.search(p, goal))

    if high_matches > low_matches:
        return "full"
    elif low_matches > high_matches:
        return "light"
    return "standard"


def process_goal(goal: str) -> dict[str, Any]:
    """Process a user goal into a structured task specification.

    This is the main entry point for goal intake.
    """
    task_types = classify_task_type(goal)
    primary_type = max(task_types, key=task_types.get) if task_types else "qa"
    skills = estimate_required_skills(goal)
    ambiguities = detect_ambiguity(goal)
    quality_tier = estimate_quality_requirement(goal)

    result = {
        "goal_text": goal,
        "task_type": primary_type,
        "task_type_scores": task_types,
        "required_skills": skills,
        "ambiguities": ambiguities,
        "needs_clarification": len(ambiguities) > 0,
        "quality_tier": quality_tier,
    }

    logger.info(
        "Goal intake: type=%s, skills=%s, ambiguities=%d, tier=%s",
        primary_type, skills, len(ambiguities), quality_tier,
    )

    return result
