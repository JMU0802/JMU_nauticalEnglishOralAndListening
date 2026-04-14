"""音频波形显示组件 — 可复用的 QWidget"""

from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """实时音频波形显示组件。

    调用 :meth:`set_samples` 更新波形数据，组件自动重绘。
    """

    BAR_HEIGHT = 80  # 默认高度（px）

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(self.BAR_HEIGHT)
        self._samples: np.ndarray = np.zeros(800, dtype=np.float32)

    def set_samples(self, samples: np.ndarray) -> None:
        """设置波形采样数据（float32 数组，范围 -1.0 ~ 1.0）。"""
        if samples.size == 0:
            self._samples = np.zeros(800, dtype=np.float32)
        else:
            step = max(1, samples.size // 800)
            self._samples = samples[::step][:800]
        self.update()

    def clear(self) -> None:
        """清除波形，回到静默状态。"""
        self._samples = np.zeros(800, dtype=np.float32)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#13263B"))

        center_y = self.height() // 2
        # 绘制中线
        painter.setPen(QPen(QColor("#2C3E50"), 1))
        painter.drawLine(0, center_y, self.width(), center_y)

        if self._samples.size == 0:
            return

        pen = QPen(QColor("#2ECC71"), 2)
        painter.setPen(pen)
        width = max(1, self.width())
        amp = (self.height() // 2) - 4
        count = min(self._samples.size, width)
        for x in range(count - 1):
            y1 = center_y - int(float(self._samples[x]) * amp)
            y2 = center_y - int(float(self._samples[x + 1]) * amp)
            painter.drawLine(x, y1, x + 1, y2)
