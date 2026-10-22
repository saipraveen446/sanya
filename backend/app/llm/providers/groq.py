from app.config import settings
from app.llm.providers.compat import OpenAICompatProvider

BASE_URL = "https://api.groq.com/openai/v1"


def build() -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="groq",
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=BASE_URL,
    )
