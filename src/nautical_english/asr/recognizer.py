"""Whisper ASR 封装 — 基于 faster-whisper，加入航海术语提示词"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from faster_whisper import WhisperModel as _WhisperModel

# 航海术语提示词 — 显著提升专业术语识别率
_MARITIME_PROMPT = (
    "Maritime English SMCP. "
    "Terms: starboard, port, bow, stern, bearing, course, vessel, "
    "collision, distress, mayday, navigating, anchoring, mooring, "
    "underway, overtaking, crossing, stand-on, give-way, lookout."
)


class WhisperRecognizer:
    """对 faster-whisper WhisperModel 的轻量封装。

    Parameters
    ----------
    model_size:
        Whisper 模型规格，如 ``"tiny"``、``"medium"``、``"large-v3"``。
    model_dir:
        本地模型缓存目录（``None`` 时使用默认缓存）。
    device:
        推理设备：``"cpu"``、``"cuda"`` 或 ``"auto"``。
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        model_dir: Path | None = None,
        device: str = "auto",
    ) -> None:
        # 延迟导入，避免在单元测试中强制加载大模型
        from faster_whisper import WhisperModel  # noqa: PLC0415

        # 优先使用本地直接路径（models/whisper/<size>/model.bin）
        local_path = Path(model_dir) / model_size if model_dir else None
        if local_path and (local_path / "model.bin").exists():
            model_arg: str | Path = local_path
            download_root = None
        else:
            model_arg = model_size
            download_root = str(model_dir) if model_dir else None

        self._model: _WhisperModel = WhisperModel(
            str(model_arg),
            device=device,
            download_root=download_root,
        )

    def transcribe(self, audio: np.ndarray | str | Path) -> str:
        """识别音频，返回纯文本字符串。

        Parameters
        ----------
        audio:
            ``np.ndarray``（float32 / 16kHz）、文件路径字符串或 Path 对象。
        """
        segments, _ = self._model.transcribe(
            audio,  # type: ignore[arg-type]
            language="en",
            initial_prompt=_MARITIME_PROMPT,
            beam_size=5,
            vad_filter=True,          # 过滤静音片段
            vad_parameters={"min_silence_duration_ms": 500},
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
