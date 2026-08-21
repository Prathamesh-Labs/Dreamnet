from sqlalchemy.orm import Session
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.services.llm.factory import LLMProviderFactory
from app.services.experiment.sandbox import SandboxExecutor, SecurityViolationError
import json
import re
from typing import Any

class ExperimentRunner:
    @staticmethod
    def run_experiment(experiment_id: Any, db: Session) -> ExperimentResult:
        # 1. Fetch experiment
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment with ID {experiment_id} not found.")

        # 2. Update status to RUNNING
        experiment.status = "RUNNING"
        db.commit()

        # Prepare experiment details for LLM generator
        experiment_dict = {
            "objective": experiment.objective,
            "baseline": experiment.baseline,
            "treatment": experiment.treatment,
            "variables": experiment.variables or {},
            "dataset": experiment.dataset,
            "metrics": experiment.metrics or [],
            "procedure": experiment.procedure or [],
            "expected_outcome": experiment.expected_outcome,
            "measurable_success_criteria": experiment.measurable_success_criteria
        }

        stdout = ""
        stderr = ""
        status = "FAILED"
        metrics = {}
        execution_time_ms = 0.0

        try:
            # 3. Resolve LLM provider and generate script
            provider = LLMProviderFactory.get_provider()
            code = provider.generate_experiment_code(experiment_dict)

            # 4. Execute inside Sandbox
            result = SandboxExecutor.run_code(code)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            status = result.get("status", "FAILED")
            execution_time_ms = result.get("execution_time_ms", 0.0)

            # 5. Parse metrics from stdout
            if status == "COMPLETED" and stdout:
                pattern = r"__DREAMNET_METRICS_START__\s*(.*?)\s*__DREAMNET_METRICS_END__"
                match = re.search(pattern, stdout, re.DOTALL)
                if match:
                    try:
                        metrics_str = match.group(1).strip()
                        metrics = json.loads(metrics_str)
                    except Exception as e:
                        stderr += f"\nError parsing metrics JSON block: {str(e)}"
                        status = "FAILED"
                else:
                    stderr += "\nError: __DREAMNET_METRICS__ output block not found in script execution logs."
                    status = "FAILED"

        except SecurityViolationError as e:
            stderr = f"Security Violation: {str(e)}\nExecution was blocked by AST Sandbox."
            status = "FAILED"
        except Exception as e:
            stderr = f"Execution Error: {str(e)}"
            status = "FAILED"

        # 6. Delete any existing experiment results (to prevent duplicate key)
        db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment.id).delete()

        # 7. Save experiment result
        db_result = ExperimentResult(
            experiment_id=experiment.id,
            stdout=stdout,
            stderr=stderr,
            metrics=metrics,
            artifacts=[],  # Default empty artifacts list
            status=status,
            execution_time_ms=execution_time_ms
        )
        db.add(db_result)

        # 8. Update parent status
        experiment.status = status
        db.commit()
        db.refresh(db_result)

        return db_result
