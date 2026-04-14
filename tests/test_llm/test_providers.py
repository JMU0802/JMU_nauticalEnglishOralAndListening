"""Unit tests for LLM provider abstraction layer (no real HTTP calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nautical_english.llm.provider import LLMMessage, LLMResponse, LLMUsage
from nautical_english.llm.config import get_timeout, get_max_tokens


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_get_timeout_default(monkeypatch):
    monkeypatch.delenv("LLM_TIMEOUT", raising=False)
    assert get_timeout() == 30


def test_get_timeout_custom(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "60")
    assert get_timeout() == 60


def test_get_max_tokens_default(monkeypatch):
    monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
    assert get_max_tokens() == 512


# ---------------------------------------------------------------------------
# get_provider factory
# ---------------------------------------------------------------------------

def test_get_provider_deepseek(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    from nautical_english.llm import get_provider
    from nautical_english.llm.deepseek_provider import DeepSeekProvider

    provider = get_provider()
    assert isinstance(provider, DeepSeekProvider)
    assert provider.name == "deepseek"


def test_get_provider_kimi(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "kimi")
    from nautical_english.llm import get_provider
    from nautical_english.llm.kimi_provider import KimiProvider

    provider = get_provider()
    assert isinstance(provider, KimiProvider)
    assert provider.name == "kimi"


def test_get_provider_unknown_raises():
    from nautical_english.llm import get_provider

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("nonexistent_provider_xyz")


# ---------------------------------------------------------------------------
# DeepSeekProvider.chat via mock
# ---------------------------------------------------------------------------

def _make_mock_response(content: str):
    """Build a minimal mock that resembles openai.ChatCompletion."""
    msg = MagicMock()
    msg.content = content

    choice = MagicMock()
    choice.message = msg

    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def test_deepseek_provider_chat(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")

    from nautical_english.llm.deepseek_provider import DeepSeekProvider

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_response(
        "[REPLY]\nXiamen VTS, over.\n[JUDGE]\n回答良好。"
    )

    with patch("openai.OpenAI", return_value=mock_client):
        provider = DeepSeekProvider()
        messages: list[LLMMessage] = [
            {"role": "system", "content": "You are VTS."},
            {"role": "user", "content": "This is MV Test. Over."},
        ]
        result = provider.chat(messages)

    assert isinstance(result, LLMResponse)
    assert "Xiamen VTS" in result.content
    assert result.provider == "deepseek"
    assert result.usage.total_tokens == 30


def test_kimi_provider_chat(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "fake-kimi-key")

    from nautical_english.llm.kimi_provider import KimiProvider

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_response(
        "[REPLY]\nRoger, over.\n[JUDGE]\n用词正确。"
    )

    with patch("openai.OpenAI", return_value=mock_client):
        provider = KimiProvider()
        result = provider.chat([{"role": "user", "content": "Hello, over."}])

    assert "Roger" in result.content
    assert result.provider == "kimi"
