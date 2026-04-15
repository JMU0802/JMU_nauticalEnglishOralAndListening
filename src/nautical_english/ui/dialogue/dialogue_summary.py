"""DialogueSummaryView — shows a post-session summary and score breakdown.

Displays all turns in a formatted table, overall score, and SMCP feedback.
Emits ``restart_requested`` to go back to scenario selection or ``retry_requested``
to replay the same scenario.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from nautical_english.coach.service import CoachService
from nautical_english.scenario.models import DialogueTurn
from nautical_english.scenario.repository import ScenarioRepository


class DialogueSummaryView(QWidget):
    """Post-session summary screen."""

    restart_requested = pyqtSignal()   # back to scenario selector
    retry_requested = pyqtSignal(int)  # replay same scenario_id

    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = scenario_repo
        self._build_ui()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_session(
        self,
        session_id: str,
        coach: "CoachService | None" = None,
    ) -> None:
        """Populate the view with results for *session_id*."""
        turns = self._repo.get_session_turns(session_id)
        if not turns:
            return

        scenario_id = turns[0].scenario_id
        scenario = self._repo.get_scenario(scenario_id)
        scenario_name = scenario.name_en if scenario else "—"

        self._scenario_lbl.setText(f"场景: {scenario_name}")

        # Overall score = average of coach-assessed turns
        scored = [t for t in turns if t.score is not None]
        avg_score = sum(t.score for t in scored) / len(scored) if scored else 0.0
        self._score_lbl.setText(f"综合得分: {avg_score:.0f} / 100")
        grade = self._grade(avg_score)
        self._grade_lbl.setText(f"等级: {grade}")

        # Populate table
        student_turns = [t for t in turns if t.role == "student"]
        coach_turns = {t.turn_index - 1: t for t in turns if t.role == "coach"}

        self._table.setRowCount(0)
        for st in student_turns:
            coach = coach_turns.get(st.turn_index + 1, None)
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._set_cell(row, 0, st.content)
            self._set_cell(row, 1, coach.llm_reply if coach else "")
            self._set_cell(row, 2, coach.llm_judgement if coach else "")
            score_val = coach.score if coach and coach.score is not None else 0.0
            self._set_cell(row, 3, f"{score_val:.0f}")

        self._table.resizeRowsToContents()
        self._retry_scenario_id = scenario_id

        # Trigger AI evaluation if coach service provided
        self._eval_text.setPlainText("⌛ AI 正在生成综合评估，请稍候…")
        if coach is not None:
            coach.evaluate_session(
                on_complete=lambda text: QTimer.singleShot(
                    0, lambda: self._set_evaluation(text)
                ),
                on_error=lambda msg: QTimer.singleShot(
                    0, lambda: self._set_evaluation(f"⚠️ 评估生成失败：{msg}")
                ),
            )
        else:
            self._eval_text.setPlainText("（无法生成评估：教练服务不可用）")

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Header
        title = QLabel("对话总结")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Scenario + score row
        info_row = QHBoxLayout()
        self._scenario_lbl = QLabel("")
        self._scenario_lbl.setObjectName("cardSubtitle")
        self._score_lbl = QLabel("")
        self._score_lbl.setObjectName("statsValue")
        self._grade_lbl = QLabel("")
        self._grade_lbl.setObjectName("statsLabel")
        info_row.addWidget(self._scenario_lbl)
        info_row.addStretch()
        info_row.addWidget(self._grade_lbl)
        info_row.addWidget(self._score_lbl)
        root.addLayout(info_row)

        # Turn table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["你说了", "教练回复", "SMCP 评语", "得分"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 60)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setWordWrap(True)
        root.addWidget(self._table)

        # AI evaluation area
        eval_sep = QFrame()
        eval_sep.setFrameShape(QFrame.Shape.HLine)
        eval_sep.setStyleSheet("color: #2C3E50;")
        root.addWidget(eval_sep)

        eval_title = QLabel("🤖 AI 综合评估")
        eval_title.setObjectName("cardSubtitle")
        root.addWidget(eval_title)

        self._eval_text = QTextEdit()
        self._eval_text.setReadOnly(True)
        self._eval_text.setMinimumHeight(150)
        self._eval_text.setStyleSheet(
            "QTextEdit { background: #1A2332; color: #D0E8FF; "
            "border: 1px solid #2C3E50; border-radius: 6px; padding: 8px; "
            "font-size: 13px; }"
        )
        root.addWidget(self._eval_text)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        retry_btn = QPushButton("🔁  再练一次")
        retry_btn.setObjectName("primaryBtn")
        retry_btn.clicked.connect(self._on_retry)

        back_btn = QPushButton("◀  返回场景库")
        back_btn.clicked.connect(self.restart_requested)

        btn_row.addWidget(retry_btn)
        btn_row.addWidget(back_btn)
        root.addLayout(btn_row)

        self._retry_scenario_id: int = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "优秀 S"
        if score >= 75:
            return "良好 A"
        if score >= 60:
            return "及格 B"
        return "待提高 C"

    def _set_evaluation(self, text: str) -> None:
        self._eval_text.setPlainText(text)

    def _set_cell(self, row: int, col: int, text: str) -> None:
        item = QTableWidgetItem(text or "")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, col, item)

    def _on_retry(self) -> None:
        if self._retry_scenario_id:
            self.retry_requested.emit(self._retry_scenario_id)
