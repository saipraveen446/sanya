from app.config import settings
from app.llm.providers.compat import OpenAICompatProvider

# Google AI Studio, OpenAI-compatible endpoint.
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def build() -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="gemini",
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=BASE_URL,
    )
