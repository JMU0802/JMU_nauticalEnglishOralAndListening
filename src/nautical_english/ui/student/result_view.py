"""结果视图 — Phase 4 完整实现，当前为骨架"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ResultView(QWidget):
    """展示单次练习评分结果（英文 UI）。

    TODO Phase 4:
    - 综合评分大字
    - 等级/反馈文本
    - 识别文本 vs 标准文本差异高亮
    - 错误词列表
    - "再练一次" / "下一题" 按钮
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._score_label = QLabel("--")
        self._score_label.setObjectName("scoreLabel")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._grade_label = QLabel("--")
        self._grade_label.setObjectName("gradeLabel")
        self._grade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._feedback_label = QLabel("Submit your recording to see feedback.")
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setWordWrap(True)

        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setPlaceholderText("Diff will appear here...")
        self._diff_view.setMaximumHeight(120)

        btn_layout = QHBoxLayout()
        self._retry_btn = QPushButton("Try Again")
        self._next_btn = QPushButton("Next Phrase →")
        btn_layout.addWidget(self._retry_btn)
        btn_layout.addWidget(self._next_btn)

        layout.addStretch()
        layout.addWidget(self._score_label)
        layout.addWidget(self._grade_label)
        layout.addWidget(self._feedback_label)
        layout.addWidget(self._diff_view)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def update_result(
        self,
        score: float,
        grade: str,
        feedback_en: str,
        diff_html: str,
    ) -> None:
        """用训练结果更新界面。"""
        self._score_label.setText(f"{score:.1f}")
        self._grade_label.setText(grade)
        self._feedback_label.setText(feedback_en)
        self._diff_view.setHtml(diff_html)
