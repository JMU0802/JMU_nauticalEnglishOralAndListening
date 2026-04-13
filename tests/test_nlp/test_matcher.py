"""NLP 匹配模块测试"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np


_PHRASES = [
    "Alter course to starboard",
    "Keep clear of me",
    "What are your intentions",
    "I am on fire and require assistance",
]


def _make_matcher(phrases=None):
    phrases = phrases or _PHRASES
    with patch("nautical_english.nlp.matcher.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        # 构造简单的伪嵌入（每个短语一个不同方向的单位向量）
        n = len(phrases)
        fake_embs = np.eye(n, dtype=np.float32)
        mock_model.encode.return_value = fake_embs
        MockST.return_value = mock_model

        from nautical_english.nlp.matcher import SentenceMatcher

        m = SentenceMatcher.__new__(SentenceMatcher)
        m._model = mock_model
        m._phrases = phrases
        m._embeddings = fake_embs
        return m


def test_find_best_match_returns_match_result():
    from nautical_english.nlp.matcher import MatchResult

    matcher = _make_matcher()
    # 伪嵌入让第一个短语向量完全匹配
    matcher._model.encode.return_value = np.array([[1, 0, 0, 0]], dtype=np.float32)
    result = matcher.find_best_match("alter course right")
    assert isinstance(result, MatchResult)
    assert isinstance(result.phrase, str)
    assert 0.0 <= result.score <= 1.0


def test_match_result_index_in_range():
    matcher = _make_matcher()
    matcher._model.encode.return_value = np.array([[0, 1, 0, 0]], dtype=np.float32)
    result = matcher.find_best_match("stay away from me")
    assert 0 <= result.index < len(_PHRASES)
