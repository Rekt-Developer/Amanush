from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.llm.gemini_llm import GeminiLLM

def get_llm() -> LLM:
    """
    Factory function to get the appropriate LLM based on the configuration.
    """
    settings = get_settings()
    
    if settings.model_provider == "gemini":
        return GeminiLLM()
    elif settings.model_provider == "openai":
        return OpenAILLM()
    else:
        raise ValueError(f"Unsupported model provider: {settings.model_provider}")
