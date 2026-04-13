"""学生进度仪表板 — Phase 4 完整实现，当前为骨架"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProgressDashboard(QWidget):
    """全体学生成绩统计仪表板（中文 UI）。

    TODO Phase 4:
    - 班级整体平均分趋势图
    - 每个短语的班级正确率热力图
    - 学生个人成绩排行
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        label = QLabel("成绩看板\n（Phase 4 开发中）")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
