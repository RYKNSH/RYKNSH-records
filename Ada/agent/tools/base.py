"""Ada Core API — Tool SDK Base Classes.

Defines the AdaTool abstract interface and ToolRegistry.
Subsidiaries (Velie, Lumina, etc.) implement AdaTool subclasses
with their domain-specific logic, then register them with the registry.

Ada provides the "socket" (interface); subsidiaries provide the "plug" (logic).
This respects the Boundary Protocol.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AdaTool(ABC):
    """Abstract base class for tools that can be used by Ada's LLM router.

    Subsidiaries implement concrete subclasses with their business logic.
    Ada converts these to LangChain StructuredTool for LangGraph integration.

    Example:
        class GitHubDiffTool(AdaTool):
            name = "github_get_diff"
            description = "Fetch the diff of a GitHub Pull Request"

            def get_input_schema(self) -> type[BaseModel]:
                class Input(BaseModel):
                    repo: str
                    pr_number: int
                return Input

            async def execute(self, **kwargs) -> str:
                # Velie's business logic here
                return "diff content..."
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def get_input_schema(self) -> type[BaseModel]:
        """Return a Pydantic model describing the tool's input parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the given parameters.

        Returns:
            String result to feed back to the LLM.
        """
        ...

    def to_langchain_tool(self) -> StructuredTool:
        """Convert this AdaTool to a LangChain StructuredTool for LangGraph."""
        schema = self.get_input_schema()

        async def _run(**kwargs: Any) -> str:
            return await self.execute(**kwargs)

        return StructuredTool.from_function(
            coroutine=_run,
            name=self.name,
            description=self.description,
            args_schema=schema,
        )


class ToolRegistry:
    """Registry for AdaTool instances.

    Tools are registered by name and can be retrieved individually
    or converted to LangChain tools in bulk.
    """

    def __init__(self) -> None:
        self._tools: dict[str, AdaTool] = {}

    def register(self, tool: AdaTool) -> None:
        """Register a tool. Overwrites if name already exists."""
        if not tool.name:
            raise ValueError("Tool must have a non-empty name")
        self._tools[tool.name] = tool
        logger.info("Tool registered: %s", tool.name)

    def get(self, name: str) -> AdaTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def to_langchain_tools(self) -> list[StructuredTool]:
        """Convert all registered tools to LangChain StructuredTool list."""
        return [tool.to_langchain_tool() for tool in self._tools.values()]

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Global registry singleton
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry singleton."""
    return _global_registry
