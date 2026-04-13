"""进度视图 — Phase 4 完整实现，当前为骨架"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProgressView(QWidget):
    """展示学生历史练习进度（英文 UI）。

    TODO Phase 4:
    - 近 10 次评分折线图（QPainter 自绘）
    - 按类别练习次数/正确率柱状图
    - 总练习次数/平均分统计
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        label = QLabel("Progress View\n(Phase 4 implementation pending)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
