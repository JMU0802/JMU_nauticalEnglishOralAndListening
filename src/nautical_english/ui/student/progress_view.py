"""进度视图 — 学员历史成绩统计与趋势展示"""

from __future__ import annotations

from statistics import mean

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)


class ScoreTrendWidget(QWidget):
    """近几次成绩折线图。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._scores: list[float] = []

    def set_scores(self, scores: list[float]) -> None:
        self._scores = scores[-10:]
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#13263B"))

        if len(self._scores) < 2:
            painter.setPen(QPen(QColor("#95A5A6"), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Need 2+ records")
            return

        width = max(1, self.width())
        height = max(1, self.height())
        padding = 16
        min_v, max_v = 0.0, 100.0
        x_step = (width - 2 * padding) / (len(self._scores) - 1)

        points: list[tuple[int, int]] = []
        for i, score in enumerate(self._scores):
            x = int(padding + i * x_step)
            norm = (score - min_v) / (max_v - min_v)
            y = int(height - padding - norm * (height - 2 * padding))
            points.append((x, y))

        painter.setPen(QPen(QColor("#2ECC71"), 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        painter.setPen(QPen(QColor("#F39C12"), 4))
        for x, y in points:
            painter.drawPoint(x, y)


class ProgressView(QWidget):
    """展示学生历史练习进度（英文 UI）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Learning Progress")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("gradeLabel")

        stats = QGridLayout()
        self._total_label = QLabel("Total Sessions: 0")
        self._avg_label = QLabel("Average Score: 0.0")
        self._best_label = QLabel("Best Score: 0.0")
        self._last_label = QLabel("Last Score: 0.0")
        stats.addWidget(self._total_label, 0, 0)
        stats.addWidget(self._avg_label, 0, 1)
        stats.addWidget(self._best_label, 1, 0)
        stats.addWidget(self._last_label, 1, 1)

        self._trend = ScoreTrendWidget()

        self._recent_list = QListWidget()
        self._recent_list.setMinimumHeight(180)

        layout.addWidget(title)
        layout.addLayout(stats)
        layout.addWidget(self._trend)
        layout.addWidget(QLabel("Recent Records"))
        layout.addWidget(self._recent_list)

    def update_records(self, records: list) -> None:
        if not records:
            self._total_label.setText("Total Sessions: 0")
            self._avg_label.setText("Average Score: 0.0")
            self._best_label.setText("Best Score: 0.0")
            self._last_label.setText("Last Score: 0.0")
            self._trend.set_scores([])
            self._recent_list.clear()
            self._recent_list.addItem("No records yet.")
            return

        scores = [float(r.overall_score) for r in records]
        self._total_label.setText(f"Total Sessions: {len(scores)}")
        self._avg_label.setText(f"Average Score: {mean(scores):.1f}")
        self._best_label.setText(f"Best Score: {max(scores):.1f}")
        self._last_label.setText(f"Last Score: {scores[-1]:.1f}")
        self._trend.set_scores(scores)

        self._recent_list.clear()
        for rec in reversed(records[-15:]):
            dt = rec.created_at.strftime("%Y-%m-%d %H:%M")
            self._recent_list.addItem(
                f"{dt} | score={rec.overall_score:.1f} | sim={rec.similarity_score:.2f}"
            )
