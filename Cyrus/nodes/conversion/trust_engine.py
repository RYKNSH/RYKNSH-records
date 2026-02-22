"""trust_engine — 🟡 Conversion Layer: Cross-Pipeline Trust Foundation.

The Trust Engine is the core differentiator of Cyrus. It sits between
Acquisition and Conversion, ensuring every interaction builds authentic trust.

5 Core Capabilities:
1. Personality Profiler — Data Layer 3 (Secure→Opt-in→Inference→Auto-correct)
2. Interaction Memory — pgvector-backed persistent memory
3. Value-First Strategist — Design what to give before selling
4. Timing Optimizer — When to reach out vs. when to wait
5. Trust Score Tracker — 0-100 score with 4 stages
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from engine.base import CyrusNode
from engine.state import CyrusState
from models.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trust Score Stages
# ---------------------------------------------------------------------------

TRUST_STAGES = [
    {"min": 0, "max": 25, "label": "stranger", "description": "知人以前。接点なし"},
    {"min": 26, "max": 50, "label": "acquaintance", "description": "知人。名前を知っている"},
    {"min": 51, "max": 75, "label": "trusted", "description": "信頼。相談される関係"},
    {"min": 76, "max": 100, "label": "partner", "description": "パートナー。家族以上の信頼"},
]


def get_trust_stage(score: float) -> dict[str, Any]:
    """Get the trust stage for a given score."""
    for stage in TRUST_STAGES:
        if stage["min"] <= score <= stage["max"]:
            return stage
    return TRUST_STAGES[0]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

PERSONALITY_PROMPT = """You are the Personality Profiler module of Cyrus Trust Engine.

Analyze the following entity and available data to infer behavioral characteristics.

## Entity Data
{entity_data}

## Available Signals
{signals}

## Data Collection Layer
Current data quality: {data_layer}
- L1 (Secure): Public info only — profile, articles, talks, writing style
- L2 (Opt-in): CRM data, newsletter behavior, website analytics
- L3 (Inference): Industry×role defaults → auto-correct from interaction patterns

## Task
Create a personality profile (respond in JSON):

{{
  "communication_style": "analytical|driver|amiable|expressive",
  "decision_speed": "fast|moderate|deliberate",
  "preferred_channel": "email|linkedin|phone|slack",
  "preferred_content_format": "data_heavy|story_driven|bullet_points|visual",
  "risk_tolerance": "conservative|moderate|aggressive",
  "values": ["..."],
  "hot_buttons": ["..."],
  "avoid_topics": ["..."],
  "confidence": 0.0-1.0,
  "data_layer_used": "l1|l2|l3",
  "recommended_tone": "..."
}}

IMPORTANT: Never reveal the profiling to the target. Adapt naturally.
"""

VALUE_FIRST_PROMPT = """You are the Value-First Strategist of Cyrus Trust Engine.

Before any sales pitch, design what to GIVE the target for free.

## Target Profile
{personality_profile}

## Target Pain Points
{pain_points}

## Market Context
{market_data}

## Task
Design 3 value-first actions (respond in JSON):

{{
  "actions": [
    {{
      "type": "report|tool|introduction|insight|template",
      "title": "...",
      "description": "...",
      "delivery_channel": "email|linkedin|slack",
      "estimated_impact": "high|medium|low",
      "effort_to_create": "low|medium|high"
    }}
  ],
  "sequence_rationale": "Why this order..."
}}
"""

TIMING_PROMPT = """You are the Timing Optimizer of Cyrus Trust Engine.

Determine if NOW is the right time to reach out to this target.

## Target Profile
{personality_profile}

## Interaction History
{interaction_history}

## Current Signals
{current_signals}

## Trust Score
Current: {trust_score}/100 | Stage: {trust_stage}

## Task
Decide timing (respond in JSON):

{{
  "should_reach_out": true|false,
  "reason": "...",
  "optimal_day": "monday|tuesday|...",
  "optimal_time": "morning|afternoon|evening",
  "wait_days": 0,
  "trigger_event": "...",
  "urgency": "high|medium|low"
}}
"""


class TrustEngine(CyrusNode):
    """Cross-pipeline trust foundation.

    Orchestrates all 5 trust capabilities for each entity
    before passing to the Conversion pipeline.
    """

    name = "trust_engine"
    layer = "conversion"

    async def execute(self, state: CyrusState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        blueprint = state.get("blueprint", {})
        icp_profiles = state.get("icp_profiles", [])
        detected_signals = state.get("detected_signals", [])
        market_data = state.get("market_data", {})

        # 1. Personality Profiler
        personality = await self._profile_personality(icp_profiles, detected_signals)

        # 2. Interaction Memory (would read from pgvector in production)
        interaction_history = self._get_interaction_history(blueprint.get("tenant_id", ""))

        # 3. Value-First Strategist
        value_first = await self._design_value_first(personality, icp_profiles, market_data)

        # 4. Timing Optimizer
        timing = await self._optimize_timing(
            personality, interaction_history, detected_signals,
            trust_score=25.0,  # Default for new leads
        )

        # 5. Trust Score
        trust_score = self._calculate_trust_score(interaction_history, detected_signals)
        trust_stage = get_trust_stage(trust_score)

        return {
            "trust_scores": {
                "overall": trust_score,
                "stage": trust_stage["label"],
                "stage_description": trust_stage["description"],
            },
            "trust_engine_output": {
                "personality_profile": personality,
                "interaction_history": interaction_history,
                "value_first_actions": value_first,
                "timing_decision": timing,
                "trust_score": trust_score,
                "trust_stage": trust_stage["label"],
            },
        }

    async def _profile_personality(
        self, icp_profiles: list[dict], signals: list[dict],
    ) -> dict[str, Any]:
        """Run Personality Profiler with 3-layer data hierarchy."""
        data_layer = "l1"  # Start conservative
        if signals:
            data_layer = "l2" if len(signals) > 2 else "l1"

        prompt = PERSONALITY_PROMPT.format(
            entity_data=str(icp_profiles)[:1500],
            signals=str(signals)[:1000],
            data_layer=data_layer,
        )
        return await self._call_ada(prompt)

    async def _design_value_first(
        self, personality: dict, icp_profiles: list[dict], market_data: dict,
    ) -> dict[str, Any]:
        """Design value-first actions before any sales pitch."""
        pain_points = []
        for profile in icp_profiles:
            pain_points.extend(profile.get("pain_points", []))

        prompt = VALUE_FIRST_PROMPT.format(
            personality_profile=str(personality)[:1000],
            pain_points=str(pain_points)[:500],
            market_data=str(market_data)[:1000],
        )
        return await self._call_ada(prompt)

    async def _optimize_timing(
        self, personality: dict, interaction_history: list[dict],
        signals: list[dict], trust_score: float,
    ) -> dict[str, Any]:
        """Determine optimal timing for next interaction."""
        trust_stage = get_trust_stage(trust_score)
        prompt = TIMING_PROMPT.format(
            personality_profile=str(personality)[:1000],
            interaction_history=str(interaction_history)[:500],
            current_signals=str(signals)[:500],
            trust_score=trust_score,
            trust_stage=trust_stage["label"],
        )
        return await self._call_ada(prompt)

    @staticmethod
    def _get_interaction_history(tenant_id: str) -> list[dict[str, Any]]:
        """Get interaction memory (would use pgvector in production)."""
        return []

    @staticmethod
    def _calculate_trust_score(
        interaction_history: list[dict], signals: list[dict],
    ) -> float:
        """Calculate trust score based on interaction depth + signal strength."""
        base_score = 10.0

        # Each past interaction adds trust
        interaction_bonus = min(len(interaction_history) * 5.0, 40.0)

        # High-confidence signals add trust
        signal_bonus = 0.0
        for sig in signals:
            conf = sig.get("confidence", 0)
            if conf > 0.8:
                signal_bonus += 5.0
            elif conf > 0.6:
                signal_bonus += 3.0
        signal_bonus = min(signal_bonus, 25.0)

        return min(base_score + interaction_bonus + signal_bonus, 100.0)

    async def _call_ada(self, prompt: str) -> dict[str, Any]:
        """Call Ada Core API."""
        if not settings.ada_api_url or not settings.ada_api_key:
            return self._mock_response(prompt)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ada_api_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.ada_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            import json
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)

    @staticmethod
    def _mock_response(prompt: str) -> dict[str, Any]:
        """Fallback mock for dev."""
        if "Personality Profiler" in prompt:
            return {
                "communication_style": "analytical",
                "decision_speed": "deliberate",
                "preferred_channel": "email",
                "preferred_content_format": "data_heavy",
                "risk_tolerance": "moderate",
                "values": ["engineering excellence", "data-driven decisions"],
                "hot_buttons": ["ROI", "efficiency", "scalability"],
                "avoid_topics": ["hype", "vague promises"],
                "confidence": 0.65,
                "data_layer_used": "l1",
                "recommended_tone": "Direct, data-backed, concise. Lead with numbers.",
            }
        elif "Value-First" in prompt:
            return {
                "actions": [
                    {
                        "type": "report",
                        "title": "Industry Benchmark: CAC by Company Stage",
                        "description": "Anonymous benchmark data from 200+ SaaS companies",
                        "delivery_channel": "email",
                        "estimated_impact": "high",
                        "effort_to_create": "low",
                    },
                    {
                        "type": "tool",
                        "title": "ROI Calculator for Marketing Automation",
                        "description": "Interactive tool showing cost savings vs current stack",
                        "delivery_channel": "linkedin",
                        "estimated_impact": "high",
                        "effort_to_create": "medium",
                    },
                    {
                        "type": "introduction",
                        "title": "Intro to Similar-Stage CTO",
                        "description": "Warm intro to a CTO who solved the same problem",
                        "delivery_channel": "email",
                        "estimated_impact": "medium",
                        "effort_to_create": "low",
                    },
                ],
                "sequence_rationale": "Start with data (appeals to analytical style), then provide actionable tool, then social proof via introduction.",
            }
        else:  # Timing
            return {
                "should_reach_out": True,
                "reason": "Recent funding signal indicates budget availability",
                "optimal_day": "tuesday",
                "optimal_time": "morning",
                "wait_days": 0,
                "trigger_event": "Series B announcement",
                "urgency": "high",
            }


trust_engine = TrustEngine()
