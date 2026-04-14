"""录音线程 — 非阻塞录音 QThread，逐块发送波形数据"""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal


class RecordingThread(QThread):
    """在独立线程中捕获麦克风音频，UI 线程零阻塞。

    实时信号
    --------
    chunk_ready(np.ndarray)      : 每 100ms 发出一次音频块（用于波形刷新）
    finished_signal(np.ndarray)  : 录音结束，发出完整音频数组
    error_signal(str)            : 录音出错

    使用方法::

        thread = RecordingThread(max_seconds=5.0)
        thread.chunk_ready.connect(waveform_widget.set_samples)
        thread.finished_signal.connect(handle_audio)
        thread.start()          # 开始录音
        # 需要停止时调用：
        thread.stop()
    """

    chunk_ready     = pyqtSignal(np.ndarray)
    finished_signal = pyqtSignal(np.ndarray)
    error_signal    = pyqtSignal(str)

    SAMPLE_RATE  = 16_000
    CHUNK_FRAMES = 1_600   # 100ms / chunk

    def __init__(
        self,
        max_seconds: float = 8.0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._max_seconds = max_seconds
        self._running = False

    def stop(self) -> None:
        """请求停止录音（线程安全）。"""
        self._running = False

    def run(self) -> None:
        self._running = True
        frames: list[np.ndarray] = []
        max_frames = int(self._max_seconds * self.SAMPLE_RATE)

        try:
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=self.CHUNK_FRAMES,
            ) as stream:
                collected = 0
                while self._running and collected < max_frames:
                    chunk, _ = stream.read(self.CHUNK_FRAMES)
                    mono = chunk[:, 0]
                    frames.append(mono)
                    collected += len(mono)
                    self.chunk_ready.emit(mono)

        except Exception as exc:  # noqa: BLE001
            self.error_signal.emit(str(exc))
            return

        if frames:
            audio = np.concatenate(frames)[:max_frames]
        else:
            audio = np.zeros(self.SAMPLE_RATE, dtype=np.float32)

        self.finished_signal.emit(audio)
        self._running = False
