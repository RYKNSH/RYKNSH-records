"""Ada Core API — Node Interface Base Classes.

Defines the AdaNode abstract interface that all graph nodes inherit from.
This is the LangGraph abstraction layer — all nodes go through AdaNode
so the graph engine can be swapped in the future.

AdaNode (graph nodes) vs AdaTool (executor tools):
- AdaNode: sentinel, validator, aggregator — they ARE graph nodes
- AdaTool: github_diff, test_runner — they are USED BY the executor node
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class AdaNode(ABC):
    """Abstract base class for Ada graph nodes.

    All Execution Layer nodes (sentinel, validator, aggregator, etc.)
    inherit from this class. This provides:
    1. A consistent interface for all nodes
    2. An abstraction layer over LangGraph (future engine swap)
    3. Built-in logging and error handling

    Example:
        class SentinelNode(AdaNode):
            name = "sentinel"

            async def process(self, state, config=None):
                # check input safety
                return {"sentinel_passed": True}
    """

    name: str = ""

    @abstractmethod
    async def process(self, state: dict, config: RunnableConfig | None = None) -> dict:
        """Process the state and return updates.

        Args:
            state: The current graph state (RouterState).
            config: Optional LangGraph RunnableConfig with tenant info etc.

        Returns:
            Dict of state field updates to merge into the graph state.
        """
        ...

    def as_graph_node(self):
        """Return a callable suitable for LangGraph's add_node().

        This is the abstraction point — if we swap graph engines,
        only this method needs to change.
        """
        return self.process

    def __repr__(self) -> str:
        return f"<AdaNode:{self.name}>"
