"""结果视图 — 展示单次评估结果与下一步操作"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ResultView(QWidget):
    """展示单次练习评分结果（英文 UI）。"""

    retry_clicked = pyqtSignal()
    next_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tts_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._score_label = QLabel("--")
        self._score_label.setObjectName("scoreLabel")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._grade_label = QLabel("--")
        self._grade_label.setObjectName("gradeLabel")
        self._grade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._feedback_label = QLabel("Submit your recording to see feedback.")
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setWordWrap(True)

        self._recognized_label = QLabel("Recognized: --")
        self._recognized_label.setWordWrap(True)
        self._reference_label = QLabel("Reference: --")
        self._reference_label.setWordWrap(True)

        self._error_words = QListWidget()
        self._error_words.setMaximumHeight(90)

        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setPlaceholderText("Diff will appear here...")
        self._diff_view.setMaximumHeight(120)

        # ── 播放标准发音按钮 ──
        self._play_btn = QPushButton("▶  Play Standard Pronunciation")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._play_tts)

        btn_layout = QHBoxLayout()
        self._retry_btn = QPushButton("Try Again")
        self._next_btn = QPushButton("Next Phrase →")
        self._retry_btn.clicked.connect(self.retry_clicked.emit)
        self._next_btn.clicked.connect(self.next_clicked.emit)
        btn_layout.addWidget(self._retry_btn)
        btn_layout.addWidget(self._next_btn)

        layout.addStretch()
        layout.addWidget(self._score_label)
        layout.addWidget(self._grade_label)
        layout.addWidget(self._feedback_label)
        layout.addWidget(self._recognized_label)
        layout.addWidget(self._reference_label)
        layout.addWidget(self._diff_view)
        layout.addWidget(QLabel("Error Words"))
        layout.addWidget(self._error_words)
        layout.addWidget(self._play_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def update_result(self, session_result) -> None:
        """用 SessionResult 更新界面。"""
        fb = session_result.feedback
        self._score_label.setText(f"{session_result.overall_score:.1f}")
        self._grade_label.setText(fb.grade)
        self._feedback_label.setText(fb.feedback_en)
        self._recognized_label.setText(f"Recognized: {fb.recognized_text}")
        self._reference_label.setText(f"Reference: {fb.standard_phrase_en}")
        self._diff_view.setHtml(fb.diff_html or "")
        self._error_words.clear()
        if fb.error_words:
            self._error_words.addItems(fb.error_words)
        else:
            self._error_words.addItem("No major word errors.")

        # 设置 TTS 音频路径
        tts_path = getattr(session_result, "tts_audio_path", None)
        if tts_path and Path(tts_path).exists():
            self._tts_path = Path(tts_path)
            self._play_btn.setEnabled(True)
        else:
            self._tts_path = None
            self._play_btn.setEnabled(False)

    def _play_tts(self) -> None:
        """播放 TTS 生成的标准发音音频。"""
        if self._tts_path is None or not self._tts_path.exists():
            return
        try:
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PyQt6.QtCore import QUrl
            if not hasattr(self, "_player"):
                self._player = QMediaPlayer()
                self._audio_out = QAudioOutput()
                self._player.setAudioOutput(self._audio_out)
            self._player.setSource(QUrl.fromLocalFile(str(self._tts_path)))
            self._player.play()
        except Exception:  # noqa: BLE001
            # 若 QMediaPlayer 不可用，回退到 sounddevice 播放
            self._play_with_sounddevice()

    def _play_with_sounddevice(self) -> None:
        """用 soundfile + sounddevice 播放 WAV 文件（不依赖 QtMultimedia）。"""
        if self._tts_path is None:
            return
        try:
            import sounddevice as sd
            import soundfile as sf
            data, samplerate = sf.read(str(self._tts_path), dtype="float32")
            sd.play(data, samplerate)
        except Exception:  # noqa: BLE001
            pass
