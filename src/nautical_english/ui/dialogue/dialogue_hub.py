"""DialogueHub — top-level container for the SMCP AI dialogue feature.

Manages the 3-screen flow:
  ScenarioSelectorView → DialogueView → DialogueSummaryView

Uses QStackedWidget so switching is instant.
"""

from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from nautical_english.coach.service import CoachService
from nautical_english.llm import get_provider
from nautical_english.scenario.repository import ScenarioRepository
from nautical_english.ui.dialogue.dialogue_summary import DialogueSummaryView
from nautical_english.ui.dialogue.dialogue_view import DialogueView
from nautical_english.ui.dialogue.scenario_selector import ScenarioSelectorView


_PAGE_SELECTOR = 0
_PAGE_DIALOGUE = 1
_PAGE_SUMMARY  = 2


class DialogueHub(QWidget):
    """Wraps the 3-screen dialogue flow in one reusable widget."""

    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        student_id_fn: Optional[Callable[[], str]] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = scenario_repo
        self._student_id_fn = student_id_fn or (lambda: "student_001")

        # One CoachService instance — replaced per session
        self._coach: CoachService | None = None
        self._active_scenario_id: int = 0

        self._build_ui()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()

        # Page 0 — selector
        self._selector = ScenarioSelectorView(self._repo)
        self._selector.scenario_selected.connect(self._on_scenario_selected)
        self._stack.addWidget(self._selector)

        # Page 1 — dialogue (placeholder, replaced per session)
        self._dialogue_placeholder = QWidget()
        self._stack.addWidget(self._dialogue_placeholder)

        # Page 2 — summary
        self._summary = DialogueSummaryView(self._repo)
        self._summary.restart_requested.connect(self._show_selector)
        self._summary.retry_requested.connect(self._on_scenario_selected)
        self._stack.addWidget(self._summary)

        root.addWidget(self._stack)
        self._stack.setCurrentIndex(_PAGE_SELECTOR)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _show_selector(self) -> None:
        self._selector.reload()
        self._stack.setCurrentIndex(_PAGE_SELECTOR)

    def _on_scenario_selected(self, scenario_id: int) -> None:
        self._active_scenario_id = scenario_id
        scenario = self._repo.get_scenario(scenario_id)
        if scenario is None:
            return

        # Build a fresh CoachService
        try:
            provider = get_provider()
        except Exception:  # noqa: BLE001
            provider = None  # type: ignore[assignment]

        if provider is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "LLM 未配置",
                "未找到可用的 LLM API Key。\n"
                "请在项目根目录创建 .env 文件并设置 DEEPSEEK_API_KEY 或 KIMI_API_KEY。",
            )
            return

        self._coach = CoachService(
            scenario_repo=self._repo,
            provider=provider,
        )

        # Replace dialogue page widget
        old_widget = self._stack.widget(_PAGE_DIALOGUE)
        if old_widget is not self._dialogue_placeholder:
            self._stack.removeWidget(old_widget)
            old_widget.deleteLater()

        new_view = DialogueView(
            coach_service=self._coach,
            scenario=scenario,
        )
        new_view.session_ended.connect(self._on_session_ended)
        self._stack.insertWidget(_PAGE_DIALOGUE, new_view)
        # remove placeholder if still there
        if self._stack.indexOf(self._dialogue_placeholder) != -1:
            self._stack.removeWidget(self._dialogue_placeholder)

        self._stack.setCurrentIndex(_PAGE_DIALOGUE)
        student_id = self._student_id_fn()
        new_view.start(student_id)

    def _on_session_ended(self, session_id: str) -> None:
        self._summary.load_session(session_id)
        self._stack.setCurrentIndex(_PAGE_SUMMARY)
