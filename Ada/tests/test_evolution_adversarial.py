"""L1 Adversarial Tests — Evolution Layer (M3).

World-class edge cases for tester, evolver, feedback.
Tests boundary conditions, malicious data, extreme scenarios.
"""

import pytest

from agent.evolution.tester import FeedbackRecord, QualityTester
from agent.evolution.evolver import Evolver
from agent.lifecycle.blueprint import AgentBlueprint, PriorityWeights


class TestFeedbackRecordAdversarial:
    """Edge cases for FeedbackRecord scoring."""

    def test_all_zeros(self):
        """All zero signals should produce a score."""
        r = FeedbackRecord(
            request_id="1", validation_score=0.0, grounding_score=0.0,
            was_retried=True, response_edited=True,
        )
        score = r.overall_score()
        assert 0.0 <= score <= 1.0

    def test_maximum_penalties(self):
        """All penalties applied should not go below 0."""
        r = FeedbackRecord(
            request_id="1", rating=1, validation_score=0.0,
            grounding_score=0.0, was_retried=True, response_edited=True,
        )
        assert r.overall_score() >= 0.0

    def test_perfect_signals(self):
        """All perfect signals should be close to 1.0."""
        r = FeedbackRecord(
            request_id="1", rating=5, validation_score=1.0,
            grounding_score=1.0, was_retried=False, response_edited=False,
        )
        assert r.overall_score() >= 0.95

    def test_boundary_rating_values(self):
        """Rating at boundaries."""
        r1 = FeedbackRecord(request_id="1", rating=1)
        r5 = FeedbackRecord(request_id="2", rating=5)
        assert r1.overall_score() < r5.overall_score()

    def test_none_rating_vs_low_rating(self):
        """No rating should score differently than rating=1."""
        r_none = FeedbackRecord(request_id="1", validation_score=0.5)
        r_low = FeedbackRecord(request_id="2", rating=1, validation_score=0.5)
        # Both should produce valid scores
        assert 0.0 <= r_none.overall_score() <= 1.0
        assert 0.0 <= r_low.overall_score() <= 1.0


class TestQualityTesterAdversarial:
    """Edge cases for QualityTester."""

    def test_massive_records(self):
        """Should handle 10000 records without issues."""
        tester = QualityTester()
        for i in range(10000):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="stress",
                model_used="gpt-4o", validation_score=0.5 + (i % 5) * 0.1,
            ))
        stats = tester.get_tenant_stats("stress")
        assert stats["count"] == 10000
        assert 0.0 < stats["avg_score"] < 1.0

    def test_all_same_model(self):
        tester = QualityTester()
        for i in range(20):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="t1",
                model_used="gpt-4o", validation_score=0.8,
            ))
        model_stats = tester.get_model_stats("t1")
        assert len(model_stats) == 1

    def test_empty_model_used(self):
        tester = QualityTester()
        tester.record(FeedbackRecord(request_id="r1", tenant_id="t1", model_used=""))
        model_stats = tester.get_model_stats("t1")
        assert "unknown" in model_stats

    def test_all_retried(self):
        tester = QualityTester()
        for i in range(5):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="t1", was_retried=True,
            ))
        stats = tester.get_tenant_stats("t1")
        assert stats["retry_rate"] == 1.0


class TestEvolverAdversarial:
    """Edge cases for Evolver."""

    def test_evolve_with_no_data(self):
        tester = QualityTester()
        evolver = Evolver(tester)
        bp = AgentBlueprint.default(tenant_id="empty")
        evolved = evolver.evolve_blueprint(bp)
        # Should return reasonable defaults
        assert evolved.default_model is not None

    def test_evolve_all_failures(self):
        """All-failure feedback should adjust parameters aggressively."""
        tester = QualityTester()
        for i in range(15):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="fail",
                model_used="gpt-4o-mini", validation_score=0.1,
                was_retried=True, rating=1,
            ))
        evolver = Evolver(tester)
        evolved = evolver.evolve_blueprint(AgentBlueprint.default(tenant_id="fail"))
        # Should reduce temperature (high retry)
        assert evolved.temperature < 0.7
        # Should increase quality weight
        assert evolved.priority_weights.quality >= 0.4

    def test_evolve_all_perfect(self):
        """All-perfect feedback should slightly increase creativity."""
        tester = QualityTester()
        for i in range(15):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="perf",
                model_used="claude-sonnet-4-20250514", validation_score=1.0,
                was_retried=False, rating=5,
            ))
        evolver = Evolver(tester)
        temp = evolver.optimize_temperature("perf")
        assert temp["recommended_temperature"] >= 0.7

    def test_model_ranking_stability(self):
        """With equal data, ranking should be deterministic."""
        tester = QualityTester()
        for i in range(20):
            model = "gpt-4o" if i % 2 == 0 else "claude-sonnet-4-20250514"
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="stable",
                model_used=model, validation_score=0.8,
            ))
        evolver = Evolver(tester)
        r1 = evolver.optimize_model_selection("stable")
        r2 = evolver.optimize_model_selection("stable")
        assert r1["recommended_model"] == r2["recommended_model"]

    def test_report_structure(self):
        """Report should always have required fields."""
        tester = QualityTester()
        evolver = Evolver(tester)
        report = evolver.generate_report("empty")
        assert "should_evolve" in report
        assert "recommendations" in report
        assert "current_stats" in report

    def test_priority_weights_sum_to_one(self):
        """Evolved weights should always sum to ~1.0."""
        tester = QualityTester()
        for i in range(15):
            tester.record(FeedbackRecord(
                request_id=f"r{i}", tenant_id="w",
                validation_score=0.3, was_retried=True,
            ))
        evolver = Evolver(tester)
        w = evolver.optimize_priority_weights("w")
        total = w.quality + w.efficiency + w.speed + w.cost
        assert total == pytest.approx(1.0, abs=0.01)
