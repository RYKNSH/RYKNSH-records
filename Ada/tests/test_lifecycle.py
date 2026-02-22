"""Tests for Lifecycle Layer nodes.

Covers:
- goal_intake: task classification, skill estimation, ambiguity detection
- researcher: query formulation, relevance scoring, diversity
- debater: persona selection, consensus calculation
- architect: execution plan design
- scribe: blueprint generation
- Full lifecycle E2E integration
"""

import pytest

from agent.lifecycle.goal_intake import (
    classify_task_type,
    estimate_required_skills,
    detect_ambiguity,
    estimate_quality_requirement,
    process_goal,
)
from agent.lifecycle.researcher import (
    formulate_queries,
    score_relevance,
    assess_diversity,
)
from agent.lifecycle.debater import (
    select_personas,
    generate_arguments,
    calculate_consensus,
    debate,
)
from agent.lifecycle.architect import design_execution_plan
from agent.lifecycle.scribe import generate_blueprint, scribe


class TestGoalIntake:
    """Test goal intake processing."""

    def test_code_classification(self):
        scores = classify_task_type("Write a Python function to sort a list")
        assert scores["code"] > scores["qa"]

    def test_analysis_classification(self):
        scores = classify_task_type("Analyze the performance of this algorithm")
        assert scores["analysis"] > 0

    def test_creative_classification(self):
        scores = classify_task_type("Write a short story about a robot")
        assert scores["creative"] > 0

    def test_qa_classification(self):
        scores = classify_task_type("What is the meaning of life?")
        assert scores["qa"] > 0

    def test_skill_estimation_code(self):
        skills = estimate_required_skills("Implement a REST API in Python")
        assert "programming" in skills
        assert "web_development" in skills

    def test_skill_estimation_fallback(self):
        skills = estimate_required_skills("Hello")
        assert skills == ["general"]

    def test_ambiguity_short_goal(self):
        questions = detect_ambiguity("Fix bug")
        assert len(questions) > 0

    def test_ambiguity_specific_goal(self):
        questions = detect_ambiguity("Write a Python function that sorts a JSON list by the 'name' field")
        assert len(questions) == 0  # Specific enough

    def test_quality_high(self):
        tier = estimate_quality_requirement("Build a production-grade, scalable API")
        assert tier == "full"

    def test_quality_low(self):
        tier = estimate_quality_requirement("Quick draft of an idea")
        assert tier == "light"

    def test_process_goal_full(self):
        result = process_goal("Implement a REST API in Python with JWT authentication")
        assert result["task_type"] == "code"
        assert "programming" in result["required_skills"]
        assert result["quality_tier"] in ("light", "standard", "full")


class TestResearcher:
    """Test researcher functions."""

    def test_formulate_queries_basic(self):
        goal_result = {"goal_text": "What is Python?", "task_type": "qa", "required_skills": ["general"]}
        queries = formulate_queries(goal_result)
        assert len(queries) >= 2  # At least raw + enrichment

    def test_score_relevance_high(self):
        score = score_relevance("Python programming", {"content": "Python is a programming language"})
        assert score > 0.3

    def test_score_relevance_low(self):
        score = score_relevance("quantum physics", {"content": "Cooking recipes for dinner"})
        assert score < 0.3

    def test_diversity_unique_sources(self):
        results = [
            {"metadata": {"source": "docs"}},
            {"metadata": {"source": "api"}},
            {"metadata": {"source": "blog"}},
        ]
        assert assess_diversity(results) == 1.0

    def test_diversity_same_source(self):
        results = [
            {"metadata": {"source": "docs"}},
            {"metadata": {"source": "docs"}},
        ]
        assert assess_diversity(results) == 0.5


class TestDebater:
    """Test debater functions."""

    def test_select_code_personas(self):
        personas = select_personas("code")
        assert len(personas) == 3
        names = [p["name"] for p in personas]
        assert "Pragmatist" in names

    def test_select_qa_personas(self):
        personas = select_personas("qa")
        assert len(personas) == 3

    def test_generate_arguments(self):
        goal_result = {"task_type": "code", "goal_text": "Build API", "quality_tier": "standard"}
        research_result = {"results": []}
        args = generate_arguments(goal_result, research_result)
        assert len(args) == 3
        assert all("persona" in a for a in args)
        assert all("recommendations" in a for a in args)

    def test_consensus_calculation(self):
        goal_result = {"task_type": "code", "goal_text": "Build API", "quality_tier": "standard"}
        research_result = {"results": []}
        args = generate_arguments(goal_result, research_result)
        consensus = calculate_consensus(args)
        assert 0.0 <= consensus["consensus_score"] <= 1.0
        assert len(consensus["merged_recommendations"]) > 0

    def test_consensus_empty(self):
        consensus = calculate_consensus([])
        assert consensus["consensus_score"] == 0.0

    def test_debate_full(self):
        goal_result = {"task_type": "analysis", "goal_text": "Analyze data", "quality_tier": "full"}
        research_result = {"results": []}
        result = debate(goal_result, research_result)
        assert result["persona_count"] == 3
        assert "consensus" in result


class TestArchitect:
    """Test architect design planning."""

    def test_code_execution_plan(self):
        goal_result = {"task_type": "code", "required_skills": ["programming"], "quality_tier": "standard"}
        debate_result = debate(goal_result, {"results": []})
        plan = design_execution_plan(goal_result, debate_result)
        assert plan["default_model"] in ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"]
        assert plan["temperature"] <= 0.5  # Code = low temp
        assert "code_executor" in plan["tools"]

    def test_qa_execution_plan(self):
        goal_result = {"task_type": "qa", "required_skills": ["research"], "quality_tier": "light"}
        debate_result = debate(goal_result, {"results": []})
        plan = design_execution_plan(goal_result, debate_result)
        assert plan["rag_enabled"] is True

    def test_system_prompt_generated(self):
        goal_result = {"task_type": "code", "required_skills": ["programming"], "quality_tier": "full"}
        debate_result = debate(goal_result, {"results": []})
        plan = design_execution_plan(goal_result, debate_result)
        assert len(plan["system_prompt"]) > 50


class TestScribe:
    """Test scribe blueprint generation."""

    @pytest.mark.asyncio
    async def test_generate_blueprint(self):
        goal_result = process_goal("Build a REST API in Python")
        research_result = {"results": [], "unique_count": 0}
        debate_result = debate(goal_result, research_result)
        architect_result = design_execution_plan(goal_result, debate_result)

        bp = await generate_blueprint(
            tenant_id="test",
            goal_result=goal_result,
            research_result=research_result,
            debate_result=debate_result,
            architect_result=architect_result,
        )
        assert bp.tenant_id == "test"
        assert bp.default_model in ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"]
        assert len(bp.system_prompt) > 0

    @pytest.mark.asyncio
    async def test_full_lifecycle_e2e(self):
        """End-to-end: goal → research → debate → design → blueprint."""
        # 1. Goal intake
        goal = process_goal("Analyze the performance of our Python web server")

        # 2. Research (no RAG available — graceful degradation)
        from agent.lifecycle.researcher import research
        research_result = await research(goal, tenant_id="test")

        # 3. Debate
        debate_result = debate(goal, research_result)

        # 4. Architect
        architect_result = design_execution_plan(goal, debate_result)

        # 5. Scribe
        bp = await scribe(
            tenant_id="test",
            goal_result=goal,
            research_result=research_result,
            debate_result=debate_result,
            architect_result=architect_result,
            persist=True,
        )

        assert bp.version >= 1
        assert bp.tenant_id == "test"
        assert bp.metadata.get("task_type") == "analysis"

        # Verify config bridge works
        config = bp.to_runnable_config()
        assert config["configurable"]["default_model"] == bp.default_model
