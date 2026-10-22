"""Shared LLM access. Skills call complete_json(); they never import a vendor SDK."""

from app.llm.client import complete_json
from app.llm.providers.factory import get_provider, iter_providers, llm_status

__all__ = ["complete_json", "get_provider", "iter_providers", "llm_status"]
