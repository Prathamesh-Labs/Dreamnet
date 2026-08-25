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

    def explain_evaluation(self, hypothesis: str, criteria: str, metrics: dict[str, Any], verdict: str, checks: list[dict[str, Any]]) -> str:
        print(f"[GeminiProvider] Explaining evaluation for verdict: '{verdict}'")
        
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"An experiment was conducted to evaluate the following hypothesis:\n"
            f"Hypothesis: {hypothesis}\n"
            f"Measurable Success Criteria: {criteria}\n\n"
            f"The sandbox execution yielded these quantitative metrics:\n"
            f"{json.dumps(metrics, indent=2)}\n\n"
            f"A deterministic checker evaluated the metrics and returned the following verdict:\n"
            f"Verdict: {verdict}\n"
            f"Checks state:\n"
            f"{json.dumps(checks, indent=2)}\n\n"
            f"Write a concise, professional explanation (2-3 sentences max) interpreting these results.\n"
            f"Detail how the metrics values relate directly to the success criteria thresholds, "
            f"and explain the scientific justification for the verdict: {verdict}.\n"
            f"Do not include any greeting or signature."
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.4
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiProvider] Error generating evaluation explanation: {e}")
            raise e

    def generate_followup_hypothesis(self, question: str, failed_hypothesis: str, failed_criteria: str, failed_metrics: dict[str, Any]) -> dict[str, Any]:
        print(f"[GeminiProvider] Generating follow-up hypothesis for: '{failed_hypothesis}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"You are conducting research on the question: '{question}'\n\n"
            f"The previous hypothesis was rejected during empirical testing:\n"
            f"Failed Hypothesis: {failed_hypothesis}\n"
            f"Failed Success Criteria: {failed_criteria}\n"
            f"Observed Metrics: {json.dumps(failed_metrics, indent=2)}\n\n"
            f"Analyze why it failed and propose exactly one new refinement/follow-up hypothesis "
            f"that attempts to resolve the failure or adjust the parameters (e.g. tuning quantization parameters, "
            f"using different layers, or adjusting block sizes)."
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
            hypotheses = data.get("hypotheses", [])
            if hypotheses:
                return hypotheses[0]
            raise ValueError("No hypotheses returned in follow-up response.")
        except Exception as e:
            print(f"[GeminiProvider] Error generating follow-up hypothesis: {e}")
            raise e

    def explain_discovery(self, title: str, pattern_type: str, evidence: dict[str, Any], description: str) -> str:
        print(f"[GeminiProvider] Explaining discovery candidate: '{title}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"A deterministic anomaly detector identified a potential discovery candidate:\n"
            f"Title: {title}\n"
            f"Pattern Type: {pattern_type}\n"
            f"Detected Evidence: {json.dumps(evidence, indent=2)}\n"
            f"Description: {description}\n\n"
            f"Write a professional, detailed explanation (3-4 sentences) interpreting this scientific pattern.\n"
            f"Explain why this pattern is interesting or contradictory, what physical/computational mechanism could cause it, "
            f"and propose a logical research pathway forward. Use only the provided evidence numbers; do not invent new facts."
        )
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.6
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiProvider] Error explaining discovery: {e}")
            raise e

    def simulate_peer_review(self, question: str, statement: str) -> list[dict[str, Any]]:
        # Structured fallback scientific review dialogue
        return [
            {
                "sender": "Physicist/Systems Specialist",
                "message": f"Regarding question '{question}' and hypothesis '{statement}', we must investigate the hardware bus bottlenecks. Reducing float operations is promising, but if system memory throughput is saturated, CPU latency will remain unchanged.",
                "avatar": "🛰️"
            },
            {
                "sender": "Statistician / Verification Specialist",
                "message": "Agreed. The experiment design must record standard deviation across a minimum of 30 execution cycles to isolate true performance speedup from thread scheduling noise.",
                "avatar": "📊"
            },
            {
                "sender": "Synthesis Agent",
                "message": "Adjusted experiment parameters to capture statistical latency distribution and independent memory constraints. The hypothesis is approved for sandboxed run.",
                "avatar": "🧠"
            }
        ]

    def generate_hypothesis_from_discovery(self, discovery_title: str, discovery_observation: str, evidence: dict[str, Any], parent_experiment: dict[str, Any]) -> dict[str, Any]:
        print(f"[GeminiProvider] Generating hypothesis from discovery: '{discovery_title}'")
        prompt = (
            f"You are DREAMNET, an autonomous scientific discovery assistant.\n"
            f"A potential scientific discovery candidate was detected:\n"
            f"Title: {discovery_title}\n"
            f"Observation: {discovery_observation}\n"
            f"Evidence: {json.dumps(evidence, indent=2)}\n"
            f"Parent Experiment Context: {json.dumps(parent_experiment, indent=2)}\n\n"
            f"Generate exactly one new, testable, and falsifiable scientific hypothesis that is "
            f"derived directly from this discovery. This hypothesis should aim to explain the mechanism "
            f"behind this unexpected pattern or anomaly."
        )
        
        try:
            from app.engines.hypothesis.schemas import SingleHypothesisOutput
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=SingleHypothesisOutput,
                    temperature=0.7
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[GeminiProvider] Error generating hypothesis from discovery: {e}")
            raise e






