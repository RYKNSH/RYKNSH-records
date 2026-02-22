"""Ada Core API — Aggregator Node.

Aggregates results from parallel (or single) execution paths.
Currently passes through single results; will handle fan-in when
parallel executors are enabled via AgentBlueprint.

Future capabilities:
1. Weighted result merging (priority weights from WHITEPAPER)
2. Contradiction detection between parallel results
3. Best-answer selection

WHITEPAPER ref: Section 3 — aggregator, Section 4 — Priority Weights
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent.nodes.base import AdaNode

logger = logging.getLogger(__name__)


class AggregatorNode(AdaNode):
    """Result aggregation node for fan-in scenarios.

    In single-executor mode (current), passes through the result.
    In parallel mode (future), merges multiple results with priority weights.

    State updates:
        aggregated_content (str): Final aggregated response content
        aggregation_method (str): "passthrough" | "weighted_merge" | "best_selection"
        parallel_results (list): Raw results from parallel paths (future)
    """

    name = "aggregator"

    async def process(
        self,
        state: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Aggregate execution results."""
        # Current: single result passthrough
        response = state.get("response_content", "")
        parallel_results = state.get("parallel_results", [])

        if parallel_results:
            # Future: multi-result aggregation
            aggregated = self._weighted_merge(parallel_results, config)
            method = "weighted_merge"
        else:
            # Single result passthrough
            aggregated = response
            method = "passthrough"

        logger.info("Aggregator: method=%s, output_len=%d", method, len(aggregated))

        return {
            "aggregated_content": aggregated,
            "aggregation_method": method,
        }

    @staticmethod
    def _weighted_merge(
        results: list[dict[str, Any]],
        config: RunnableConfig | None = None,
    ) -> str:
        """Merge multiple results using priority weights.

        Priority order (from WHITEPAPER):
        1. Quality (highest weight)
        2. Efficiency
        3. Speed
        4. Lightweight (lowest weight)
        """
        if not results:
            return ""

        if len(results) == 1:
            return results[0].get("content", "")

        # Extract weights from config or use defaults
        weights = {"quality": 0.4, "efficiency": 0.3, "speed": 0.2, "cost": 0.1}
        if config and "configurable" in config:
            custom_weights = config["configurable"].get("priority_weights")
            if custom_weights:
                weights.update(custom_weights)

        # Score each result
        scored = []
        for r in results:
            content = r.get("content", "")
            score = (
                len(content) / 1000 * weights["quality"] +  # Longer = more thorough
                r.get("validation_score", 0.5) * weights["efficiency"] +
                (1.0 - min(r.get("time_ms", 1000) / 5000, 1.0)) * weights["speed"] +
                (1.0 - min(r.get("cost_usd", 0.01) / 0.1, 1.0)) * weights["cost"]
            )
            scored.append((score, content))

        # Select best scoring result
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    @staticmethod
    def detect_contradictions(results: list[dict[str, Any]]) -> list[str]:
        """Detect contradictions between parallel results.

        Simple heuristic: check for negation patterns between responses.
        Full contradiction detection requires LLM judgment (M3+).
        """
        if len(results) < 2:
            return []

        contradictions: list[str] = []
        contents = [r.get("content", "").lower() for r in results]

        # Simple negation-based contradiction detection
        negation_pairs = [
            ("yes", "no"),
            ("true", "false"),
            ("correct", "incorrect"),
            ("possible", "impossible"),
            ("should", "should not"),
        ]

        for i, c1 in enumerate(contents):
            for j, c2 in enumerate(contents):
                if i >= j:
                    continue
                for pos, neg in negation_pairs:
                    if pos in c1 and neg in c2:
                        contradictions.append(
                            f"Result {i} says '{pos}' but result {j} says '{neg}'"
                        )
                    elif neg in c1 and pos in c2:
                        contradictions.append(
                            f"Result {i} says '{neg}' but result {j} says '{pos}'"
                        )

        return contradictions


# Module-level singleton
aggregator_node = AggregatorNode()
