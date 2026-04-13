"""评分模块测试"""

from __future__ import annotations

import pytest

from nautical_english.nlp.scorer import PhraseScorer, ScoreResult


@pytest.fixture
def scorer():
    return PhraseScorer(alpha=0.6, beta=0.4)


def test_perfect_match_scores_high(scorer):
    result = scorer.compute(
        recognized="alter course to starboard",
        reference="Alter course to starboard",
        similarity=0.99,
    )
    assert result.overall >= 90
    assert result.grade == "Excellent"


def test_wrong_direction_scores_lower(scorer):
    result = scorer.compute(
        recognized="alter course to port",
        reference="Alter course to starboard",
        similarity=0.65,
    )
    assert result.overall < 85


def test_completely_wrong_scores_poor(scorer):
    result = scorer.compute(
        recognized="hello world foo bar",
        reference="Mayday mayday mayday",
        similarity=0.05,
    )
    assert result.overall < 50


def test_score_in_valid_range(scorer):
    for sim in [0.0, 0.3, 0.6, 0.9, 1.0]:
        result = scorer.compute("some text", "some text", sim)
        assert 0.0 <= result.overall <= 100.0


def test_score_result_is_frozen(scorer):
    result = scorer.compute("a", "b", 0.5)
    assert isinstance(result, ScoreResult)
    with pytest.raises(Exception):
        result.overall = 50  # frozen dataclass should raise


def test_wer_capped_at_one(scorer):
    # 极端情况：识别完全错误
    result = scorer.compute("xyz xyz xyz", "Alter course to starboard", 0.0)
    assert result.wer <= 1.0
