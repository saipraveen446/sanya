from app.config import settings
from app.llm.providers.compat import OpenAICompatProvider

# Paid fallback after Gemini, Groq, and OpenRouter. Also used when DEFAULT_LLM_PROVIDER=openai.
BASE_URL = "https://api.openai.com/v1"


def build() -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="openai",
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=BASE_URL,
    )
