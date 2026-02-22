"""Ada Core API — Tool Registry.

Central registry for all tools available to Ada agents.
Tools are categorized by domain (code_review, growth, creative, etc.)
and can be selectively enabled per AgentBlueprint.

MS4.1: Enables sub-company integration (Velie, Cyrus, Lumina).
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolSpec(BaseModel):
    """Specification for a registered tool."""

    name: str
    description: str
    category: str  # code_review, growth, creative, general
    provider: str = "ada"  # ada, velie, cyrus, lumina
    version: str = "1.0.0"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    cost_per_call_usd: float = 0.0
    avg_latency_ms: float = 0.0
    requires_auth: bool = False


class ToolRegistry:
    """Central tool registry.

    Manages tool registration, discovery, and filtering.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("Tool registered: %s (%s/%s)", tool.name, tool.provider, tool.category)

    def get(self, name: str) -> ToolSpec | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_by_category(self, category: str) -> list[ToolSpec]:
        """List tools by category."""
        return [t for t in self._tools.values() if t.category == category]

    def list_by_provider(self, provider: str) -> list[ToolSpec]:
        """List tools by provider (sub-company)."""
        return [t for t in self._tools.values() if t.provider == provider]

    def list_all(self) -> list[ToolSpec]:
        """List all registered tools."""
        return list(self._tools.values())

    def filter_for_blueprint(self, tool_names: list[str]) -> list[ToolSpec]:
        """Get tools that match a blueprint's tool list."""
        return [self._tools[n] for n in tool_names if n in self._tools]

    def catalog(self) -> list[dict[str, Any]]:
        """Generate a catalog for external consumption (SDK/API)."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "provider": t.provider,
                "version": t.version,
                "cost_per_call_usd": t.cost_per_call_usd,
            }
            for t in sorted(self._tools.values(), key=lambda x: (x.category, x.name))
        ]


# Module singleton
tool_registry = ToolRegistry()


# ---------------------------------------------------------------------------
# Built-in tool registrations
# ---------------------------------------------------------------------------

def _register_defaults() -> None:
    """Register default Ada tools."""
    defaults = [
        # General
        ToolSpec(name="web_search", description="Search the web for information", category="general"),
        ToolSpec(name="rag", description="Retrieve tenant-specific knowledge", category="general"),

        # Code Review (Velie-originated)
        ToolSpec(
            name="github_diff", description="Fetch PR diff from GitHub",
            category="code_review", provider="velie",
            cost_per_call_usd=0.001, avg_latency_ms=500,
        ),
        ToolSpec(
            name="test_runner", description="Execute test suite and return results",
            category="code_review", provider="velie",
            cost_per_call_usd=0.005, avg_latency_ms=5000,
        ),
        ToolSpec(
            name="linter", description="Run linting checks on code",
            category="code_review", provider="velie",
            cost_per_call_usd=0.001, avg_latency_ms=1000,
        ),
        ToolSpec(
            name="code_executor", description="Execute code in sandboxed environment",
            category="code_review", provider="ada",
            cost_per_call_usd=0.01, avg_latency_ms=3000,
        ),

        # Growth (Cyrus-originated)
        ToolSpec(
            name="analytics_query", description="Query analytics data",
            category="growth", provider="cyrus",
            cost_per_call_usd=0.002, avg_latency_ms=2000,
        ),
        ToolSpec(
            name="ab_test_analyzer", description="Analyze A/B test results",
            category="growth", provider="cyrus",
            cost_per_call_usd=0.005, avg_latency_ms=3000,
        ),

        # Creative (Lumina-originated)
        ToolSpec(
            name="image_generator", description="Generate images from text prompts",
            category="creative", provider="lumina",
            cost_per_call_usd=0.02, avg_latency_ms=10000,
        ),
        ToolSpec(
            name="brand_checker", description="Check brand consistency",
            category="creative", provider="lumina",
            cost_per_call_usd=0.003, avg_latency_ms=2000,
        ),
    ]
    for tool in defaults:
        tool_registry.register(tool)


_register_defaults()
