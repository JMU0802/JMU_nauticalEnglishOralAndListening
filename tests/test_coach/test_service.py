"""Unit tests for CoachService state machine (no real LLM calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nautical_english.coach.service import CoachService, CoachState, TurnResult
from nautical_english.llm.provider import LLMResponse, LLMUsage
from nautical_english.scenario.models import Scenario


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_scenario() -> Scenario:
    s = Scenario(
        id=1,
        name_en="Test Scenario",
        name_zh="测试场景",
        category="Navigation",
        difficulty=1,
        description_en="desc en",
        description_zh="desc zh",
        system_role_en="You are VTS.",
        opening_line_en="State your vessel. Over.",
        max_turns=4,
    )
    return s


def _make_repo(scenario):
    repo = MagicMock()
    repo.get_scenario.return_value = scenario
    repo.new_session_id.return_value = "test-uuid-1234"
    repo.save_turn.return_value = 1
    return repo


def _make_provider(reply_content: str):
    provider = MagicMock()
    provider.chat.return_value = LLMResponse(
        content=reply_content,
        usage=LLMUsage(10, 20, 30),
        provider="mock",
        model="mock-model",
    )
    return provider


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_initial_state():
    repo = _make_repo(_make_scenario())
    provider = _make_provider("[REPLY]\nRoger. Over.\n[JUDGE]\n良好。")
    svc = CoachService(repo, provider)
    assert svc.state == CoachState.IDLE


def test_start_session_returns_opening():
    scenario = _make_scenario()
    repo = _make_repo(scenario)
    provider = _make_provider("[REPLY]\nRoger. Over.\n[JUDGE]\n良好。")
    svc = CoachService(repo, provider)

    opening = svc.start_session(scenario_id=1, student_id="s001")
    assert opening == scenario.opening_line_en
    assert svc.state == CoachState.READY
    assert svc.session_id == "test-uuid-1234"


def test_start_session_unknown_scenario_raises():
    repo = MagicMock()
    repo.get_scenario.return_value = None
    provider = _make_provider("")
    svc = CoachService(repo, provider)

    with pytest.raises(ValueError, match="not found"):
        svc.start_session(scenario_id=999, student_id="s001")


def test_score_heuristic_with_keywords():
    scenario = _make_scenario()
    repo = _make_repo(scenario)
    provider = _make_provider("[REPLY]\nTest. Over.\n[JUDGE]\n分析。")
    svc = CoachService(repo, provider)
    svc.start_session(1, "s001")

    # "over" + "roger" + "wilco" = 3 keywords → 50 + 30 = 80
    score = svc._score_student_turn("Xiamen VTS, roger wilco, over.")
    assert score == 80.0


def test_score_heuristic_no_keywords():
    scenario = _make_scenario()
    repo = _make_repo(scenario)
    provider = _make_provider("[REPLY]\nTest.\n[JUDGE]\n分析。")
    svc = CoachService(repo, provider)
    svc.start_session(1, "s001")

    score = svc._score_student_turn("Hello world no keywords here")
    assert score == 50.0


def test_student_speak_triggers_llm(monkeypatch):
    """student_speak should kick off _llm_call in a thread."""
    scenario = _make_scenario()
    repo = _make_repo(scenario)
    provider = _make_provider("[REPLY]\nXiamen VTS, roger. Over.\n[JUDGE]\n良好。")

    results: list[TurnResult] = []
    svc = CoachService(repo, provider, on_turn_complete=results.append)
    svc.start_session(1, "s001")

    # Call _llm_call synchronously for testing
    svc._llm_call("MV Test, over.", student_turn_idx=1)

    assert len(results) == 1
    assert "roger" in results[0].llm_reply.lower()
    assert "良好" in results[0].judgement
