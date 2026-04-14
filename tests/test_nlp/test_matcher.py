"""NLP 匹配模块测试"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np


_PHRASES = [
    "Alter course to starboard",
    "Keep clear of me",
    "What are your intentions",
    "I am on fire and require assistance",
]


def _make_matcher(phrases=None):
    phrases = phrases or _PHRASES
    from nautical_english.nlp.matcher import SentenceMatcher

    mock_model = MagicMock()
    # 构造简单的伪嵌入（每个短语一个不同方向的单位向量）
    n = len(phrases)
    fake_embs = np.eye(n, dtype=np.float32)
    mock_model.encode.return_value = fake_embs

    m = SentenceMatcher.__new__(SentenceMatcher)
    m._model = mock_model
    m._phrases = phrases
    m._embeddings = fake_embs
    m._cache = {}
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


def test_find_best_match_uses_cache_for_same_query():
    matcher = _make_matcher()
    matcher._model.encode.return_value = np.array([[1, 0, 0, 0]], dtype=np.float32)

    first = matcher.find_best_match("Alter course right")
    second = matcher.find_best_match(" alter course right ")

    assert first is second
    # 1 次用于 query 编码，后续命中缓存不再编码 query。
    assert matcher._model.encode.call_count == 1
