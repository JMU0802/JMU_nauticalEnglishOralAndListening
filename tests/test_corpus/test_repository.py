"""语料库模块测试"""

from __future__ import annotations

import pytest

from nautical_english.corpus.repository import CorpusRepository


@pytest.fixture
def repo():
    return CorpusRepository(db_url="sqlite:///:memory:", seed=True)


def test_get_all_phrases_returns_list(repo):
    phrases = repo.get_all_phrases()
    assert isinstance(phrases, list)
    assert len(phrases) > 0


def test_get_phrases_by_difficulty(repo):
    easy = repo.get_phrases_by_difficulty(1)
    assert all(p.difficulty == 1 for p in easy)


def test_get_all_categories(repo):
    cats = repo.get_all_categories()
    assert len(cats) > 0
    assert cats[0].name_en == "Navigation"


def test_save_training_record(repo):
    phrases = repo.get_all_phrases()
    record_id = repo.save_training_record(
        student_id="test_student_001",
        phrase_id=phrases[0].id,
        recognized_text="alter course to starboard",
        wer_score=0.1,
        similarity_score=0.95,
        overall_score=87.0,
    )
    assert isinstance(record_id, int)
    assert record_id > 0


def test_get_student_records(repo):
    phrases = repo.get_all_phrases()
    repo.save_training_record("s001", phrases[0].id, "text", 0.2, 0.8, 72.0)
    repo.save_training_record("s001", phrases[0].id, "text2", 0.1, 0.9, 85.0)
    records = repo.get_student_records("s001")
    assert len(records) == 2


def test_add_and_delete_phrase(repo):
    cats = repo.get_all_categories()
    initial_count = len(repo.get_all_phrases())
    pid = repo.add_phrase(
        category_id=cats[0].id,
        phrase_en="Test phrase",
        phrase_zh="测试短语",
        difficulty=1,
    )
    assert len(repo.get_all_phrases()) == initial_count + 1
    repo.delete_phrase(pid)
    assert len(repo.get_all_phrases()) == initial_count
