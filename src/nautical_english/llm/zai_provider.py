"""Z.ai (ZhipuAI / 智谱AI) provider — OpenAI-compatible API.

Base URL: https://open.bigmodel.cn/api/paas/v4/
Default model: glm-4-plus  (最强通用模型，支持流式输出)
"""

from __future__ import annotations

from typing import Iterator

from nautical_english.llm.provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMUsage


class ZaiProvider(BaseLLMProvider):
    """Connects to ZhipuAI (z.ai) via the OpenAI-compatible interface."""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    DEFAULT_MODEL = "glm-4-plus"   # 最强通用模型

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self._model = model

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "zai"

    @property
    def model(self) -> str:
        return self._model

    def _make_client(self):
        try:
            from openai import OpenAI  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "openai package is required for ZaiProvider. "
                "Install it with: pip install openai"
            ) from exc

        from nautical_english.llm.config import get_api_key, get_timeout

        return OpenAI(
            api_key=get_api_key("zai"),
            base_url=self.BASE_URL,
            timeout=get_timeout(),
        )

    def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> LLMResponse:
        client = self._make_client()
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

    def stream_chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Real SSE streaming — yields text chunks as they arrive from the server."""
        client = self._make_client()
        with client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
