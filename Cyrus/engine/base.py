"""CyrusNode — Abstract base class for all 23 Cyrus nodes.

Priority Weights: Outcome(0.40) > Quality(0.30) > Speed(0.20) > Cost(0.10)
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from engine.state import CyrusState

logger = logging.getLogger(__name__)


# Priority weights — applied globally to all nodes
PRIORITY_WEIGHTS = {
    "outcome": 0.40,
    "quality": 0.30,
    "speed": 0.20,
    "cost": 0.10,
}


class CyrusNode(ABC):
    """Base class for all Cyrus graph nodes.

    Subclasses must implement `execute()`. The `__call__` method
    wraps execution with timing, logging, and error handling.
    """

    name: str = "base_node"
    layer: str = "unknown"

    @abstractmethod
    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the node logic. Returns a partial state update."""
        ...

    async def __call__(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Wrap execution with metrics, logging, and error handling."""
        start = time.perf_counter()
        logger.info("▶ [%s] %s starting", self.layer, self.name)

        try:
            result = await self.execute(state, config)
            elapsed = time.perf_counter() - start
            logger.info("✓ [%s] %s completed in %.2fs", self.layer, self.name, elapsed)

            # Append node metrics
            metrics = state.get("node_metrics", [])
            metrics.append({
                "node": self.name,
                "layer": self.layer,
                "elapsed_seconds": round(elapsed, 3),
                "success": True,
            })

            return {
                **result,
                "current_layer": self.layer,
                "current_node": self.name,
                "node_metrics": metrics,
            }

        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error("✗ [%s] %s failed after %.2fs: %s", self.layer, self.name, elapsed, e)

            errors = state.get("errors", [])
            errors.append(f"[{self.name}] {e!s}")
            metrics = state.get("node_metrics", [])
            metrics.append({
                "node": self.name,
                "layer": self.layer,
                "elapsed_seconds": round(elapsed, 3),
                "success": False,
                "error": str(e),
            })

            return {
                "current_layer": self.layer,
                "current_node": self.name,
                "node_metrics": metrics,
                "errors": errors,
            }
