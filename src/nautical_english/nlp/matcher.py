"""句子语义匹配模块 — 基于 Sentence-BERT 的余弦相似度匹配"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MatchResult:
    """匹配结果。"""

    phrase: str           # 最佳匹配短语
    score: float          # 余弦相似度 ∈ [0, 1]
    index: int            # 在候选列表中的下标


_DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class SentenceMatcher:
    """将学员语音文本与 SMCP 标准短语库进行语义相似度匹配。

    Parameters
    ----------
    phrases:
        标准短语列表（来自数据库）。
    model_name:
        sentence-transformers 模型名称。
    """

    def __init__(
        self,
        phrases: list[str],
        model_name: str = _DEFAULT_MODEL,
    ) -> None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        self._model = SentenceTransformer(model_name)
        self._phrases = phrases
        # 预计算语料库向量（normalize 后可直接用点积代替余弦）
        self._embeddings: np.ndarray = self._model.encode(
            phrases, normalize_embeddings=True, show_progress_bar=False
        )

    def find_best_match(self, query: str) -> MatchResult:
        """在候选短语中找到与 ``query`` 最接近的标准句。"""
        q_emb = self._model.encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )
        scores = (self._embeddings @ q_emb.T).flatten()
        idx = int(np.argmax(scores))
        return MatchResult(
            phrase=self._phrases[idx],
            score=float(scores[idx]),
            index=idx,
        )

    def update_phrases(self, phrases: list[str]) -> None:
        """更新候选短语库并重新编码（语料变更时调用）。"""
        self._phrases = phrases
        self._embeddings = self._model.encode(
            phrases, normalize_embeddings=True, show_progress_bar=False
        )
