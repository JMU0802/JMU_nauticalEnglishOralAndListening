"""反馈生成模块测试"""

from __future__ import annotations

import pytest

from nautical_english.feedback.generator import FeedbackGenerator
from nautical_english.nlp.scorer import ScoreResult


@pytest.fixture
def gen():
    return FeedbackGenerator()


def _make_score(overall: float, grade: str, feedback: str) -> ScoreResult:
    wer = max(0.0, 1.0 - overall / 100)
    return ScoreResult(
        wer=wer,
        similarity=overall / 100,
        overall=overall,
        grade=grade,
        feedback_en=feedback,
    )


def test_feedback_contains_standard_phrase(gen):
    score = _make_score(75.0, "Good", "Good attempt.")
    fb = gen.generate(
        recognized="alter course port",
        reference="Alter course to starboard",
        score=score,
        reference_zh="向右转向",
    )
    assert fb.standard_phrase_en == "Alter course to starboard"
    assert fb.standard_phrase_zh == "向右转向"


def test_score_display_format(gen):
    score = _make_score(87.5, "Good", "Good attempt.")
    fb = gen.generate("alter course starboard", "Alter course to starboard",
                      score, "向右转向")
    assert "87.5" in fb.score_display
    assert "100" in fb.score_display


def test_feedback_grade_matches(gen):
    score = _make_score(92.0, "Excellent", "Perfect!")
    fb = gen.generate("alter course to starboard",
                      "Alter course to starboard", score, "向右转向")
    assert fb.grade == "Excellent"


def test_diff_html_not_empty_on_error(gen):
    score = _make_score(40.0, "Poor", "Incorrect.")
    fb = gen.generate("random wrong words",
                      "Keep clear of me", score, "请避让")
    assert len(fb.diff_html) > 0


def test_error_words_not_empty_on_mismatch(gen):
    score = _make_score(50.0, "Fair", "Partially correct.")
    fb = gen.generate("alter course to port",
                      "Alter course to starboard", score, "向右转向")
    assert len(fb.error_words) > 0
