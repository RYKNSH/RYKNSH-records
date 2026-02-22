"""Ada Core API — Node Package.

Public interface for Ada's graph nodes.
All Execution Layer nodes (sentinel, validator, aggregator, etc.) live here.
"""

from agent.nodes.base import AdaNode

__all__ = ["AdaNode"]
