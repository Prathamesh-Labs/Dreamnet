import google.generativeai as genai
from typing import Any
import json
from app.services.llm.base import BaseLLMProvider
from app.engines.hypothesis.schemas import HypothesisEngineResponse

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
