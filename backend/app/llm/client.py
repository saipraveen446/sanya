"""Call the active provider and parse a JSON object from the reply.

Returns None when no API key is set, the request fails, or the model
does not return valid JSON. Callers then use their own fallback parser.
"""

from app.llm.providers.factory import iter_providers


async def complete_json(
    system: str,
    user: str,
    *,
    provider_name: str | None = None,
) -> dict | None:
    """Send a system + user prompt and return the model's JSON dict.

    Tries DEFAULT_LLM_PROVIDER first, then the free-first fallback order.
    provider_name moves that vendor to the front for this call only.
    """
    for provider in iter_providers(provider_name):
        result = await provider.complete_json(system, user)
        if result is not None:
            return result
    return None
