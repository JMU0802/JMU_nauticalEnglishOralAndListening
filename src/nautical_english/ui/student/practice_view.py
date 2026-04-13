"""练习视图 — Phase 4 完整实现，当前为骨架"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class PracticeView(QWidget):
    """学生端主练习界面（英文 UI）。

    TODO Phase 4:
    - 显示当前 SMCP 短语和中文释义
    - 录音按钮（按住录音）
    - 音频波形可视化
    - 提交按钮
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._phrase_label = QLabel("Alter course to starboard.")
        self._phrase_label.setObjectName("phraseLabel")
        self._phrase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._phrase_zh_label = QLabel("向右转向。")
        self._phrase_zh_label.setObjectName("phraseLabelZh")
        self._phrase_zh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_btn = QPushButton("🎙 HOLD TO SPEAK")
        self._record_btn.setObjectName("recordBtn")
        self._record_btn.setFixedSize(160, 80)

        self._submit_btn = QPushButton("Submit")

        layout.addStretch()
        layout.addWidget(self._phrase_label)
        layout.addWidget(self._phrase_zh_label)
        layout.addSpacing(30)
        layout.addWidget(self._record_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(20)
        layout.addWidget(self._submit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
