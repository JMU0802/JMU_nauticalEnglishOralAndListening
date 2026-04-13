"""Coqui TTS 封装 — 离线英语语音合成"""

from __future__ import annotations

from pathlib import Path


class TTSSynthesizer:
    """对 Coqui TTS 的轻量封装，支持英文标准发音合成。

    Parameters
    ----------
    model_name:
        Coqui TTS 模型标识符（详见 ``tts --list_models``）。
    """

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/glow-tts",
    ) -> None:
        # 延迟导入，避免在单元测试中强制加载大模型
        from TTS.api import TTS  # noqa: PLC0415

        self._tts = TTS(model_name=model_name, progress_bar=False)

    def synthesize(self, text: str, output_path: Path) -> Path:
        """将 ``text`` 合成为 WAV 文件，写入 ``output_path``。

        Returns
        -------
        Path
            实际写入的文件路径。
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._tts.tts_to_file(text=text, file_path=str(output_path))
        return output_path
