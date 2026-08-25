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
    @abstractmethod
    def explain_evaluation(self, hypothesis: str, criteria: str, metrics: dict[str, Any], verdict: str, checks: list[dict[str, Any]]) -> str:
        """
        Generates a natural language explanation of why the experiment results
        support, reject, or are inconclusive regarding the hypothesis.
        """
        pass

    @abstractmethod
    def generate_followup_hypothesis(self, question: str, failed_hypothesis: str, failed_criteria: str, failed_metrics: dict[str, Any]) -> dict[str, Any]:
        """
        Given a failed hypothesis and the metrics that failed, generate a new
        refinement hypothesis to attempt to resolve the issue.
        """
        pass

    @abstractmethod
    def explain_discovery(self, title: str, pattern_type: str, evidence: dict[str, Any], description: str) -> str:
        """
        Generates a natural language explanation of a detected discovery candidate pattern.
        """
        pass

    @abstractmethod
    def simulate_peer_review(self, question: str, statement: str) -> list[dict[str, Any]]:
        """
        Simulates peer review discussions for space agency/scientific validation.
        """
        pass

    @abstractmethod
    def generate_hypothesis_from_discovery(self, discovery_title: str, discovery_observation: str, evidence: dict[str, Any], parent_experiment: dict[str, Any]) -> dict[str, Any]:
        """
        Generates a new testable hypothesis derived from a detected discovery pattern.
        """
        pass






