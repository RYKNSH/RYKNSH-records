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
import time
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
    3. Built-in observability (automatic execution timing)

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

        Wraps the process method with automatic timing/observability.
        This is the abstraction point — if we swap graph engines,
        only this method needs to change.
        """
        node = self

        async def _wrapped(state: dict, config: RunnableConfig | None = None) -> dict:
            start = time.perf_counter()
            try:
                result = await node.process(state, config)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.debug(
                    "Node [%s] completed in %.2fms", node.name, elapsed_ms,
                )
                # Append node timing to metrics list in state
                metrics_entry = {
                    "node_name": node.name,
                    "execution_time_ms": round(elapsed_ms, 2),
                    "success": True,
                }
                existing = list(state.get("node_metrics", []))
                existing.append(metrics_entry)
                result["node_metrics"] = existing
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    "Node [%s] failed after %.2fms: %s", node.name, elapsed_ms, e,
                )
                raise

        return _wrapped

    def __repr__(self) -> str:
        return f"<AdaNode:{self.name}>"

