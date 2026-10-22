"""Gemini, Groq, and OpenRouter all speak the OpenAI chat API.

One client class is enough; each vendor file only sets key, model, and base URL.
"""

import json
import re

from openai import AsyncOpenAI

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class OpenAICompatProvider:
    def __init__(
        self,
        name: str,
        api_key: str,
        model: str,
        base_url: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.extra_headers = extra_headers or {}

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _client(self) -> AsyncOpenAI:
        kwargs: dict = {"api_key": self.api_key, "base_url": self.base_url}
        if self.extra_headers:
            kwargs["default_headers"] = self.extra_headers
        return AsyncOpenAI(**kwargs)

    async def complete_json(self, system: str, user: str) -> dict | None:
        """Ask the model for JSON. Tries json_object mode, then a plain chat call."""
        if not self.enabled:
            return None
        client = self._client()
        content = await self._complete(client, system, user, use_json_mode=True)
        if content is None:
            content = await self._complete(client, system, user, use_json_mode=False)
        if not content:
            return None
        try:
            return json.loads(_FENCE_RE.sub("", content.strip()))
        except json.JSONDecodeError:
            return None

    async def _complete(
        self,
        client: AsyncOpenAI,
        system: str,
        user: str,
        *,
        use_json_mode: bool,
    ) -> str | None:
        kwargs: dict = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = await client.chat.completions.create(**kwargs)
        except Exception:
            return None
        return response.choices[0].message.content if response.choices else None
