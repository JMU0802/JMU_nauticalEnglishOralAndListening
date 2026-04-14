"""练习视图 — 学生端练习交互主界面"""

from __future__ import annotations

from typing import Any

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WaveformWidget(QWidget):
    """简单波形组件：展示最近一次录音波形。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(110)
        self._samples = np.zeros(800, dtype=np.float32)

    def set_samples(self, samples: np.ndarray) -> None:
        if samples.size == 0:
            self._samples = np.zeros(800, dtype=np.float32)
        else:
            # 下采样到固定点数，避免重绘开销过高。
            step = max(1, samples.size // 800)
            self._samples = samples[::step][:800]
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#13263B"))

        center_y = self.height() // 2
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


class PracticeView(QWidget):
    """学生端主练习界面（英文 UI）。"""

    submit_requested = pyqtSignal(object, str)  # (audio ndarray, student_id)
    next_requested = pyqtSignal()
    category_filter_changed = pyqtSignal(object)  # category_id | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sample_rate = 16_000
        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []
        self._latest_audio: np.ndarray | None = None
        self._recording = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        top = QGridLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._student_id_edit = QLineEdit("cadet_001")
        self._student_id_edit.setPlaceholderText("Student ID")
        form.addRow("Student", self._student_id_edit)

        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories", None)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        form.addRow("Category", self._category_combo)
        top.addLayout(form, 0, 0)

        self._next_btn = QPushButton("Next Phrase")
        self._next_btn.clicked.connect(self.next_requested.emit)
        top.addWidget(
            self._next_btn,
            0,
            1,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(top)

        self._phrase_label = QLabel("Alter course to starboard.")
        self._phrase_label.setObjectName("phraseLabel")
        self._phrase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._phrase_zh_label = QLabel("向右转向。")
        self._phrase_zh_label.setObjectName("phraseLabelZh")
        self._phrase_zh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_btn = QPushButton("HOLD TO SPEAK")
        self._record_btn.setObjectName("recordBtn")
        self._record_btn.setFixedSize(160, 80)
        self._record_btn.setEnabled(False)
        self._record_btn.pressed.connect(self._start_recording)
        self._record_btn.released.connect(self._stop_recording)

        self._submit_btn = QPushButton("Submit")
        self._submit_btn.setEnabled(False)
        self._submit_btn.clicked.connect(self._on_submit)

        self._play_my_audio_btn = QPushButton("Play My Recording")
        self._play_my_audio_btn.setEnabled(False)
        self._play_my_audio_btn.clicked.connect(self._play_my_recording)

        self._waveform = WaveformWidget()

        self._status_label = QLabel("Loading AI models...")
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._clear_btn = QPushButton("Clear Recording")
        self._clear_btn.clicked.connect(self._clear_recording)
        self._clear_btn.setEnabled(False)

        control_row = QHBoxLayout()
        control_row.addStretch()
        control_row.addWidget(self._clear_btn)
        control_row.addWidget(self._play_my_audio_btn)
        control_row.addWidget(self._submit_btn)
        control_row.addStretch()

        layout.addStretch()
        layout.addWidget(self._phrase_label)
        layout.addWidget(self._phrase_zh_label)
        layout.addSpacing(10)
        layout.addWidget(self._waveform)
        layout.addSpacing(10)
        layout.addWidget(self._record_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(control_row)
        layout.addWidget(self._status_label)
        layout.addStretch()

    def set_categories(self, categories: list[Any]) -> None:
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItem("All Categories", None)
        for cat in categories:
            self._category_combo.addItem(f"{cat.name_en} / {cat.name_zh}", cat.id)
        self._category_combo.blockSignals(False)

    def set_phrase(self, phrase_en: str, phrase_zh: str) -> None:
        self._phrase_label.setText(phrase_en)
        self._phrase_zh_label.setText(phrase_zh)
        self._clear_recording()

    def set_ready(self, ready: bool) -> None:
        self._record_btn.setEnabled(ready)
        self._next_btn.setEnabled(ready)
        if ready:
            self._status_label.setText("Models ready. Hold the red button and speak.")
        else:
            self._status_label.setText("Loading AI models...")

    def set_busy(self, busy: bool, message: str = "") -> None:
        self._record_btn.setEnabled(not busy)
        self._next_btn.setEnabled(not busy)
        self._submit_btn.setEnabled((not busy) and self._latest_audio is not None)
        self._play_my_audio_btn.setEnabled((not busy) and self._latest_audio is not None)
        if message:
            self._status_label.setText(message)

    def student_id(self) -> str:
        value = self._student_id_edit.text().strip()
        return value or "cadet_001"

    def _on_category_changed(self, _idx: int) -> None:
        self.category_filter_changed.emit(self._category_combo.currentData())

    def _audio_callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        del frames, time_info
        if status:
            return
        if indata is not None:
            self._chunks.append(indata.copy().reshape(-1))

    def _start_recording(self) -> None:
        if self._recording:
            return
        self._chunks = []
        try:
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._recording = True
            self._status_label.setText("Recording... release button to stop.")
            self._record_btn.setText("RECORDING")
        except Exception as exc:  # noqa: BLE001
            self._recording = False
            self._record_btn.setText("HOLD TO SPEAK")
            QMessageBox.critical(self, "Microphone Error", str(exc))

    def _stop_recording(self) -> None:
        if not self._recording:
            return
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:  # noqa: BLE001
            pass
        finally:
            self._stream = None
            self._recording = False
            self._record_btn.setText("HOLD TO SPEAK")

        if not self._chunks:
            self._status_label.setText("No voice detected, please try again.")
            return

        audio = np.concatenate(self._chunks).astype(np.float32)
        # 去除静音尾部，降低误触录制影响。
        nz = np.where(np.abs(audio) > 0.002)[0]
        if nz.size > 0:
            audio = audio[nz[0] : nz[-1] + 1]
        self._latest_audio = audio
        self._waveform.set_samples(audio)
        self._submit_btn.setEnabled(True)
        self._play_my_audio_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._status_label.setText("Recording captured. Click Submit to evaluate.")

    def _clear_recording(self) -> None:
        self._latest_audio = None
        self._waveform.set_samples(np.array([], dtype=np.float32))
        self._submit_btn.setEnabled(False)
        self._play_my_audio_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)

    def _play_my_recording(self) -> None:
        """回听最近一次录音。"""
        if self._latest_audio is None or self._latest_audio.size == 0:
            return
        try:
            sd.play(self._latest_audio, self._sample_rate)
            self._status_label.setText("Playing your recording...")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Playback Error", str(exc))

    def _on_submit(self) -> None:
        if self._latest_audio is None or self._latest_audio.size == 0:
            QMessageBox.information(self, "No Recording", "Please record your voice first.")
            return
        self.submit_requested.emit(self._latest_audio, self.student_id())
        self._status_label.setText("Evaluating... please wait.")
