from app.infrastructure.config import get_settings
from app.domain.external.llm import LLM
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.llm.gemini_llm import GeminiLLM

def get_llm() -> LLM:
    """
    Returns an instance of the LLM based on the provider specified in the settings.
    """
    settings = get_settings()
    provider = getattr(settings, 'model_provider', 'openai')

    if provider == 'gemini':
        return GeminiLLM()
    elif provider == 'openai':
        return OpenAILLM()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
