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
