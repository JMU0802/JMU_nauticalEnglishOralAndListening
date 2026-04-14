"""语料库管理界面 — 管理端完整 CRUD 实现"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from nautical_english.corpus.repository import CorpusRepository


# ─────────────────────────────────────────────────────────────
# 短语编辑对话框
# ─────────────────────────────────────────────────────────────

class PhraseEditDialog(QDialog):
    """新增 / 编辑短语的模态对话框。"""

    def __init__(
        self,
        categories: list,
        phrase=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._categories = categories
        self.setWindowTitle("编辑短语" if phrase else "新增短语")
        self.setMinimumWidth(440)
        self._setup_ui(phrase)

    def _setup_ui(self, phrase) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._en_edit = QLineEdit()
        self._en_edit.setPlaceholderText("英文短语（必填）")

        self._zh_edit = QLineEdit()
        self._zh_edit.setPlaceholderText("中文翻译（必填）")

        self._phonetic_edit = QLineEdit()
        self._phonetic_edit.setPlaceholderText("音标（可选）")

        self._category_combo = QComboBox()
        for cat in self._categories:
            self._category_combo.addItem(
                f"{cat.name_en} / {cat.name_zh}", cat.id
            )

        self._difficulty_spin = QSpinBox()
        self._difficulty_spin.setRange(1, 3)
        self._difficulty_spin.setSuffix(" 级")

        if phrase is not None:
            self._en_edit.setText(phrase.phrase_en)
            self._zh_edit.setText(phrase.phrase_zh)
            self._phonetic_edit.setText(phrase.phonetic or "")
            self._difficulty_spin.setValue(phrase.difficulty)
            for i in range(self._category_combo.count()):
                if self._category_combo.itemData(i) == phrase.category_id:
                    self._category_combo.setCurrentIndex(i)
                    break

        form.addRow("英文短语 *", self._en_edit)
        form.addRow("中文翻译 *", self._zh_edit)
        form.addRow("音标", self._phonetic_edit)
        form.addRow("类别", self._category_combo)
        form.addRow("难度", self._difficulty_spin)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate_and_accept(self) -> None:
        if not self._en_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "英文短语不能为空。")
            return
        if not self._zh_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "中文翻译不能为空。")
            return
        self.accept()

    def get_data(self) -> dict:
        """返回表单数据字典，与 CorpusRepository.add_phrase / update_phrase 参数匹配。"""
        return {
            "phrase_en":   self._en_edit.text().strip(),
            "phrase_zh":   self._zh_edit.text().strip(),
            "phonetic":    self._phonetic_edit.text().strip() or None,
            "category_id": self._category_combo.currentData(),
            "difficulty":  self._difficulty_spin.value(),
        }


# ─────────────────────────────────────────────────────────────
# 列索引常量
# ─────────────────────────────────────────────────────────────

_HEADERS        = ["ID", "英文短语", "中文翻译", "类别", "难度", "音标"]
_COL_ID         = 0
_COL_EN         = 1
_COL_ZH         = 2
_COL_CATEGORY   = 3
_COL_DIFFICULTY = 4
_COL_PHONETIC   = 5


class CorpusManager(QWidget):
    """SMCP 语料库管理界面（管理员端，中文 UI）。

    提供：
    - 全字段搜索过滤
    - 新增 / 编辑 / 删除短语
    - 表格即时刷新
    """

    def __init__(
        self,
        repository: CorpusRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = repository or CorpusRepository()
        self._categories: list = []
        self._setup_ui()
        self._load_data()

    # ── UI 构建 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("语料库管理")
        title.setObjectName("gradeLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        search_label = QLabel("搜索：")
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("输入关键词过滤短语…")
        self._search_edit.textChanged.connect(self._on_search)

        self._add_btn     = QPushButton("＋ 新增")
        self._edit_btn    = QPushButton("✎ 编辑")
        self._delete_btn  = QPushButton("✕ 删除")
        self._refresh_btn = QPushButton("↻ 刷新")

        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)

        self._add_btn.clicked.connect(self._add_phrase)
        self._edit_btn.clicked.connect(self._edit_phrase)
        self._delete_btn.clicked.connect(self._delete_phrase)
        self._refresh_btn.clicked.connect(self._load_data)

        toolbar.addWidget(search_label)
        toolbar.addWidget(self._search_edit, stretch=1)
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addWidget(self._refresh_btn)
        layout.addLayout(toolbar)

        # 统计标签
        self._count_label = QLabel("共 0 条短语")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._count_label)

        # 表格
        self._model = QStandardItemModel(0, len(_HEADERS))
        self._model.setHorizontalHeaderLabels(_HEADERS)

        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # 搜索所有列

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSectionResizeMode(
            _COL_EN, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            _COL_ZH, QHeaderView.ResizeMode.Stretch
        )
        self._table.setColumnWidth(_COL_ID, 50)
        self._table.setColumnWidth(_COL_DIFFICULTY, 60)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self._table)

    # ── 数据操作 ─────────────────────────────────────────────────

    def _load_data(self) -> None:
        """从数据库加载所有短语到表格模型。"""
        phrases = self._repo.get_all_phrases()
        categories = self._repo.get_all_categories()
        self._categories = categories
        self._cat_map: dict[int, str] = {
            c.id: f"{c.name_en}/{c.name_zh}" for c in categories
        }

        self._model.setRowCount(0)
        for p in phrases:
            diff_str = "★" * p.difficulty + "☆" * (3 - p.difficulty)
            row = [
                QStandardItem(str(p.id)),
                QStandardItem(p.phrase_en),
                QStandardItem(p.phrase_zh),
                QStandardItem(self._cat_map.get(p.category_id, "—")),
                QStandardItem(diff_str),
                QStandardItem(p.phonetic or ""),
            ]
            for item in row:
                item.setEditable(False)
            self._model.appendRow(row)

        self._count_label.setText(f"共 {len(phrases)} 条短语")
        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)

    def _on_search(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _on_selection_changed(self) -> None:
        has_selection = len(self._table.selectionModel().selectedRows()) > 0
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _selected_phrase_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        source_row = self._proxy.mapToSource(rows[0]).row()
        return int(self._model.item(source_row, _COL_ID).text())

    # ── CRUD 操作 ────────────────────────────────────────────────

    def _add_phrase(self) -> None:
        if not self._categories:
            self._categories = self._repo.get_all_categories()
        if not self._categories:
            QMessageBox.warning(self, "无类别", "请先新增至少一个类别，再添加短语。")
            return
        dialog = PhraseEditDialog(self._categories, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._repo.add_phrase(**data)
            self._load_data()

    def _edit_phrase(self) -> None:
        phrase_id = self._selected_phrase_id()
        if phrase_id is None:
            return
        phrase = next(
            (p for p in self._repo.get_all_phrases() if p.id == phrase_id), None
        )
        if phrase is None:
            return
        dialog = PhraseEditDialog(self._categories, phrase=phrase, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._repo.update_phrase(phrase_id, **data)
            self._load_data()

    def _delete_phrase(self) -> None:
        phrase_id = self._selected_phrase_id()
        if phrase_id is None:
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 ID={phrase_id} 的短语吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.delete_phrase(phrase_id)
            self._load_data()

    # ── 公共接口 ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """外部调用：刷新语料列表。"""
        self._load_data()
