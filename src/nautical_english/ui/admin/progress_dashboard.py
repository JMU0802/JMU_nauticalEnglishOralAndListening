"""学生进度仪表板 — 管理端完整统计实现"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nautical_english.corpus.repository import CorpusRepository


# ─────────────────────────────────────────────────────────────
# 小型折线图
# ─────────────────────────────────────────────────────────────

class _MiniChart(QWidget):
    """迷你折线图：展示最近 N 次评分趋势。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(140)
        self._title = title
        self._scores: list[float] = []

    def set_scores(self, scores: list[float]) -> None:
        self._scores = scores[-20:]
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0D1F3C"))

        w, h = self.width(), self.height()
        pad = 20

        if self._title:
            painter.setPen(QColor("#95A5A6"))
            painter.drawText(pad, pad - 4, self._title)

        if len(self._scores) < 2:
            painter.setPen(QColor("#7F8C8D"))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无足够数据"
            )
            return

        # 网格线
        painter.setPen(QPen(QColor("#1E3A5F"), 1))
        for y_val in (25, 50, 75):
            py = h - pad - int(y_val / 100 * (h - 2 * pad))
            painter.drawLine(pad, py, w - pad, py)
            painter.drawText(2, py + 4, str(y_val))

        # 折线
        n = len(self._scores)
        x_step = (w - 2 * pad) / (n - 1)
        pts = []
        for i, s in enumerate(self._scores):
            px = int(pad + i * x_step)
            py = h - pad - int(s / 100 * (h - 2 * pad))
            pts.append((px, py))

        painter.setPen(QPen(QColor("#3498DB"), 2))
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

        painter.setBrush(QColor("#2ECC71"))
        painter.setPen(Qt.PenStyle.NoPen)
        for px, py in pts:
            painter.drawEllipse(px - 3, py - 3, 6, 6)


# ─────────────────────────────────────────────────────────────
# 主组件
# ─────────────────────────────────────────────────────────────

class ProgressDashboard(QWidget):
    """全体学生成绩统计仪表板（管理员端，中文 UI）。

    显示：
    - 班级整体统计（总次数、平均分、参与人数）
    - 班级评分趋势折线图
    - 每条短语的练习次数与平均分
    - 学生个人平均分排行榜
    """

    def __init__(
        self,
        repository: CorpusRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = repository or CorpusRepository()
        self._setup_ui()
        self.refresh()

    # ── UI 构建 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        title = QLabel("学生成绩看板")
        title.setObjectName("gradeLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        refresh_btn = QPushButton("↻ 刷新数据")
        refresh_btn.clicked.connect(self.refresh)
        outer.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # ── 顶部统计卡片 ──
        stats_box = QGroupBox("总体统计")
        stats_layout = QGridLayout(stats_box)
        self._total_label      = QLabel("总练习次数：0")
        self._avg_label        = QLabel("班级平均分：0.0")
        self._student_cnt      = QLabel("参与学生数：0")
        self._phrase_cnt_label = QLabel("覆盖短语数：0")
        for i, lbl in enumerate([
            self._total_label, self._avg_label,
            self._student_cnt, self._phrase_cnt_label,
        ]):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_layout.addWidget(lbl, i // 2, i % 2)
        outer.addWidget(stats_box)

        # ── 趋势图 ──
        chart_box = QGroupBox("全班评分趋势（最近 50 次）")
        chart_layout = QVBoxLayout(chart_box)
        self._chart = _MiniChart()
        self._chart.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._chart.setFixedHeight(160)
        chart_layout.addWidget(self._chart)
        outer.addWidget(chart_box)

        # ── 下半部分：短语统计 + 学生排行 ──
        bottom = QHBoxLayout()

        # 短语练习统计
        phrase_box = QGroupBox("各短语练习统计")
        phrase_layout = QVBoxLayout(phrase_box)
        self._phrase_table = QTableWidget(0, 4)
        self._phrase_table.setHorizontalHeaderLabels(["ID", "英文短语", "次数", "均分"])
        self._phrase_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._phrase_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._phrase_table.setSortingEnabled(True)
        phrase_layout.addWidget(self._phrase_table)
        bottom.addWidget(phrase_box, stretch=3)

        # 学生排行
        rank_box = QGroupBox("学生平均分排行")
        rank_layout = QVBoxLayout(rank_box)
        self._ranking_list = QListWidget()
        rank_layout.addWidget(self._ranking_list)
        bottom.addWidget(rank_box, stretch=2)

        outer.addLayout(bottom)

    # ── 数据刷新 ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """从数据库重新加载并刷新所有统计数据。"""
        records = self._repo.get_all_records(limit=1000)
        if not records:
            self._total_label.setText("总练习次数：0")
            self._avg_label.setText("班级平均分：0.0")
            self._student_cnt.setText("参与学生数：0")
            self._phrase_cnt_label.setText("覆盖短语数：0")
            self._chart.set_scores([])
            self._phrase_table.setRowCount(0)
            self._ranking_list.clear()
            self._ranking_list.addItem("暂无数据")
            return

        scores_all = [float(r.overall_score) for r in records]
        student_ids = {r.student_id for r in records}
        phrase_ids  = {r.phrase_id  for r in records}

        # 顶部卡片
        self._total_label.setText(f"总练习次数：{len(records)}")
        self._avg_label.setText(f"班级平均分：{mean(scores_all):.1f}")
        self._student_cnt.setText(f"参与学生数：{len(student_ids)}")
        self._phrase_cnt_label.setText(f"覆盖短语数：{len(phrase_ids)}")

        # 趋势图（最近 50 次，时序由 get_all_records 的 desc 翻转回来）
        recent_scores = list(reversed(scores_all[:50]))
        self._chart.set_scores(recent_scores)

        # 短语统计
        phrase_stats = self._repo.get_phrase_stats()
        self._phrase_table.setSortingEnabled(False)
        self._phrase_table.setRowCount(len(phrase_stats))
        for row, stat in enumerate(phrase_stats):
            self._phrase_table.setItem(row, 0, QTableWidgetItem(str(stat["phrase_id"])))
            en_item = QTableWidgetItem(stat["phrase_en"])
            self._phrase_table.setItem(row, 1, en_item)
            self._phrase_table.setItem(row, 2, QTableWidgetItem(str(stat["count"])))
            avg_item = QTableWidgetItem(f"{stat['avg_score']:.1f}")
            self._phrase_table.setItem(row, 3, avg_item)
        self._phrase_table.setSortingEnabled(True)

        # 学生排行（按平均分降序）
        student_scores: dict[str, list[float]] = defaultdict(list)
        for r in records:
            student_scores[r.student_id].append(float(r.overall_score))
        ranking = sorted(
            [(sid, mean(scs)) for sid, scs in student_scores.items()],
            key=lambda x: x[1],
            reverse=True,
        )
        self._ranking_list.clear()
        for rank, (sid, avg) in enumerate(ranking, start=1):
            medal = ["🏆", "🥈", "🥉"][rank - 1] if rank <= 3 else f"{rank}."
            self._ranking_list.addItem(f"{medal}  {sid}  ─  {avg:.1f} 分")

