"""主窗口 — 包含学生端/管理端两个标签页"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """应用主窗口。

    采用 QTabWidget 组织学生端（英文）和管理端（中文）。
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Maritime English Trainer — JMU 集美大学")
        self.setMinimumSize(1100, 750)
        self._load_stylesheet()
        self._setup_ui()

    # ── UI 搭建 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_student_placeholder(), "Practice（练习）")
        self._tabs.addTab(self._build_admin_placeholder(), "管理后台")
        layout.addWidget(self._tabs)

    def _build_student_placeholder(self) -> QWidget:
        """学生端占位视图 — Phase 4 替换为 PracticeView。"""
        w = QWidget()
        v = QVBoxLayout(w)
        label = QLabel("Student Practice View\n(Phase 4 implementation pending)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(label)
        return w

    def _build_admin_placeholder(self) -> QWidget:
        """管理端占位视图 — Phase 4 替换为 CorpusManager。"""
        w = QWidget()
        v = QVBoxLayout(w)
        label = QLabel("管理后台\n（Phase 4 开发中）")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(label)
        return w

    # ── 样式加载 ─────────────────────────────────────────────────

    def _load_stylesheet(self) -> None:
        qss_path = (
            Path(__file__).parent / "resources" / "styles.qss"
        )
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
