"""反馈生成模块 — 将评分结果转化为结构化反馈对象"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from nautical_english.nlp.scorer import ScoreResult


@dataclass
class FeedbackResult:
    """一次练习的完整反馈。"""

    recognized_text: str        # 学员 ASR 文本
    standard_phrase_en: str     # 标准英文短语
    standard_phrase_zh: str     # 中文释义
    score_display: str          # 如 "87.5 / 100"
    grade: str                  # Excellent / Good / Fair / Poor
    feedback_en: str            # 英文反馈句
    error_words: list[str] = field(default_factory=list)    # 错误词列表
    diff_html: str = ""         # HTML 格式差异高亮（用于 QTextEdit）


class FeedbackGenerator:
    """根据识别文本、标准短语、评分结果生成结构化反馈。"""

    def generate(
        self,
        recognized: str,
        reference: str,
        score: ScoreResult,
        reference_zh: str,
    ) -> FeedbackResult:
        error_words = self._find_error_words(recognized, reference)
        diff_html = self._build_diff_html(recognized, reference)

        return FeedbackResult(
            recognized_text=recognized,
            standard_phrase_en=reference,
            standard_phrase_zh=reference_zh,
            score_display=f"{score.overall} / 100",
            grade=score.grade,
            feedback_en=score.feedback_en,
            error_words=error_words,
            diff_html=diff_html,
        )

    # ── 私有辅助方法 ─────────────────────────────────────────────

    @staticmethod
    def _find_error_words(recognized: str, reference: str) -> list[str]:
        """找出学员文本中与标准句不同的词。"""
        ref_words = reference.lower().split()
        rec_words = recognized.lower().split()
        matcher = difflib.SequenceMatcher(None, ref_words, rec_words)
        errors: list[str] = []
        for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
            if tag in ("replace", "insert"):
                errors.extend(rec_words[j1:j2])
        return errors

    @staticmethod
    def _build_diff_html(recognized: str, reference: str) -> str:
        """生成 HTML 差异高亮：红色=错误，绿色=标准。"""
        ref_words = reference.split()
        rec_words = recognized.split()
        matcher = difflib.SequenceMatcher(None,
                                          [w.lower() for w in ref_words],
                                          [w.lower() for w in rec_words])
        parts: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                parts.append(" ".join(ref_words[i1:i2]))
            elif tag == "replace":
                parts.append(
                    f'<span style="color:#E74C3C">'
                    f'{" ".join(rec_words[j1:j2])}</span>'
                    f' <span style="color:#2ECC71">'
                    f'({" ".join(ref_words[i1:i2])})</span>'
                )
            elif tag == "delete":
                parts.append(
                    f'<span style="color:#2ECC71">'
                    f'[{" ".join(ref_words[i1:i2])}]</span>'
                )
            elif tag == "insert":
                parts.append(
                    f'<span style="color:#E74C3C">'
                    f'{" ".join(rec_words[j1:j2])}</span>'
                )
        return " ".join(parts)
