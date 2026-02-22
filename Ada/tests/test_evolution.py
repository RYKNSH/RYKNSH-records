"""Tests for Evolution Layer — QualityTester + Evolver.

Covers:
- FeedbackRecord scoring
- QualityTester aggregation
- Evolver model optimization
- Evolver temperature optimization
- Evolver priority weights optimization
- Blueprint evolution
- Feedback API
- E2E evolution flow
"""

import pytest

from agent.evolution.tester import FeedbackRecord, QualityTester
from agent.evolution.evolver import Evolver
from agent.lifecycle.blueprint import AgentBlueprint


class TestFeedbackRecord:
    """Test FeedbackRecord scoring."""

    def test_perfect_score(self):
        r = FeedbackRecord(
            request_id="1", rating=5, validation_score=1.0, grounding_score=1.0,
        )
        assert r.overall_score() >= 0.9

    def test_bad_rating(self):
        r = FeedbackRecord(
            request_id="1", rating=1, validation_score=1.0,
        )
        assert r.overall_score() < 0.7

    def test_retry_penalty(self):
        r1 = FeedbackRecord(request_id="1", validation_score=0.8)
        r2 = FeedbackRecord(request_id="2", validation_score=0.8, was_retried=True)
        assert r2.overall_score() < r1.overall_score()

    def test_edit_penalty(self):
        r1 = FeedbackRecord(request_id="1", validation_score=0.8)
        r2 = FeedbackRecord(request_id="2", validation_score=0.8, response_edited=True)
        assert r2.overall_score() < r1.overall_score()

    def test_no_rating_uses_implicit(self):
        r = FeedbackRecord(
            request_id="1", validation_score=0.9, grounding_score=0.8,
        )
        score = r.overall_score()
        assert 0.0 < score < 1.0


class TestQualityTester:
    """Test QualityTester aggregation."""

    @pytest.fixture
    def tester(self):
        return QualityTester()

    def test_empty_stats(self, tester):
        stats = tester.get_tenant_stats("t1")
        assert stats["count"] == 0

    def test_record_and_stats(self, tester):
        tester.record(FeedbackRecord(request_id="1", tenant_id="t1", model_used="gpt-4o", validation_score=0.9))
        tester.record(FeedbackRecord(request_id="2", tenant_id="t1", model_used="gpt-4o", validation_score=0.7))
        stats = tester.get_tenant_stats("t1")
        assert stats["count"] == 2
        assert 0.0 < stats["avg_score"] < 1.0

    def test_model_stats(self, tester):
        tester.record(FeedbackRecord(request_id="1", tenant_id="t1", model_used="gpt-4o", validation_score=0.9))
        tester.record(FeedbackRecord(request_id="2", tenant_id="t1", model_used="gpt-4o-mini", validation_score=0.5))
        model_stats = tester.get_model_stats("t1")
        assert "gpt-4o" in model_stats
        assert "gpt-4o-mini" in model_stats
        assert model_stats["gpt-4o"]["avg_score"] > model_stats["gpt-4o-mini"]["avg_score"]

    def test_record_from_state(self, tester):
        state = {
            "validation_score": 0.85,
            "retry_count": 1,
            "response_model": "claude-sonnet-4-20250514",
            "usage": {"total_tokens": 500},
        }
        feedback = tester.record_from_state(state, "req1", "t1")
        assert feedback.was_retried is True
        assert feedback.model_used == "claude-sonnet-4-20250514"
        assert tester.total_records == 1

    def test_tenant_isolation(self, tester):
        tester.record(FeedbackRecord(request_id="1", tenant_id="t1", validation_score=0.9))
        tester.record(FeedbackRecord(request_id="2", tenant_id="t2", validation_score=0.5))
        assert tester.get_tenant_stats("t1")["count"] == 1
        assert tester.get_tenant_stats("t2")["count"] == 1


class TestEvolver:
    """Test Evolver optimization."""

    @pytest.fixture
    def populated_evolver(self):
        tester = QualityTester()
        # Add enough records to trigger optimization
        for i in range(15):
            tester.record(FeedbackRecord(
                request_id=f"req-{i}",
                tenant_id="t1",
                model_used="gpt-4o" if i % 3 != 0 else "gpt-4o-mini",
                validation_score=0.8 if i % 3 != 0 else 0.4,
                was_retried=i % 5 == 0,
            ))
        return Evolver(tester)

    def test_should_evolve_insufficient_data(self):
        tester = QualityTester()
        e = Evolver(tester)
        assert e.should_evolve("t1") is False

    def test_should_evolve_sufficient_data(self, populated_evolver):
        assert populated_evolver.should_evolve("t1") is True

    def test_optimize_model_selection(self, populated_evolver):
        result = populated_evolver.optimize_model_selection("t1")
        assert "recommended_model" in result
        assert len(result["model_ranking"]) > 0
        # gpt-4o should rank higher (higher validation scores)
        assert result["recommended_model"] == "gpt-4o"

    def test_optimize_temperature(self, populated_evolver):
        result = populated_evolver.optimize_temperature("t1")
        assert 0.1 <= result["recommended_temperature"] <= 1.0

    def test_optimize_priority_weights(self, populated_evolver):
        weights = populated_evolver.optimize_priority_weights("t1")
        total = weights.quality + weights.efficiency + weights.speed + weights.cost
        assert total == pytest.approx(1.0, abs=0.01)

    def test_evolve_blueprint(self, populated_evolver):
        current = AgentBlueprint.default(tenant_id="t1")
        evolved = populated_evolver.evolve_blueprint(current)
        assert evolved.metadata.get("evolution_reason") == "statistical_optimization"
        assert evolved.metadata.get("evolved_from_version") == current.version

    def test_generate_report(self, populated_evolver):
        report = populated_evolver.generate_report("t1")
        assert report["should_evolve"] is True
        assert "recommendations" in report
        assert "model" in report["recommendations"]
        assert "temperature" in report["recommendations"]


class TestFeedbackAPI:
    """Test Feedback API."""

    @pytest.mark.asyncio
    async def test_submit_feedback(self):
        from server.feedback import submit_feedback, FeedbackRequest
        req = FeedbackRequest(request_id="test-1", rating=5, comment="Great!", category="helpful")
        resp = await submit_feedback(req, tenant_id="t1")
        assert resp.success is True


class TestEvolutionE2E:
    """End-to-end evolution flow."""

    @pytest.mark.asyncio
    async def test_full_evolution_pipeline(self):
        """Record feedback → analyze → evolve blueprint."""
        tester = QualityTester()
        evolver = Evolver(tester)

        # Simulate 15 requests with varying quality
        for i in range(15):
            tester.record(FeedbackRecord(
                request_id=f"e2e-{i}",
                tenant_id="e2e",
                model_used="claude-sonnet-4-20250514",
                validation_score=0.6 + (i % 4) * 0.1,
                was_retried=i % 4 == 0,
                rating=3 + (i % 3),
            ))

        # Should have enough data
        assert evolver.should_evolve("e2e")

        # Generate report
        report = evolver.generate_report("e2e")
        assert report["feedback_count"] == 15

        # Evolve blueprint
        current = AgentBlueprint.default(tenant_id="e2e")
        evolved = evolver.evolve_blueprint(current)

        # Evolved should have adjusted parameters
        config = evolved.to_runnable_config()
        assert "configurable" in config
        assert config["configurable"]["default_model"] in ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"]
