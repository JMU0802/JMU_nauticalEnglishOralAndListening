"""LLM provider configuration — reads from environment variables or .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional .env loading (python-dotenv is optional)
# ---------------------------------------------------------------------------
_ENV_LOADED = False


def _load_dotenv_once() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped]

        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
    except ImportError:
        pass  # python-dotenv not installed — rely on real env vars


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

SUPPORTED_PROVIDERS = ("deepseek", "kimi", "zai", "openai")


def get_provider_name() -> str:
    """Return the active LLM provider name (lowercase).

    Priority: ``LLM_PROVIDER`` env-var → first key found → "deepseek".
    """
    _load_dotenv_once()
    name = os.getenv("LLM_PROVIDER", "").strip().lower()
    if name in SUPPORTED_PROVIDERS:
        return name
    # auto-detect from which key is present
    if os.getenv("ZAI_API_KEY"):
        return "zai"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("KIMI_API_KEY"):
        return "kimi"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "deepseek"


def get_api_key(provider: Optional[str] = None) -> str:
    """Return the API key for *provider* (default: active provider)."""
    _load_dotenv_once()
    p = provider or get_provider_name()
    mapping = {
        "deepseek": "DEEPSEEK_API_KEY",
        "kimi": "KIMI_API_KEY",
        "zai": "ZAI_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    key = os.getenv(mapping.get(p, "DEEPSEEK_API_KEY"), "")
    return key


def get_timeout() -> int:
    """Request timeout in seconds (default 30)."""
    _load_dotenv_once()
    try:
        return int(os.getenv("LLM_TIMEOUT", "30"))
    except ValueError:
        return 30


def get_max_tokens() -> int:
    """Maximum tokens in a single LLM response (default 200).

    SMCP replies are short: [REPLY] ≤60 words + [JUDGE] ≤3 sentences ≈ 150 tokens.
    200 gives comfortable headroom while halving latency vs the old 512 default.
    Override via LLM_MAX_TOKENS env-var if needed.
    """
    _load_dotenv_once()
    try:
        return int(os.getenv("LLM_MAX_TOKENS", "200"))
    except ValueError:
        return 200
