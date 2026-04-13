"""音频录制模块 — 使用 sounddevice 从麦克风采集音频"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioCapture:
    """麦克风录音，支持阻塞式录制和异步流式录制两种模式。"""

    def __init__(self, sample_rate: int = 16_000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._recording: np.ndarray | None = None

    # ── 设备查询 ─────────────────────────────────────────────────

    def get_available_devices(self) -> list[dict]:
        """返回当前系统所有输入设备列表。"""
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)  # type: ignore[arg-type]
            if d["max_input_channels"] > 0
        ]

    # ── 阻塞式录制 ───────────────────────────────────────────────

    def record(self, duration: float) -> np.ndarray:
        """同步录音 ``duration`` 秒，返回 float32 一维数组。"""
        frames = int(duration * self.sample_rate)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()
        self._recording = audio.flatten()
        return self._recording

    # ── 文件操作 ─────────────────────────────────────────────────

    def save(self, path: Path) -> None:
        """将最近一次录音保存为 WAV 文件。"""
        if self._recording is None:
            raise ValueError("No recording available. Call record() first.")
        sf.write(str(path), self._recording, self.sample_rate)

    @staticmethod
    def load(path: Path) -> np.ndarray:
        """加载 WAV 文件，返回 float32 一维数组（16kHz 单声道）。"""
        data, _ = sf.read(str(path), dtype="float32", always_2d=False)
        return data
