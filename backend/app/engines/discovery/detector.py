from typing import Any
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.evaluation import Evaluation
from app.models.hypothesis import Hypothesis
from app.engines.discovery.schemas import DetectedPattern

class DiscoveryDetector:
    @staticmethod
    def detect_patterns(hypotheses: list[Hypothesis]) -> list[DetectedPattern]:
        patterns: list[DetectedPattern] = []
        
        # Helper lists to hold processed elements
        completed_exps: list[tuple[Hypothesis, Experiment, ExperimentResult, Evaluation]] = []
        
        for h in hypotheses:
            if h.experiment and h.experiment.result and h.experiment.evaluation:
                completed_exps.append((h, h.experiment, h.experiment.result, h.experiment.evaluation))

        if not completed_exps:
            return patterns

        # 1. Unexpected Magnitude & Direction Detector
        for h, exp, res, val in completed_exps:
            metrics = res.metrics or {}
            evidence_checks = val.evidence or []
            
            for check in evidence_checks:
                metric_name = check.get("metric", "")
                observed = check.get("observed")
                rule = check.get("rule", "")
                passed = check.get("passed", False)
                
                if observed is None:
                    continue
                
                # Check for criteria values in the rule string (e.g. "latency_reduction_pct >= 20.0%")
                # Extract number
                import re
                num_match = re.search(r'([0-9\.]+)', rule)
                if not num_match:
                    continue
                threshold = float(num_match.group(1))

                # Rule A: Unexpected Magnitude
                # If metric is positive/passed and observed is vastly larger than threshold (e.g. >20% delta above it)
                if passed and threshold > 0:
                    delta_pct = ((observed - threshold) / threshold) * 100.0
                    if delta_pct >= 20.0:
                        patterns.append(DetectedPattern(
                            pattern_type="unexpected_magnitude",
                            title=f"Unexpected effect magnitude in {metric_name.replace('_', ' ')}",
                            description=(
                                f"For hypothesis '{h.statement}', the observed {metric_name.replace('_', ' ')} was "
                                f"{observed:.2f}%, which is {delta_pct:.1f}% higher than the expected threshold of {threshold:.2f}%."
                              ),
                            evidence={"metric": metric_name, "observed": observed, "expected_threshold": threshold, "delta_pct": delta_pct},
                            supporting_experiments=[str(exp.id)]
                        ))

                # Rule B: Unexpected Direction
                # If check failed because metric was in the opposite direction (e.g. latency reduction < 0 or accuracy gain < 0)
                # indicating a performance flip
                if not passed:
                    if (metric_name == "latency_reduction_pct" and observed < 0) or \
                       (metric_name == "accuracy_gain" and observed < 0) or \
                       (metric_name == "improvement_percentage" and observed < 0):
                        patterns.append(DetectedPattern(
                            pattern_type="unexpected_direction",
                            title=f"Opposite performance direction detected in {metric_name.replace('_', ' ')}",
                            description=(
                                f"Expected improvement for '{h.statement}', but observed a negative delta of "
                                f"{observed:.2f}% indicating a performance regression instead of gain."
                            ),
                            evidence={"metric": metric_name, "observed": observed, "expected_threshold": threshold},
                            supporting_experiments=[str(exp.id)]
                        ))

        # 2. Contradiction Detector
        # If one experiment supports H_a and another rejects H_b for the same question
        supported_list = [exp for h, exp, res, val in completed_exps if val.verdict == "SUPPORTED"]
        rejected_list = [exp for h, exp, res, val in completed_exps if val.verdict == "REJECTED"]
        
        if len(supported_list) >= 1 and len(rejected_list) >= 1:
            patterns.append(DetectedPattern(
                pattern_type="contradiction",
                title="Contradicting empirical research evidence",
                description=(
                    f"Research question has conflicting outcomes. Experiment {supported_list[0].id} "
                    f"supported its hypothesis, while Experiment {rejected_list[0].id} rejected its hypothesis."
                ),
                evidence={
                    "supported_experiments": [str(e.id) for e in supported_list],
                    "rejected_experiments": [str(e.id) for e in rejected_list]
                },
                supporting_experiments=[str(e.id) for e in supported_list + rejected_list]
            ))

        # 3. Repeated Pattern Detector
        # If we have multiple successful experiments showing improvement in latency reduction
        latency_exps = []
        for h, exp, res, val in completed_exps:
            if val.verdict == "SUPPORTED":
                for check in (val.evidence or []):
                    if check.get("metric") == "latency_reduction_pct" and check.get("passed"):
                        latency_exps.append(exp)
                        
        if len(latency_exps) >= 2:
            patterns.append(DetectedPattern(
                pattern_type="repeated_pattern",
                title="Consistently repeated latency optimization pattern",
                description=(
                    f"Consistently observed latency reduction across {len(latency_exps)} separate experimental "
                    f"trials, confirming reproducibility of the optimization pathway."
                ),
                evidence={"trials_count": len(latency_exps), "experiment_ids": [str(e.id) for e in latency_exps]},
                supporting_experiments=[str(e.id) for e in latency_exps]
            ))

        return patterns
