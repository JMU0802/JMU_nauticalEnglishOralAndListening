"""Unit tests for ScenarioRepository and seed data."""

from __future__ import annotations

import pytest

from nautical_english.scenario.repository import ScenarioRepository


# ---------------------------------------------------------------------------
# Fixtures — use in-memory SQLite
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo() -> ScenarioRepository:
    r = ScenarioRepository(db_url="sqlite:///:memory:")
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_repo(repo):
    assert repo.get_all_scenarios() == []


def test_seed_if_empty_populates(repo):
    repo.seed_if_empty()
    scenarios = repo.get_all_scenarios()
    assert len(scenarios) == 10


def test_seed_if_empty_idempotent(repo):
    repo.seed_if_empty()
    repo.seed_if_empty()
    assert len(repo.get_all_scenarios()) == 10


def test_get_scenario_by_id(repo):
    repo.seed_if_empty()
    scenarios = repo.get_all_scenarios()
    first = scenarios[0]
    fetched = repo.get_scenario(first.id)
    assert fetched is not None
    assert fetched.name_en == first.name_en


def test_get_scenarios_by_category(repo):
    repo.seed_if_empty()
    nav_scenarios = repo.get_scenarios_by_category("Navigation")
    assert all(s.category == "Navigation" for s in nav_scenarios)
    assert len(nav_scenarios) > 0


def test_get_categories(repo):
    repo.seed_if_empty()
    cats = repo.get_categories()
    assert "Navigation" in cats
    assert "Distress" in cats
    assert "Emergency" in cats


def test_add_scenario(repo):
    sid = repo.add_scenario(
        name_en="Test Scenario",
        name_zh="测试",
        category="Navigation",
        difficulty=1,
        description_en="desc en",
        description_zh="desc zh",
        system_role_en="You are VTS.",
        opening_line_en="State your name. Over.",
        max_turns=6,
    )
    assert sid > 0
    s = repo.get_scenario(sid)
    assert s is not None
    assert s.name_en == "Test Scenario"


def test_update_scenario(repo):
    repo.seed_if_empty()
    s = repo.get_all_scenarios()[0]
    ok = repo.update_scenario(s.id, difficulty=3)
    assert ok
    updated = repo.get_scenario(s.id)
    assert updated.difficulty == 3


def test_delete_scenario(repo):
    repo.seed_if_empty()
    s = repo.get_all_scenarios()[0]
    ok = repo.delete_scenario(s.id)
    assert ok
    assert repo.get_scenario(s.id) is None


def test_new_session_id_unique(repo):
    ids = {repo.new_session_id() for _ in range(10)}
    assert len(ids) == 10  # all unique UUIDs


def test_save_turn_and_retrieve(repo):
    repo.seed_if_empty()
    scenario_id = repo.get_all_scenarios()[0].id
    session_id = repo.new_session_id()

    repo.save_turn(
        session_id=session_id,
        student_id="s001",
        scenario_id=scenario_id,
        turn_index=0,
        role="coach",
        content="State your vessel. Over.",
    )
    repo.save_turn(
        session_id=session_id,
        student_id="s001",
        scenario_id=scenario_id,
        turn_index=1,
        role="student",
        content="MV Test. Over.",
        llm_judgement="良好",
        score=70.0,
    )

    turns = repo.get_session_turns(session_id)
    assert len(turns) == 2
    assert turns[0].role == "coach"
    assert turns[1].score == 70.0


def test_get_student_sessions(repo):
    repo.seed_if_empty()
    scenario_id = repo.get_all_scenarios()[0].id

    session_a = repo.new_session_id()
    session_b = repo.new_session_id()

    for sid in (session_a, session_b):
        repo.save_turn(
            session_id=sid,
            student_id="s002",
            scenario_id=scenario_id,
            turn_index=0,
            role="student",
            content="Hello. Over.",
        )

    sessions = repo.get_student_sessions("s002")
    assert set(sessions) == {session_a, session_b}
