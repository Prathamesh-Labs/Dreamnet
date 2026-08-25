import unittest
from uuid import uuid4
import app.database.base
from app.models.hypothesis import Hypothesis
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.evaluation import Evaluation
from app.engines.discovery.detector import DiscoveryDetector
from app.engines.discovery.scorer import DiscoveryScorer

class TestDiscoveryDetector(unittest.TestCase):
    def setUp(self):
        self.question_id = uuid4()

    def test_no_discoveries_when_no_data(self):
        patterns = DiscoveryDetector.detect_patterns([])
        self.assertEqual(len(patterns), 0)

    def test_unexpected_magnitude_detection(self):
        # Setup hypothesis with a completed experiment and evaluation showing high latency reduction
        h = Hypothesis(
            id=uuid4(),
            question_id=self.question_id,
            statement="Model quantization (INT8) reduces latency with negligible impact.",
            rationale="Test rationale",
            status="SUPPORTED"
        )
        exp = Experiment(
            id=uuid4(),
            hypothesis_id=h.id,
            objective="Objective test",
            baseline="Baseline FP32",
            treatment="INT8 precision",
            dataset="Validation set",
            measurable_success_criteria="Inference speedup >= 2.0x, latency reduction >= 10.0%",
            approved=True,
            status="COMPLETED"
        )
        res = ExperimentResult(
            id=uuid4(),
            experiment_id=exp.id,
            metrics={"latency_reduction_pct": 35.0, "speedup_factor": 2.5},
            execution_time_ms=250.0
        )
        # Check rule passed (e.g. latency_reduction_pct >= 10.0%)
        evidence = [
            {"metric": "latency_reduction_pct", "rule": "latency_reduction_pct >= 10.0%", "observed": 35.0, "passed": True}
        ]
        val = Evaluation(
            id=uuid4(),
            experiment_id=exp.id,
            verdict="SUPPORTED",
            evidence=evidence,
            confidence=0.95
        )
        
        # Link relationships manually for local validation
        h.experiment = exp
        exp.result = res
        exp.evaluation = val
        
        patterns = DiscoveryDetector.detect_patterns([h])
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].pattern_type, "unexpected_magnitude")

        
        # Test scoring
        novelty, conf, sig, repro = DiscoveryScorer.score_pattern(patterns[0], val.confidence)
        self.assertEqual(novelty, 0.80)
        self.assertEqual(conf, 0.95)
        self.assertGreater(sig, 0.60)
        self.assertEqual(repro, 0.50) # only 1 supporting experiment

    def test_unexpected_direction_detection(self):
        h = Hypothesis(
            id=uuid4(),
            question_id=self.question_id,
            statement="Model quantization reduces latency.",
            rationale="Test rationale",
            status="REJECTED"
        )
        exp = Experiment(
            id=uuid4(),
            hypothesis_id=h.id,
            objective="Objective test",
            baseline="Baseline FP32",
            treatment="INT8 precision",
            dataset="Validation set",
            measurable_success_criteria="latency reduction >= 10.0%",
            approved=True,
            status="FAILED"
        )
        res = ExperimentResult(
            id=uuid4(),
            experiment_id=exp.id,
            metrics={"latency_reduction_pct": -15.0},
            execution_time_ms=250.0
        )
        # Check failed because it regressioned (observed: -15.0%)
        evidence = [
            {"metric": "latency_reduction_pct", "rule": "latency_reduction_pct >= 10.0%", "observed": -15.0, "passed": False}
        ]
        val = Evaluation(
            id=uuid4(),
            experiment_id=exp.id,
            verdict="REJECTED",
            evidence=evidence,
            confidence=0.90
        )
        
        h.experiment = exp
        exp.result = res
        exp.evaluation = val
        
        patterns = DiscoveryDetector.detect_patterns([h])
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].pattern_type, "unexpected_direction")
        
        novelty, conf, sig, repro = DiscoveryScorer.score_pattern(patterns[0], val.confidence)
        self.assertEqual(novelty, 0.75)
        self.assertEqual(conf, 0.90)

    def test_contradiction_detection(self):
        h1 = Hypothesis(id=uuid4(), question_id=self.question_id, statement="H1 statement", status="SUPPORTED")
        exp1 = Experiment(id=uuid4(), hypothesis_id=h1.id, objective="O1", baseline="B", treatment="T", dataset="D", measurable_success_criteria="criteria", approved=True, status="COMPLETED")
        res1 = ExperimentResult(id=uuid4(), experiment_id=exp1.id, metrics={}, execution_time_ms=100.0)
        val1 = Evaluation(id=uuid4(), experiment_id=exp1.id, verdict="SUPPORTED", evidence=[], confidence=0.90)
        h1.experiment = exp1
        exp1.result = res1
        exp1.evaluation = val1

        h2 = Hypothesis(id=uuid4(), question_id=self.question_id, statement="H2 statement", status="REJECTED")
        exp2 = Experiment(id=uuid4(), hypothesis_id=h2.id, objective="O2", baseline="B", treatment="T", dataset="D", measurable_success_criteria="criteria", approved=True, status="FAILED")
        res2 = ExperimentResult(id=uuid4(), experiment_id=exp2.id, metrics={}, execution_time_ms=100.0)
        val2 = Evaluation(id=uuid4(), experiment_id=exp2.id, verdict="REJECTED", evidence=[], confidence=0.85)
        h2.experiment = exp2
        exp2.result = res2
        exp2.evaluation = val2

        patterns = DiscoveryDetector.detect_patterns([h1, h2])
        self.assertTrue(any(p.pattern_type == "contradiction" for p in patterns))

if __name__ == "__main__":
    unittest.main()
