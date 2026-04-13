"""语料管理界面 — Phase 4 完整实现，当前为骨架"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CorpusManager(QWidget):
    """SMCP 语料库管理界面（中文 UI）。

    TODO Phase 4:
    - QTableView 展示所有短语（SQLAlchemy 数据绑定）
    - 添加/编辑/删除短语
    - 按类别/难度筛选
    - CSV 导入功能
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        label = QLabel("语料管理\n（Phase 4 开发中）")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
