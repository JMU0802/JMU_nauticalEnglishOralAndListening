"""主窗口 — 学生端与管理端联动主界面"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nautical_english.ui.admin.corpus_manager import CorpusManager
from nautical_english.ui.admin.progress_dashboard import ProgressDashboard
from nautical_english.ui.app_controller import AppController
from nautical_english.ui.student.practice_view import PracticeView
from nautical_english.ui.student.progress_view import ProgressView
from nautical_english.ui.student.result_view import ResultView
from nautical_english.ui.dialogue.dialogue_hub import DialogueHub


class MainWindow(QMainWindow):
    """应用主窗口。

    采用 QTabWidget 组织学生端（英文）和管理端（中文）。
    """

    def __init__(self) -> None:
        super().__init__()
        self._controller = AppController()
        self.setWindowTitle("Maritime English Trainer — JMU 集美大学")
        self.setMinimumSize(1100, 750)
        self._load_stylesheet()
        self._setup_ui()
        self._bind_signals()
        self._bootstrap()

    # ── UI 搭建 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_student_panel(), "Practice（练习）")
        self._tabs.addTab(self._build_dialogue_panel(), "AI 对话（SMCP）")
        self._tabs.addTab(self._build_admin_panel(), "管理后台")
        layout.addWidget(self._tabs)

    def _build_student_panel(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)

        self._student_tabs = QTabWidget()
        self._practice_view = PracticeView()
        self._result_view = ResultView()
        self._progress_view = ProgressView()
        self._student_tabs.addTab(self._practice_view, "Practice")
        self._student_tabs.addTab(self._result_view, "Result")
        self._student_tabs.addTab(self._progress_view, "Progress")
        layout.addWidget(self._student_tabs)
        return root

    def _build_admin_panel(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)

        self._admin_tabs = QTabWidget()
        self._corpus_manager = CorpusManager(repository=self._controller.repo)
        self._progress_dashboard = ProgressDashboard(repository=self._controller.repo)
        self._admin_tabs.addTab(self._corpus_manager, "语料管理")
        self._admin_tabs.addTab(self._progress_dashboard, "成绩看板")
        layout.addWidget(self._admin_tabs)
        return root

    def _build_dialogue_panel(self) -> QWidget:
        self._dialogue_hub = DialogueHub(
            scenario_repo=self._controller.scenario_repo,
            student_id_fn=self._practice_view.student_id,
        )
        return self._dialogue_hub

    # ── 样式加载 ─────────────────────────────────────────────────

    def _load_stylesheet(self) -> None:
        qss_path = (
            Path(__file__).parent / "resources" / "styles.qss"
        )
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _bind_signals(self) -> None:
        self._practice_view.next_requested.connect(self._on_next_phrase)
        self._practice_view.submit_requested.connect(self._on_submit)
        self._practice_view.category_filter_changed.connect(self._on_change_category)

        self._result_view.retry_clicked.connect(self._go_practice)
        self._result_view.next_clicked.connect(self._on_next_from_result)

        self._controller.models_loading.connect(self._on_models_loading)
        self._controller.models_ready.connect(self._on_models_ready)
        self._controller.models_error.connect(self._on_models_error)
        self._controller.session_done.connect(self._on_session_done)
        self._controller.session_error.connect(self._on_session_error)

    def _bootstrap(self) -> None:
        self.statusBar().showMessage("Loading corpus...")
        self._controller.load_corpus()
        self._practice_view.set_categories(self._controller.categories)
        self._practice_view.set_ready(False)
        self.statusBar().showMessage("Loading AI models in background...")
        self._controller.start_loading_models()

    def _on_models_loading(self, msg: str) -> None:
        self.statusBar().showMessage(msg)
        self._practice_view.set_busy(True, msg)

    def _on_models_ready(self) -> None:
        self.statusBar().showMessage("Models ready")
        self._practice_view.set_ready(True)
        self._on_next_phrase()
        self._refresh_progress()

    def _on_models_error(self, msg: str) -> None:
        self.statusBar().showMessage("Model loading failed")
        QMessageBox.critical(self, "Model Load Error", msg)

    def _on_change_category(self, category_id) -> None:  # noqa: ANN001
        self._controller.set_category_filter(category_id)
        self._on_next_phrase()

    def _on_next_phrase(self) -> None:
        phrase = self._controller.next_phrase()
        if phrase is None:
            QMessageBox.warning(self, "No Phrase", "No phrase available for this filter.")
            return
        self._practice_view.set_phrase(phrase.phrase_en, phrase.phrase_zh)
        self.statusBar().showMessage(f"Current phrase id: {phrase.id}")

    def _on_submit(self, audio, student_id: str) -> None:  # noqa: ANN001
        self._practice_view.set_busy(True, "Evaluating your speech...")
        self.statusBar().showMessage("Running ASR + scoring...")
        self._controller.run_session(audio, student_id)

    def _on_session_done(self, session_result) -> None:  # noqa: ANN001
        self._result_view.update_result(session_result)
        self._student_tabs.setCurrentWidget(self._result_view)
        self._practice_view.set_busy(False, "Evaluation complete.")
        self.statusBar().showMessage(f"Session done. Score: {session_result.overall_score:.1f}")
        self._refresh_progress()
        # 刷新管理端成绩看板
        self._progress_dashboard.refresh()

    def _on_session_error(self, msg: str) -> None:
        self._practice_view.set_busy(False, "Evaluation failed.")
        self.statusBar().showMessage("Session failed")
        QMessageBox.critical(self, "Session Error", msg)

    def _go_practice(self) -> None:
        self._student_tabs.setCurrentWidget(self._practice_view)

    def _on_next_from_result(self) -> None:
        self._go_practice()
        self._on_next_phrase()

    def _refresh_progress(self) -> None:
        records = self._controller.get_recent_records(self._practice_view.student_id())
        self._progress_view.update_records(records)
