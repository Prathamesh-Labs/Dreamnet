from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mock import MockProvider

class LLMProviderFactory:
    @staticmethod
    def get_provider() -> BaseLLMProvider:
        if settings.GEMINI_API_KEY:
            print("[LLMProviderFactory] Using GeminiProvider.")
            return GeminiProvider(api_key=settings.GEMINI_API_KEY)
        
        # Fallback to Mock Provider when no keys are found
        print("[LLMProviderFactory] WARNING: No API keys configured. Falling back to MockProvider.")
        return MockProvider()
