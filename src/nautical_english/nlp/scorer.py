"""发音评分模块 — WER + 语义相似度双指标融合"""

from __future__ import annotations

from dataclasses import dataclass

import jiwer

# ── 评分等级映射（阈值降序）──────────────────────────────────────
_GRADE_MAP: list[tuple[float, str, str]] = [
    (90.0, "Excellent", "Perfect! Standard pronunciation."),
    (70.0, "Good", "Good attempt. Minor errors detected."),
    (50.0, "Fair", "Partially correct. Keep practicing."),
    (0.0, "Poor", "Incorrect. Please try again."),
]


@dataclass(frozen=True)
class ScoreResult:
    """综合评分结果。"""

    wer: float             # 词错误率 ∈ [0, 1]（越低越好）
    similarity: float      # 语义相似度 ∈ [0, 1]
    overall: float         # 综合分数 ∈ [0, 100]
    grade: str             # 等级字符串
    feedback_en: str       # 英文反馈文本


class PhraseScorer:
    """计算学员朗读与标准短语的综合得分。

    综合得分公式：
        overall = 100 × (α × similarity + β × (1 - WER))

    Parameters
    ----------
    alpha:
        语义相似度权重（默认 0.6）。
    beta:
        WER 准确度权重（默认 0.4）。
    """

    def __init__(self, alpha: float = 0.6, beta: float = 0.4) -> None:
        self.alpha = alpha
        self.beta = beta

    def compute(
        self, recognized: str, reference: str, similarity: float
    ) -> ScoreResult:
        """计算综合评分。

        Parameters
        ----------
        recognized:
            ASR 识别出的学员文本。
        reference:
            标准 SMCP 短语。
        similarity:
            来自 :class:`SentenceMatcher` 的余弦相似度。
        """
        wer = min(jiwer.wer(reference.lower(), recognized.lower()), 1.0)
        raw = self.alpha * similarity + self.beta * (1.0 - wer)
        overall = round(max(0.0, min(100.0, raw * 100)), 1)

        grade, feedback_en = next(
            (g, f)
            for threshold, g, f in _GRADE_MAP
            if overall >= threshold
        )

        return ScoreResult(
            wer=wer,
            similarity=similarity,
            overall=overall,
            grade=grade,
            feedback_en=feedback_en,
        )
