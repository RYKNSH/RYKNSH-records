"""Ada Core API — Strategist Node.

Dynamically selects the optimal execution strategy based on input analysis.
Replaces the simpler `select_model` function with full Priority Weights support.

Responsibilities:
1. Input complexity analysis (message length, tools, multi-turn)
2. Model selection (complexity + tenant config → optimal model)
3. Temperature control (code=low, creative=high)
4. CoT decision (complex queries → chain-of-thought prompt injection)
5. Quality tier determination (Light/Standard/Full)

WHITEPAPER ref: Section 4 — Priority Weights, Section 7 — Quality Tiers
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from agent.nodes.base import AdaNode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Complexity Analysis
# ---------------------------------------------------------------------------

def analyze_complexity(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Analyze input complexity to inform strategy selection.

    Returns a dict with:
        score (float): 0.0 (trivial) to 1.0 (very complex)
        factors (dict): Individual factor scores
    """
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return {"score": 0.0, "factors": {}}

    latest = user_messages[-1].get("content", "")

    # Factor 1: Message length
    length_score = min(len(latest) / 2000, 1.0)

    # Factor 2: Multi-turn depth
    turn_score = min(len(user_messages) / 10, 1.0)

    # Factor 3: Technical indicators
    tech_patterns = [
        r"(?i)(code|function|class|implement|debug|error|bug|api)",
        r"(?i)(analyze|compare|evaluate|review|audit)",
        r"(?i)(explain\s+why|how\s+does|what\s+causes)",
        r"(?i)(step\s+by\s+step|detailed|thorough|comprehensive)",
    ]
    tech_matches = sum(1 for p in tech_patterns if re.search(p, latest))
    tech_score = min(tech_matches / 3, 1.0)

    # Factor 4: Multi-task indicators
    multi_patterns = [
        r"(?i)(and\s+also|additionally|moreover|furthermore)",
        r"(?i)(first|second|third|\d+\.\s)",
        r"(?i)(both|all\s+of|each\s+of)",
    ]
    multi_matches = sum(1 for p in multi_patterns if re.search(p, latest))
    multi_score = min(multi_matches / 2, 1.0)

    # Weighted complexity score (Quality > Efficiency > Speed > Lightweight)
    score = (
        length_score * 0.2 +
        turn_score * 0.1 +
        tech_score * 0.4 +
        multi_score * 0.3
    )

    return {
        "score": round(min(score, 1.0), 3),
        "factors": {
            "length": round(length_score, 3),
            "turns": round(turn_score, 3),
            "technical": round(tech_score, 3),
            "multi_task": round(multi_score, 3),
        },
    }


def determine_temperature(messages: list[dict[str, str]]) -> float:
    """Determine optimal temperature based on content type.

    - Code/technical: 0.1-0.3 (precise)
    - Analytical: 0.3-0.5 (balanced)
    - Creative/general: 0.7 (flexible)
    """
    latest = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            latest = m.get("content", "")
            break

    if not latest:
        return 0.7

    # Code patterns → low temperature
    code_patterns = r"(?i)(code|function|class|implement|fix|debug|syntax|compile|python|javascript|sql)"
    if re.search(code_patterns, latest):
        return 0.2

    # Analytical patterns → medium temperature
    analysis_patterns = r"(?i)(analyze|compare|evaluate|review|audit|assess|examine)"
    if re.search(analysis_patterns, latest):
        return 0.4

    return 0.7


def should_use_cot(complexity_score: float, messages: list[dict[str, str]]) -> bool:
    """Determine if chain-of-thought prompting should be used.

    CoT is beneficial for:
    - Complex queries (score > 0.5)
    - Explicit reasoning requests
    """
    if complexity_score > 0.5:
        return True

    latest = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            latest = m.get("content", "")
            break

    cot_triggers = r"(?i)(explain|reason|why|how|step\s+by\s+step|think\s+through|walk\s+me\s+through)"
    return bool(re.search(cot_triggers, latest))


def determine_quality_tier(
    config: RunnableConfig | None,
    complexity_score: float,
) -> str:
    """Determine quality tier: light, standard, or full.

    Priority:
    1. Explicit tier from AgentBlueprint config
    2. Auto-select based on complexity
    """
    # Check explicit config
    if config and "configurable" in config:
        explicit_tier = config["configurable"].get("quality_tier")
        if explicit_tier in ("light", "standard", "full"):
            return explicit_tier

    # Auto-select
    if complexity_score < 0.3:
        return "light"
    elif complexity_score < 0.6:
        return "standard"
    return "full"


# ---------------------------------------------------------------------------
# StrategistNode
# ---------------------------------------------------------------------------

COT_SYSTEM_SUFFIX = (
    "\n\nIMPORTANT: Think step by step. Break down your reasoning "
    "before providing your final answer."
)


class StrategistNode(AdaNode):
    """Strategic decision-making node.

    Analyzes input and determines the optimal execution strategy:
    model, temperature, CoT, and quality tier.

    State updates:
        selected_model (str): Chosen LLM model
        langchain_messages (list): Converted + enriched messages
        request_id (str): Unique request identifier
        quality_tier (str): light/standard/full
        use_cot (bool): Whether CoT prompting is active
        complexity_score (float): Input complexity 0.0-1.0
    """

    name = "strategist"

    async def process(
        self,
        state: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Analyze input and select optimal execution strategy."""
        from agent.providers import MODELS, get_fallback

        messages = state.get("messages", [])
        requested_model = state.get("model")
        requested_temp = state.get("temperature")

        # -----------------------------------------------------------------
        # 1. Complexity analysis
        # -----------------------------------------------------------------
        analysis = analyze_complexity(messages)
        complexity_score = analysis["score"]

        # -----------------------------------------------------------------
        # 2. Model selection
        # -----------------------------------------------------------------
        tenant_default = "claude-sonnet-4-20250514"
        if config and "configurable" in config:
            tenant_default = config["configurable"].get("default_model", tenant_default)
            allowed = config["configurable"].get("allowed_models", list(MODELS.keys()))
        else:
            allowed = list(MODELS.keys())

        if requested_model and requested_model in MODELS and requested_model in allowed:
            selected = requested_model
        elif tenant_default in MODELS:
            selected = tenant_default
        else:
            selected = "claude-sonnet-4-20250514"

        # -----------------------------------------------------------------
        # 3. Temperature control
        # -----------------------------------------------------------------
        if requested_temp is not None:
            temperature = requested_temp
        else:
            temperature = determine_temperature(messages)

        # -----------------------------------------------------------------
        # 4. CoT decision
        # -----------------------------------------------------------------
        use_cot = should_use_cot(complexity_score, messages)

        # -----------------------------------------------------------------
        # 5. Quality tier
        # -----------------------------------------------------------------
        quality_tier = determine_quality_tier(config, complexity_score)

        # -----------------------------------------------------------------
        # 6. Build LangChain messages
        # -----------------------------------------------------------------
        from agent.graph import _convert_messages
        lc_messages = _convert_messages(messages)

        # Inject enriched system prompt (from context_loader)
        system_prompt = state.get("system_prompt_enriched")
        if system_prompt:
            prompt_text = system_prompt
            if use_cot:
                prompt_text += COT_SYSTEM_SUFFIX
            lc_messages.insert(0, SystemMessage(content=prompt_text))
        elif use_cot:
            lc_messages.insert(0, SystemMessage(content=COT_SYSTEM_SUFFIX.strip()))

        request_id = str(uuid.uuid4())

        logger.info(
            "Strategy: model=%s, temp=%.1f, cot=%s, tier=%s, complexity=%.3f (request=%s)",
            selected, temperature, use_cot, quality_tier, complexity_score, request_id,
        )

        return {
            "selected_model": selected,
            "temperature": temperature,
            "langchain_messages": lc_messages,
            "request_id": request_id,
            "quality_tier": quality_tier,
            "use_cot": use_cot,
            "complexity_score": complexity_score,
        }


# Module-level singleton
strategist_node = StrategistNode()
