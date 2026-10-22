from app.config import settings
from app.llm.providers.compat import OpenAICompatProvider

BASE_URL = "https://openrouter.ai/api/v1"


def build() -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="openrouter",
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=BASE_URL,
        extra_headers={
            "HTTP-Referer": settings.openrouter_http_referer,
            "X-Title": settings.openrouter_app_name,
        },
    )
