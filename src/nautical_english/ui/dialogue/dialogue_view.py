"""DialogueView — main conversation screen for SMCP AI coach dialogue.

Layout:
  ┌──────────────────────────────────────────────────────────┐
  │  Scenario name / description header                      │
  ├──────────────────────────────────────────────────────────┤
  │  Conversation history (coach / student bubbles)          │
  │  (QScrollArea)                                           │
  ├──────────────────────────────────────────────────────────┤
  │  SMCP assessment panel (collapsible, last turn only)     │
  ├──────────────────────────────────────────────────────────┤
  │  [🎤 Record]  [▶ Play back]  [⌨ Type instead]  [End]   │
  └──────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import re
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nautical_english.coach.service import CoachService, CoachState, TurnResult
from nautical_english.scenario.models import Scenario


# ---------------------------------------------------------------------------
# Chat bubble
# ---------------------------------------------------------------------------

class _Bubble(QFrame):
    _COACH_BG = "#1E3A5F"
    _STUDENT_BG = "#1B4D2E"

    def __init__(
        self,
        role: str,
        text: str,
        judgement: str = "",
        score: float | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        bg = self._COACH_BG if role == "coach" else self._STUDENT_BG
        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border-radius: 8px; "
            f"padding: 4px; margin: 2px 0; }}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 6, 8, 6)
        self._layout.setSpacing(4)

        role_label_text = "🎙 Coach" if role == "coach" else "👤 You"
        role_lbl = QLabel(role_label_text)
        role_lbl.setStyleSheet("color: #AAB8C2; font-size: 11px;")
        self._layout.addWidget(role_lbl)

        self._text_lbl = QLabel(text)
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        self._layout.addWidget(self._text_lbl)

        if judgement:
            self._add_judge_widgets(judgement, score)
        elif score is not None:
            score_lbl = QLabel(f"得分: {score:.0f} / 100")
            score_lbl.setStyleSheet("color: #2ECC71; font-size: 12px;")
            self._layout.addWidget(score_lbl)

    def update_reply(self, text: str) -> None:
        """Update bubble text in-place while streaming."""
        self._text_lbl.setText(text)

    def finalize(self, reply_text: str, judgement: str, score: float | None) -> None:
        """Replace streaming cursor with final text and add judgement/score widgets."""
        self._text_lbl.setText(reply_text)
        if judgement:
            self._add_judge_widgets(judgement, score)
        elif score is not None:
            score_lbl = QLabel(f"得分: {score:.0f} / 100")
            score_lbl.setStyleSheet("color: #2ECC71; font-size: 12px;")
            self._layout.addWidget(score_lbl)

    def _add_judge_widgets(self, judgement: str, score: float | None) -> None:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2C3E50;")
        self._layout.addWidget(sep)

        judge_lbl = QLabel(f"📋 {judgement}")
        judge_lbl.setWordWrap(True)
        judge_lbl.setStyleSheet("color: #F1C40F; font-size: 12px;")
        self._layout.addWidget(judge_lbl)

        if score is not None:
            score_lbl = QLabel(f"得分: {score:.0f} / 100")
            score_lbl.setStyleSheet("color: #2ECC71; font-size: 12px;")
            self._layout.addWidget(score_lbl)


# ---------------------------------------------------------------------------
# Recording thread (inline — keeps UI responsive)
# ---------------------------------------------------------------------------

class _RecordWorker(QThread):
    chunk_ready = pyqtSignal(np.ndarray)
    finished_signal = pyqtSignal(np.ndarray, float)  # samples, duration_s

    def __init__(self, max_seconds: float = 10.0, sr: int = 16000) -> None:
        super().__init__()
        self._max_seconds = max_seconds
        self._sr = sr
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        frames: list[np.ndarray] = []
        block_size = 1600  # 100 ms chunks

        def _callback(indata: np.ndarray, frames_count: int, time_info, status) -> None:
            chunk = indata[:, 0].copy()
            frames.append(chunk)
            self.chunk_ready.emit(chunk)

        with sd.InputStream(
            samplerate=self._sr,
            channels=1,
            dtype="float32",
            blocksize=block_size,
            callback=_callback,
        ):
            total_blocks = int(self._max_seconds * self._sr / block_size)
            for _ in range(total_blocks):
                if self._stop_flag:
                    break
                self.msleep(100)

        if frames:
            audio = np.concatenate(frames)
            duration = audio.size / self._sr
            self.finished_signal.emit(audio, duration)
        else:
            self.finished_signal.emit(np.zeros(1, dtype=np.float32), 0.0)


# ---------------------------------------------------------------------------
# DialogueView
# ---------------------------------------------------------------------------

class DialogueView(QWidget):
    """Active conversation screen."""

    session_ended = pyqtSignal(str)   # session_id

    def __init__(
        self,
        coach_service: CoachService,
        scenario: Scenario,
        asr_callback: Optional[Callable[[np.ndarray, int], str]] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._coach = coach_service
        self._scenario = scenario
        self._asr = asr_callback  # optional speech-to-text function
        self._audio_buffer: np.ndarray | None = None
        self._sr = 16000
        self._record_worker: _RecordWorker | None = None
        self._stream_bubble: _Bubble | None = None   # coach bubble being streamed

        self._build_ui()
        self._connect_coach()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def start(self, student_id: str) -> None:
        """Kick off the session — receives opening line from coach."""
        opening = self._coach.start_session(
            scenario_id=self._scenario.id,
            student_id=student_id,
        )
        self._append_bubble("coach", opening)
        self._update_controls()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # Header
        hdr = QLabel(f"{self._scenario.name_en}  |  {self._scenario.name_zh}")
        hdr.setObjectName("dialogueHeader")
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setWordWrap(True)
        root.addWidget(hdr)

        desc = QLabel(self._scenario.description_zh)
        desc.setObjectName("pageSubtitle")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        root.addWidget(desc)

        # Scroll area for bubbles
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._bubble_container = QWidget()
        self._bubble_layout = QVBoxLayout(self._bubble_container)
        self._bubble_layout.setSpacing(6)
        self._bubble_layout.addStretch()
        self._scroll.setWidget(self._bubble_container)
        root.addWidget(self._scroll)

        # Status label
        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("dialogueStatus")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._status_lbl)

        # Controls
        ctrl = QHBoxLayout()
        self._rec_btn = QPushButton("🎤  开始录音")
        self._rec_btn.setObjectName("recBtn")
        self._rec_btn.setCheckable(True)
        self._rec_btn.toggled.connect(self._on_record_toggled)

        self._play_btn = QPushButton("▶  回听")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._play_back)

        self._type_btn = QPushButton("⌨  文字输入")
        self._type_btn.clicked.connect(self._type_instead)

        self._send_btn = QPushButton("发送")
        self._send_btn.setObjectName("primaryBtn")
        self._send_btn.setEnabled(False)
        self._send_btn.clicked.connect(self._send_audio)

        self._end_btn = QPushButton("结束对话")
        self._end_btn.setObjectName("dangerBtn")
        self._end_btn.clicked.connect(self._end_session)

        for btn in (self._rec_btn, self._play_btn, self._type_btn, self._send_btn, self._end_btn):
            ctrl.addWidget(btn)

        root.addLayout(ctrl)

    # ------------------------------------------------------------------
    # Coach wiring
    # ------------------------------------------------------------------

    def _connect_coach(self) -> None:
        self._coach._on_turn_complete = self._on_turn_result
        self._coach._on_error = self._on_llm_error
        self._coach._on_stream_chunk = self._on_raw_chunk

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _on_record_toggled(self, checked: bool) -> None:
        if checked:
            self._rec_btn.setText("⏹  停止")
            self._audio_buffer = None
            self._play_btn.setEnabled(False)
            self._send_btn.setEnabled(False)
            self._status_lbl.setText("录音中…")
            self._record_worker = _RecordWorker(max_seconds=10.0, sr=self._sr)
            self._record_worker.finished_signal.connect(self._on_recording_done)
            self._record_worker.start()
        else:
            self._rec_btn.setText("🎤  开始录音")
            if self._record_worker:
                self._record_worker.stop()
                self._record_worker = None
            self._status_lbl.setText("")

    def _on_recording_done(self, audio: np.ndarray, duration: float) -> None:
        self._audio_buffer = audio
        self._status_lbl.setText(f"已录音 {duration:.1f} 秒")
        self._play_btn.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._rec_btn.setChecked(False)

    def _play_back(self) -> None:
        if self._audio_buffer is not None and self._audio_buffer.size > 1:
            sd.play(self._audio_buffer, samplerate=self._sr)

    # ------------------------------------------------------------------
    # Send / type
    # ------------------------------------------------------------------

    def _send_audio(self) -> None:
        if self._audio_buffer is None:
            return
        text = ""
        if self._asr is not None:
            try:
                text = self._asr(self._audio_buffer, self._sr)
            except Exception:  # noqa: BLE001
                text = ""
        if not text:
            text = "(录音)"

        self._append_bubble("student", text)
        self._status_lbl.setText("AI 教练思考中…")
        self._set_input_enabled(False)
        self._coach.student_speak(text)

    def _type_instead(self) -> None:
        text, ok = QInputDialog.getText(self, "文字输入", "请输入你的回复（英文）：")
        if ok and text.strip():
            self._append_bubble("student", text.strip())
            self._status_lbl.setText("AI 教练思考中…")
            self._set_input_enabled(False)
            self._coach.student_speak(text.strip())

    # ------------------------------------------------------------------
    # Coach callbacks
    # ------------------------------------------------------------------

    def _on_turn_result(self, result: TurnResult) -> None:
        """Called from background thread — post to main thread via QTimer."""
        QTimer.singleShot(0, lambda: self._apply_turn_result(result))

    def _apply_turn_result(self, result: TurnResult) -> None:
        if self._stream_bubble is not None:
            # Finalize the already-visible streaming bubble
            self._stream_bubble.finalize(result.llm_reply, result.judgement, result.score)
            self._stream_bubble = None
        else:
            # Non-streaming fallback
            self._append_bubble(
                "coach",
                result.llm_reply,
                judgement=result.judgement,
                score=result.score,
            )
        self._status_lbl.setText("")
        if self._coach.state == CoachState.DONE:
            self._status_lbl.setText("\u5bf9\u8bdd\u5df2\u5b8c\u6210")
            self._set_input_enabled(False)
            self._end_btn.setEnabled(True)
        else:
            self._set_input_enabled(True)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def _on_raw_chunk(self, accumulated: str) -> None:
        """Called from background thread on each streaming chunk."""
        QTimer.singleShot(0, lambda: self._apply_stream_chunk(accumulated))

    def _apply_stream_chunk(self, accumulated: str) -> None:
        """Update (or create) the coach streaming bubble — runs on main thread."""
        # Extract only the [REPLY] portion for display
        reply_match = re.search(
            r'\[REPLY\](.*?)(?=\[JUDGE\]|$)', accumulated, re.DOTALL | re.IGNORECASE
        )
        display = reply_match.group(1).strip() if reply_match else accumulated.strip()

        if self._stream_bubble is None:
            # Create the bubble on first chunk
            self._stream_bubble = _Bubble("coach", display + " \u258c", parent=self._bubble_container)
            idx = self._bubble_layout.count() - 1  # before stretch
            self._bubble_layout.insertWidget(idx, self._stream_bubble)
        else:
            self._stream_bubble.update_reply(display + " \u258c")

        QTimer.singleShot(
            50,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            ),
        )

    def _on_llm_error(self, msg: str) -> None:
        QTimer.singleShot(
            0,
            lambda: (
                self._status_lbl.setText(""),
                QMessageBox.warning(self, "LLM 错误", f"AI 教练出错：\n{msg}"),
                self._set_input_enabled(True),
            ),
        )

    # ------------------------------------------------------------------
    # Session end
    # ------------------------------------------------------------------

    def _end_session(self) -> None:
        if self._coach.state not in (CoachState.DONE, CoachState.READY):
            return
        self._coach.end_session()
        self.session_ended.emit(self._coach.session_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _append_bubble(
        self,
        role: str,
        text: str,
        judgement: str = "",
        score: float | None = None,
    ) -> None:
        bubble = _Bubble(role, text, judgement=judgement, score=score, parent=self._bubble_container)
        idx = self._bubble_layout.count() - 1  # before stretch
        self._bubble_layout.insertWidget(idx, bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def _set_input_enabled(self, enabled: bool) -> None:
        self._rec_btn.setEnabled(enabled)
        self._type_btn.setEnabled(enabled)
        # play/send keep independent state
        if not enabled:
            self._send_btn.setEnabled(False)

    def _update_controls(self) -> None:
        enabled = self._coach.state == CoachState.READY
        self._set_input_enabled(enabled)
