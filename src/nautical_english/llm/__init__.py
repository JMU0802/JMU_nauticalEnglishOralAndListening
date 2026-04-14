"""llm package — LLM provider abstraction layer.

Factory usage::

    from nautical_english.llm import get_provider
    provider = get_provider()          # reads LLM_PROVIDER env var
    resp = provider.chat(messages)
"""

from __future__ import annotations

from nautical_english.llm.provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMUsage


def get_provider(name: str | None = None) -> BaseLLMProvider:
    """Return a provider instance for *name* (or the configured default).

    Parameters
    ----------
    name:
        One of ``"deepseek"``, ``"kimi"``, ``"openai"``.  When *None* the
        value of the ``LLM_PROVIDER`` environment variable is used.

    Raises
    ------
    ValueError
        If *name* is unrecognised.
    """
    from nautical_english.llm.config import get_provider_name

    provider_name = (name or get_provider_name()).lower().strip()

    if provider_name == "deepseek":
        from nautical_english.llm.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider()

    if provider_name == "zai":
        from nautical_english.llm.zai_provider import ZaiProvider

        return ZaiProvider()

    if provider_name == "kimi":
        from nautical_english.llm.kimi_provider import KimiProvider

        return KimiProvider()

    if provider_name == "openai":
        # Fallback: plain OpenAI with default base URL
        from nautical_english.llm.deepseek_provider import DeepSeekProvider  # same client structure

        class _OpenAIProvider(DeepSeekProvider):
            BASE_URL = "https://api.openai.com/v1"
            DEFAULT_MODEL = "gpt-4o-mini"

            @property
            def name(self) -> str:
                return "openai"

        return _OpenAIProvider()

    raise ValueError(
        f"Unknown LLM provider: {provider_name!r}. "
        f"Choose from: deepseek, kimi, zai, openai"
    )


__all__ = [
    "get_provider",
    "BaseLLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMUsage",
]
