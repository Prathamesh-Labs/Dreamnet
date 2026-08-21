from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_hypotheses(self, question: str) -> list[dict[str, Any]]:
        """
        Given a research question, return a list of structured hypothesis dictionaries.
        Each dict should match:
        {
            "statement": str,
            "rationale": str,
            "assumptions": list[str],
            "variables": list[str],
            "predicted_outcome": str,
            "confidence": float,
            "testability": str  # 'HIGH', 'MEDIUM', 'LOW'
        }
        """
        pass

    @abstractmethod
    def design_experiment(self, hypothesis: dict[str, Any]) -> dict[str, Any]:
        """
        Given a hypothesis dictionary, design a structured experiment.
        Should return a dictionary matching the Experiment schema:
        {
            "objective": str,
            "baseline": str,
            "treatment": str,
            "variables": {
                "independent": list[str],
                "dependent": list[str],
                "control": list[str]
            },
            "dataset": str,
            "metrics": list[str],
            "procedure": list[str],
            "expected_outcome": str,
            "measurable_success_criteria": str
        }
        """
        pass

    @abstractmethod
    def generate_experiment_code(self, experiment: dict[str, Any]) -> str:
        """
        Given an experiment dictionary, generate executable Python code.
        The code must be safe, run inside the AST sandbox, and output
        computed metrics inside bounded JSON blocks:
        __DREAMNET_METRICS_START__
        {"metric_name": value}
        __DREAMNET_METRICS_END__
        """
        pass


