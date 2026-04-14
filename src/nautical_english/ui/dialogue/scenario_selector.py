"""ScenarioSelectorView — lets the student choose a scenario before practice.

Displays scenario cards grouped by category with difficulty ★ indicators.
Emits ``scenario_selected(scenario_id: int)`` when the user clicks Start.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nautical_english.scenario.repository import ScenarioRepository
from nautical_english.scenario.models import Scenario


class _ScenarioCard(QFrame):
    """Clickable card that represents a single scenario."""

    clicked = pyqtSignal(int)   # scenario_id

    def __init__(self, scenario: Scenario, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scenario_id = scenario.id
        self.setObjectName("scenarioCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        # Title row
        title_row = QHBoxLayout()
        name_lbl = QLabel(scenario.name_en)
        name_lbl.setObjectName("cardTitle")
        zh_lbl = QLabel(scenario.name_zh)
        zh_lbl.setObjectName("cardSubtitle")
        diff_lbl = QLabel("★" * scenario.difficulty + "☆" * (3 - scenario.difficulty))
        diff_lbl.setObjectName("cardDifficulty")
        title_row.addWidget(name_lbl)
        title_row.addWidget(zh_lbl)
        title_row.addStretch()
        title_row.addWidget(diff_lbl)
        layout.addLayout(title_row)

        # Description
        desc_lbl = QLabel(scenario.description_zh)
        desc_lbl.setObjectName("cardDesc")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Start button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        start_btn = QPushButton("开始对话")
        start_btn.setObjectName("startDialogueBtn")
        start_btn.setFixedWidth(100)
        start_btn.clicked.connect(self._emit_clicked)
        btn_row.addWidget(start_btn)
        layout.addLayout(btn_row)

    def _emit_clicked(self) -> None:
        self.clicked.emit(self._scenario_id)


class ScenarioSelectorView(QWidget):
    """Full-page scenario selection screen."""

    scenario_selected = pyqtSignal(int)  # scenario_id

    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = scenario_repo
        self._build_ui()
        self.reload()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Refresh the scenario list from the database."""
        scenarios = self._repo.get_all_scenarios()
        self._category_combo.clear()
        self._category_combo.addItem("全部类别", userData=None)
        categories = sorted({s.category for s in scenarios if s.category})
        for cat in categories:
            self._category_combo.addItem(cat, userData=cat)
        self._populate_cards(scenarios)

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Header
        header = QLabel("SMCP 情景对话练习")
        header.setObjectName("pageTitle")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(header)

        sub = QLabel("选择一个场景，与 AI 教练进行口语对话练习")
        sub.setObjectName("pageSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("类别:"))
        self._category_combo = QComboBox()
        self._category_combo.setMinimumWidth(160)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        filter_row.addWidget(self._category_combo)
        filter_row.addStretch()
        root.addLayout(filter_row)

        # Scrollable card area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._card_container = QWidget()
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setSpacing(8)
        self._card_layout.addStretch()
        self._scroll.setWidget(self._card_container)
        root.addWidget(self._scroll)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _populate_cards(self, scenarios: list[Scenario]) -> None:
        # Remove old cards (keep trailing stretch)
        while self._card_layout.count() > 1:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for scenario in scenarios:
            card = _ScenarioCard(scenario, self._card_container)
            card.clicked.connect(self.scenario_selected)
            self._card_layout.insertWidget(self._card_layout.count() - 1, card)

    def _on_category_changed(self, _idx: int) -> None:
        cat = self._category_combo.currentData()
        if cat is None:
            scenarios = self._repo.get_all_scenarios()
        else:
            scenarios = self._repo.get_scenarios_by_category(cat)
        self._populate_cards(scenarios)
