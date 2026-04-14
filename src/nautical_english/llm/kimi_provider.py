"""Kimi (Moonshot AI) provider — OpenAI-compatible API."""

from __future__ import annotations

from nautical_english.llm.provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMUsage


class KimiProvider(BaseLLMProvider):
    """Connects to ``https://api.moonshot.cn/v1`` via the openai SDK."""

    BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self._model = model

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "kimi"

    @property
    def model(self) -> str:
        return self._model

    def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> LLMResponse:
        try:
            from openai import OpenAI  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "openai package is required for KimiProvider. "
                "Install it with: pip install openai"
            ) from exc

        from nautical_english.llm.config import get_api_key, get_timeout

        client = OpenAI(
            api_key=get_api_key("kimi"),
            base_url=self.BASE_URL,
            timeout=get_timeout(),
        )
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = resp.choices[0].message.content or ""
        usage = LLMUsage(
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            total_tokens=resp.usage.total_tokens if resp.usage else 0,
        )
        return LLMResponse(content=content, usage=usage, provider=self.name, model=self._model)
