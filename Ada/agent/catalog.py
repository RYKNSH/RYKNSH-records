"""Ada Core API — Node Set Catalog + SDK Specification.

Pre-built node set configurations for different use cases.
Each catalog entry defines a complete AgentBlueprint template
ready for sub-company deployment.

MS4.2-4.3: Enables rapid deployment for Velie, Cyrus, Lumina.
"""

from __future__ import annotations

from typing import Any

from agent.lifecycle.blueprint import AgentBlueprint, PriorityWeights


# ===========================================================================
# Node Set Catalog
# ===========================================================================

CATALOG: dict[str, dict[str, Any]] = {
    "code_reviewer": {
        "name": "World-Class Code Reviewer",
        "description": "Production-grade code review with security, performance, and best-practice analysis.",
        "provider": "velie",
        "blueprint_template": {
            "persona": "Expert code reviewer. Catches bugs, security flaws, and performance issues. "
                       "Enforces best practices. Never misses edge cases.",
            "system_prompt": (
                "You are a world-class code reviewer. Analyze code changes for:\n"
                "1. Bugs and logic errors\n"
                "2. Security vulnerabilities (OWASP awareness)\n"
                "3. Performance bottlenecks\n"
                "4. Best practice violations\n"
                "5. Test coverage gaps\n\n"
                "Be thorough but constructive. Prioritize critical issues."
            ),
            "priority_weights": {"quality": 0.5, "efficiency": 0.3, "speed": 0.1, "cost": 0.1},
            "default_model": "claude-sonnet-4-20250514",
            "temperature": 0.2,
            "tools": ["github_diff", "test_runner", "linter", "code_executor"],
            "quality_tier": "full",
            "rag_enabled": True,
        },
    },
    "growth_hacker": {
        "name": "Growth Hacker",
        "description": "Data-driven growth analysis with A/B testing and funnel optimization.",
        "provider": "cyrus",
        "blueprint_template": {
            "persona": "Data-driven growth strategist. Identifies opportunities through analytics.",
            "system_prompt": (
                "You are a growth hacker. Focus on:\n"
                "1. Funnel analysis and conversion optimization\n"
                "2. A/B test design and result interpretation\n"
                "3. User retention and engagement metrics\n"
                "4. Growth experiments with clear hypotheses\n"
            ),
            "priority_weights": {"quality": 0.3, "efficiency": 0.4, "speed": 0.2, "cost": 0.1},
            "default_model": "gpt-4o",
            "temperature": 0.5,
            "tools": ["analytics_query", "ab_test_analyzer"],
            "quality_tier": "standard",
            "rag_enabled": True,
        },
    },
    "creative_director": {
        "name": "Creative Director",
        "description": "Brand-consistent creative production with AI-assisted design.",
        "provider": "lumina",
        "blueprint_template": {
            "persona": "Creative director with a keen eye for brand consistency and visual impact.",
            "system_prompt": (
                "You are a creative director. Focus on:\n"
                "1. Brand voice and visual consistency\n"
                "2. Compelling copy and messaging\n"
                "3. Creative campaign concepts\n"
                "4. Audience-appropriate tone and style\n"
            ),
            "priority_weights": {"quality": 0.4, "efficiency": 0.2, "speed": 0.2, "cost": 0.2},
            "default_model": "claude-sonnet-4-20250514",
            "temperature": 0.8,
            "tools": ["image_generator", "brand_checker"],
            "quality_tier": "full",
            "rag_enabled": False,
        },
    },
}


def build_blueprint_from_catalog(
    catalog_key: str,
    tenant_id: str,
    overrides: dict[str, Any] | None = None,
) -> AgentBlueprint:
    """Create an AgentBlueprint from a catalog entry.

    Args:
        catalog_key: Key into CATALOG (e.g., "code_reviewer")
        tenant_id: Tenant ID
        overrides: Optional field overrides
    """
    import uuid

    entry = CATALOG.get(catalog_key)
    if not entry:
        raise ValueError(f"Unknown catalog entry: {catalog_key}")

    template = entry["blueprint_template"]
    weights = template.get("priority_weights", {})

    bp = AgentBlueprint(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=catalog_key,
        persona=template["persona"],
        system_prompt=template["system_prompt"],
        priority_weights=PriorityWeights(**weights),
        default_model=template.get("default_model", "claude-sonnet-4-20250514"),
        temperature=template.get("temperature", 0.7),
        tools=template.get("tools", []),
        quality_tier=template.get("quality_tier", "standard"),
        rag_enabled=template.get("rag_enabled", True),
        metadata={"catalog_source": catalog_key, "provider": entry.get("provider", "ada")},
    )

    if overrides:
        for key, value in overrides.items():
            if hasattr(bp, key):
                setattr(bp, key, value)

    return bp


def get_catalog_summary() -> list[dict[str, str]]:
    """Get a summary of available node sets for SDK/API."""
    return [
        {
            "key": key,
            "name": entry["name"],
            "description": entry["description"],
            "provider": entry["provider"],
        }
        for key, entry in CATALOG.items()
    ]
