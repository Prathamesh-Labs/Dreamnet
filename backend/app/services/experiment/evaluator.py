import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.evaluation import Evaluation
from app.services.llm.factory import LLMProviderFactory
from typing import Any

class ExperimentEvaluator:
    @staticmethod
    def compare(observed: float, op: str, threshold: float) -> bool:
        if op == "<": return observed < threshold
        elif op == "<=": return observed <= threshold
        elif op == ">": return observed > threshold
        elif op == ">=": return observed >= threshold
        elif op == "==": return observed == threshold
        return False

    @staticmethod
    def evaluate_metrics_deterministically(metrics: dict[str, Any], criteria: str) -> tuple[str, float, list[dict[str, Any]]]:
        # Preprocess metrics dynamically
        preprocessed = dict(metrics)

        # 1. Latency & Speedup
        if "baseline_latency_ms" in preprocessed and "treatment_latency_ms" in preprocessed:
            base_lat = preprocessed["baseline_latency_ms"]
            treat_lat = preprocessed["treatment_latency_ms"]
            if base_lat > 0:
                preprocessed["latency_reduction_pct"] = ((base_lat - treat_lat) / base_lat) * 100.0
                preprocessed["speedup_factor"] = base_lat / treat_lat

        # 2. Accuracy Drop
        if "baseline_accuracy" in preprocessed and "treatment_accuracy" in preprocessed:
            preprocessed["accuracy_delta"] = preprocessed["baseline_accuracy"] - preprocessed["treatment_accuracy"]

        # 3. Accuracy Gain
        if "student_baseline_accuracy" in preprocessed and "student_distilled_accuracy" in preprocessed:
            preprocessed["accuracy_gain"] = preprocessed["student_distilled_accuracy"] - preprocessed["student_baseline_accuracy"]

        criteria_lower = criteria.lower().replace("≥", ">=").replace("≤", "<=")
        checks = []

        # P-value rule
        p_match = re.search(r'(p-value|p_value|p\s*value|p)\s*.*?(<|<=|>|>=|==)\s*([0-9\.]+)', criteria_lower)
        if p_match:
            op = p_match.group(2)
            val = float(p_match.group(3))
            observed_val = preprocessed.get("p_value")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "p_value",
                    "rule": f"p_value {op} {val}",
                    "observed": observed_val,
                    "passed": passed
                })

        # Latency reduction rule
        lat_match = re.search(r'latency.*?(reduction|drop|by|gain|improvement)?\s*.*?(>=|<=|>|<|==)\s*([0-9\.]+)', criteria_lower)
        if lat_match:
            op = lat_match.group(2)
            val = float(lat_match.group(3))
            observed_val = preprocessed.get("latency_reduction_pct") or preprocessed.get("latency_reduction")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "latency_reduction_pct",
                    "rule": f"latency_reduction_pct {op} {val}%",
                    "observed": observed_val,
                    "passed": passed
                })

        # Speedup factor rule
        speedup_match = re.search(r'speedup.*?(factor)?\s*.*?(>=|<=|>|<|==)\s*([0-9\.]+)', criteria_lower)
        if speedup_match:
            op = speedup_match.group(2)
            val = float(speedup_match.group(3))
            observed_val = preprocessed.get("speedup_factor")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "speedup_factor",
                    "rule": f"speedup_factor {op} {val}x",
                    "observed": observed_val,
                    "passed": passed
                })

        # Accuracy loss/drop rule
        acc_loss_match = re.search(r'accuracy\s*(loss|drop|delta|drop_pct)?\s*.*?(<|<=|>|>=|==)\s*([0-9\.]+)', criteria_lower)
        if acc_loss_match:
            op = acc_loss_match.group(2)
            val = float(acc_loss_match.group(3))
            observed_val = preprocessed.get("accuracy_delta")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "accuracy_delta",
                    "rule": f"accuracy_delta {op} {val}%",
                    "observed": observed_val,
                    "passed": passed
                })

        # Accuracy gain rule
        acc_gain_match = re.search(r'accuracy\s*gain\s*.*?(>=|<=|>|<|==)\s*([0-9\.]+)', criteria_lower)
        if acc_gain_match:
            op = acc_gain_match.group(1)
            val = float(acc_gain_match.group(2))
            observed_val = preprocessed.get("accuracy_gain")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "accuracy_gain",
                    "rule": f"accuracy_gain {op} {val}%",
                    "observed": observed_val,
                    "passed": passed
                })

        # Improvement rule
        imp_match = re.search(r'improvement.*?\s*.*?(>=|<=|>|<|==)\s*([0-9\.]+)', criteria_lower)
        if imp_match:
            op = imp_match.group(1)
            val = float(imp_match.group(2))
            observed_val = preprocessed.get("improvement_percentage")
            if observed_val is not None:
                passed = ExperimentEvaluator.compare(observed_val, op, val)
                checks.append({
                    "metric": "improvement_percentage",
                    "rule": f"improvement_percentage {op} {val}%",
                    "observed": observed_val,
                    "passed": passed
                })

        if not checks:
            # Fallback inconclusive if no matching metrics were parsed
            return "INCONCLUSIVE", 0.50, checks

        # If any check fails -> REJECTED, else -> SUPPORTED
        all_passed = all(c["passed"] for c in checks)
        verdict = "SUPPORTED" if all_passed else "REJECTED"
        confidence = 0.95 if all_passed else 0.90

        return verdict, confidence, checks

    @staticmethod
    def evaluate_experiment(experiment_id: Any, db: Session) -> Evaluation:
        # 1. Fetch Experiment and Result
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment with ID {experiment_id} not found.")

        result = db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).first()
        if not result:
            raise ValueError(f"Execution results for experiment {experiment_id} not found. Run the experiment first.")

        # 2. Run deterministic evaluation
        verdict, confidence, checks = ExperimentEvaluator.evaluate_metrics_deterministically(
            result.metrics or {}, 
            experiment.measurable_success_criteria
        )

        # 3. Generate LLM observation interpretation
        provider = LLMProviderFactory.get_provider()
        hypothesis_statement = experiment.hypothesis.statement if experiment.hypothesis else ""
        
        try:
            summary = provider.explain_evaluation(
                hypothesis=hypothesis_statement,
                criteria=experiment.measurable_success_criteria,
                metrics=result.metrics or {},
                verdict=verdict,
                checks=checks
            )
        except Exception as e:
            # Fallback explanation if LLM generation fails
            summary = f"Deterministic verdict: {verdict}. Verification rules state: " + ", ".join(
                [f"{c['rule']} ({'Passed' if c['passed'] else 'Failed'}, Observed: {c['observed']})" for c in checks]
            )

        # 4. Save evaluation
        db.query(Evaluation).filter(Evaluation.experiment_id == experiment.id).delete()

        db_evaluation = Evaluation(
            experiment_id=experiment.id,
            verdict=verdict,
            evidence=checks,
            confidence=confidence,
            observations=summary
        )
        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)

        return db_evaluation
