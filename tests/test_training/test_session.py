"""TrainingSession 集成测试 — 注入 Mock 依赖，不加载真实模型"""

from unittest.mock import MagicMock
from pathlib import Path

import numpy as np
import pytest

from nautical_english.training.session import TrainingSession, SessionResult


def _make_session(tmp_path: Path) -> TrainingSession:
    """创建注入 Mock 依赖的 TrainingSession。"""
    mock_asr = MagicMock()
    mock_asr.transcribe.return_value = "alter course to starboard"

    mock_matcher = MagicMock()
    mock_matcher.find_best_match.return_value = MagicMock(
        phrase="Alter course to starboard",
        score=0.95,
        index=0,
    )

    mock_scorer = MagicMock()
    mock_scorer.compute.return_value = MagicMock(
        wer=0.05, similarity=0.95, overall=87.0,
        grade="Good", feedback_en="Good attempt.",
    )

    mock_feedback_gen = MagicMock()
    mock_feedback_gen.generate.return_value = MagicMock(
        standard_phrase_en="Alter course to starboard",
        score_display="87.0 / 100",
        grade="Good",
        feedback_en="Good attempt.",
        diff_html="<span>Alter course to starboard</span>",
    )

    mock_tts = MagicMock()
    mock_tts.synthesize.return_value = tmp_path / "feedback.wav"

    mock_repo = MagicMock()
    mock_repo.save_training_record.return_value = 1

    return TrainingSession(
        recognizer=mock_asr,
        matcher=mock_matcher,
        scorer=mock_scorer,
        feedback_gen=mock_feedback_gen,
        synthesizer=mock_tts,
        repository=mock_repo,
        phrase_zh_map={"Alter course to starboard": "向右转向"},
    )


def test_session_run_returns_session_result(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    result = session.run(audio, student_id="stu001", output_dir=tmp_path)

    assert isinstance(result, SessionResult)
    assert result.recognized_text == "alter course to starboard"
    assert result.matched_phrase == "Alter course to starboard"
    assert result.overall_score == 87.0


def test_session_calls_all_components(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    session.run(audio, student_id="stu001", output_dir=tmp_path)

    session._asr.transcribe.assert_called_once()
    session._matcher.find_best_match.assert_called_once_with("alter course to starboard")
    session._scorer.compute.assert_called_once()
    session._feedback.generate.assert_called_once()
    session._tts.synthesize.assert_called_once()
    session._repo.save_training_record.assert_called_once()


def test_session_saves_training_record(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    session.run(audio, student_id="student_007", output_dir=tmp_path)

    call_kwargs = session._repo.save_training_record.call_args
    assert call_kwargs.kwargs["student_id"] == "student_007"
    assert call_kwargs.kwargs["overall_score"] == 87.0
