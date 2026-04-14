"""计分卡组件 — 展示评分、等级与关键指标"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout


class ScoreCard(QFrame):
    """可复用评分展示控件。

    显示大号分数、等级标签（Excellent / Good / Fair / Needs Work）  
    以及 WER、相似度两个关键指标。

    Usage::

        card = ScoreCard()
        card.set_score(87.5, "Good", wer=0.12, similarity=0.94)
    """

    _GRADE_COLORS = {
        "Excellent": "#2ECC71",
        "Good":      "#3498DB",
        "Fair":      "#F39C12",
        "Needs Work":"#E74C3C",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("scoreCard")
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(4)
        outer.setContentsMargins(16, 16, 16, 16)

        self._score_label = QLabel("--")
        self._score_label.setObjectName("scoreLabel")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._grade_label = QLabel("--")
        self._grade_label.setObjectName("gradeLabel")
        self._grade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats_row = QGridLayout()
        stats_row.setColumnStretch(0, 1)
        stats_row.setColumnStretch(1, 1)

        self._wer_label = QLabel("WER: --")
        self._wer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sim_label = QLabel("Similarity: --")
        self._sim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats_row.addWidget(self._wer_label, 0, 0)
        stats_row.addWidget(self._sim_label, 0, 1)

        outer.addWidget(self._score_label)
        outer.addWidget(self._grade_label)
        outer.addLayout(stats_row)

    def set_score(
        self,
        score: float,
        grade: str,
        *,
        wer: float | None = None,
        similarity: float | None = None,
    ) -> None:
        """更新计分卡显示。

        Parameters
        ----------
        score:       总体评分 0-100
        grade:       等级字符串 ("Excellent" / "Good" / "Fair" / "Needs Work")
        wer:         词错误率（可选）
        similarity:  短语语义相似度（可选）
        """
        self._score_label.setText(f"{score:.1f}")

        grade_color = self._GRADE_COLORS.get(grade, "#ECF0F1")
        self._grade_label.setText(grade)
        self._grade_label.setStyleSheet(
            f"color: {grade_color}; font-size: 20px; font-weight: bold;"
        )

        if wer is not None:
            self._wer_label.setText(f"WER: {wer:.1%}")
        if similarity is not None:
            self._sim_label.setText(f"Similarity: {similarity:.1%}")

    def reset(self) -> None:
        """清空显示。"""
        self._score_label.setText("--")
        self._grade_label.setText("--")
        self._grade_label.setStyleSheet("")
        self._wer_label.setText("WER: --")
        self._sim_label.setText("Similarity: --")
