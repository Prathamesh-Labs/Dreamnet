import google.generativeai as genai
from typing import Any
import json
from app.services.llm.base import BaseLLMProvider
from app.engines.hypothesis.schemas import HypothesisEngineResponse
from app.engines.experiment.schemas import ExperimentEngineResponse

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        # Using gemini-1.5-flash for fast and structured reasoning
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_hypotheses(self, question: str) -> list[dict[str, Any]]:
        print(f"[GeminiProvider] Calling API for question: '{question}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"Given the research question below, generate exactly 3 competing, distinct, "
            f"and falsifiable hypotheses to investigate the question.\n\n"
            f"Research Question:\n{question}\n\n"
            f"Ensure H1, H2, and H3 examine different primary mechanisms "
            f"(e.g., if H1 focuses on model quantization, H2 should focus on knowledge distillation, "
            f"and H3 should focus on architecture changes). Do not generate redundant hypotheses."
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=HypothesisEngineResponse,
                    temperature=0.7
                )
            )
            data = json.loads(response.text)
            return data.get("hypotheses", [])
        except Exception as e:
            print(f"[GeminiProvider] Error generating hypotheses: {e}")
            raise e

    def design_experiment(self, hypothesis: dict[str, Any]) -> dict[str, Any]:
        print(f"[GeminiProvider] Designing experiment for hypothesis: '{hypothesis.get('statement')}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"Given the scientific hypothesis details below, design a structured, testable, "
            f"and reproducible experiment specification.\n\n"
            f"Hypothesis Statement:\n{hypothesis.get('statement')}\n\n"
            f"Rationale:\n{hypothesis.get('rationale')}\n\n"
            f"Predicted Outcome:\n{hypothesis.get('predicted_outcome')}\n\n"
            f"Boundary Assumptions:\n{', '.join(hypothesis.get('assumptions', []))}\n\n"
            f"Variables:\n{', '.join(hypothesis.get('variables', []))}\n\n"
            f"Ensure the generated experiment provides complete details for: objective, baseline, "
            f"treatment, dataset, metrics, expected outcome, measurable success criteria, and a "
            f"step-by-step procedure list. Categorize variables clearly into independent, dependent, and control."
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ExperimentEngineResponse,
                    temperature=0.7
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(f"[GeminiProvider] Error designing experiment: {e}")
            raise e

    def generate_experiment_code(self, experiment: dict[str, Any]) -> str:
        print(f"[GeminiProvider] Generating experiment code for objective: '{experiment.get('objective')}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"Write a self-contained Python script to simulate or execute the following experiment plan:\n\n"
            f"Objective:\n{experiment.get('objective')}\n\n"
            f"Baseline Setup:\n{experiment.get('baseline')}\n\n"
            f"Treatment:\n{experiment.get('treatment')}\n\n"
            f"Procedure:\n{', '.join(experiment.get('procedure', []))}\n\n"
            f"Success Criteria:\n{experiment.get('measurable_success_criteria')}\n\n"
            f"CRITICAL SECURITY CONSTRAINTS:\n"
            f"- The code will run in a highly restricted AST sandbox.\n"
            f"- Do NOT import: 'os', 'sys', 'subprocess', 'socket', 'ctypes', 'urllib', 'requests', or 'builtins'.\n"
            f"- Do NOT call forbidden functions: 'open', 'eval', 'exec', 'compile', or '__import__'.\n"
            f"- Use only standard python libraries: 'time', 'json', 'math', 'random', 'statistics'.\n\n"
            f"OUTPUT METRICS CONSTRAINT:\n"
            f"- The script must calculate numerical values representing the variables and target metrics.\n"
            f"- At the very end of execution, the script MUST output the computed quantitative metrics strictly "
            f"in a JSON block printed to stdout, bounded by special markers like so:\n"
            f"print('__DREAMNET_METRICS_START__')\n"
            f"print(json.dumps(metrics_dict))\n"
            f"print('__DREAMNET_METRICS_END__')\n\n"
            f"Return ONLY the executable Python script code. Do not include markdown code block backticks (e.g. no ```python) or any other conversational text."
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2
                )
            )
            # Remove any markdown formatting backticks if they are returned by chance
            code = response.text.strip()
            if code.startswith("```python"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            print(f"[GeminiProvider] Error generating experiment code: {e}")
            raise e


