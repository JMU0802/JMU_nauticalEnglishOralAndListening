"""Abstract base class and shared types for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, TypedDict


# ---------------------------------------------------------------------------
# Shared message / response types
# ---------------------------------------------------------------------------

class LLMMessage(TypedDict):
    """A single chat message (OpenAI-compatible format)."""

    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    provider: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Common interface for all LLM back-ends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier, e.g. ``"deepseek"``."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model string passed to the API."""

    @abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send *messages* to the LLM and return the reply."""

    def stream_chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Stream response tokens one by one.

        Default implementation calls :meth:`chat` and yields the full
        response at once.  Override for real server-sent-event streaming.
        """
        yield self.chat(messages, max_tokens=max_tokens, temperature=temperature).content

    def is_available(self) -> bool:
        """Return True if the provider has a non-empty API key."""
        from nautical_english.llm.config import get_api_key

        return bool(get_api_key(self.name))
