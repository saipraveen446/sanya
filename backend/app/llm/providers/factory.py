"""Pick which vendor to use from DEFAULT_LLM_PROVIDER in .env.

The env value is tried first. If that key is missing, the free-first order follows:
gemini → groq → openrouter → openai.
"""

from app.config import settings
from app.llm.providers.compat import OpenAICompatProvider
from app.llm.providers.gemini import build as gemini_build
from app.llm.providers.groq import build as groq_build
from app.llm.providers.openai import build as openai_build
from app.llm.providers.openrouter import build as openrouter_build

_BUILDERS = {
    "gemini": gemini_build,
    "groq": groq_build,
    "openrouter": openrouter_build,
    "openai": openai_build,
}

# Best free quota and quality first. OpenAI is paid, so it is last.
_FALLBACK_ORDER = ("gemini", "groq", "openrouter", "openai")


def provider_order(name: str | None = None) -> list[str]:
    """Env default first, then the remaining providers in free-first order."""
    requested = (name or settings.default_llm_provider or "gemini").strip().lower()
    if requested == "auto" or requested not in _BUILDERS:
        return list(_FALLBACK_ORDER)
    rest = [key for key in _FALLBACK_ORDER if key != requested]
    return [requested, *rest]


def iter_providers(name: str | None = None):
    """Enabled providers in try order. Skips vendors with an empty API key."""
    for key in provider_order(name):
        provider = _BUILDERS[key]()
        if provider.enabled:
            yield provider


def get_provider(name: str | None = None) -> OpenAICompatProvider | None:
    """Return the first enabled provider, or None if no API key is configured."""
    return next(iter_providers(name), None)


def llm_status() -> dict:
    """Shape used by GET /api/health."""
    provider = get_provider()
    return {
        "enabled": provider is not None,
        "provider": provider.name if provider else None,
        "model": provider.model if provider else None,
        "order": [item.name for item in iter_providers()],
        "available": {
            name: {"enabled": builder().enabled, "model": builder().model}
            for name, builder in _BUILDERS.items()
        },
    }
