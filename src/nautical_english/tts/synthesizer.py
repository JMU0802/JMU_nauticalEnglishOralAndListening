"""TTS 封装 — 英语标准发音合成（多引擎自动降级）

优先级：Coqui TTS → edge-tts (Microsoft Azure, 需联网) → pyttsx3 (系统TTS)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class TTSSynthesizer:
    """语音合成器，自动选择可用的 TTS 引擎。

    Parameters
    ----------
    model_name:
        Coqui TTS 模型标识符（若 Coqui 未安装则忽略）。
    voice:
        edge-tts 声音名称，默认为英式英语男声。
    """

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/glow-tts",
        voice: str = "en-GB-RyanNeural",
    ) -> None:
        self._backend: str = "none"
        self._tts_obj = None
        self._voice = voice

        # 1. 尝试 Coqui TTS
        try:
            from TTS.api import TTS  # type: ignore[import-untyped]  # noqa: PLC0415
            self._tts_obj = TTS(model_name=model_name, progress_bar=False)
            self._backend = "coqui"
            log.info("TTS backend: Coqui TTS (%s)", model_name)
            return
        except Exception as e:  # noqa: BLE001
            log.debug("Coqui TTS unavailable: %s", e)

        # 2. 尝试 edge-tts
        try:
            import edge_tts  # type: ignore[import-untyped]  # noqa: F401
            self._backend = "edge"
            log.info("TTS backend: edge-tts (%s)", voice)
            return
        except ImportError as e:
            log.debug("edge-tts unavailable: %s", e)

        # 3. 尝试 pyttsx3
        try:
            import pyttsx3  # type: ignore[import-untyped]  # noqa: PLC0415
            engine = pyttsx3.init()
            self._tts_obj = engine
            self._backend = "pyttsx3"
            log.info("TTS backend: pyttsx3")
            return
        except Exception as e:  # noqa: BLE001
            log.debug("pyttsx3 unavailable: %s", e)

        log.warning("No TTS backend available — synthesis will be skipped")

    @property
    def backend(self) -> str:
        return self._backend

    def synthesize(self, text: str, output_path: Path) -> Path | None:
        """将 ``text`` 合成为 WAV 文件，写入 ``output_path``。

        Returns
        -------
        Path | None
            写入的文件路径，若 TTS 不可用则返回 None。
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self._backend == "coqui":
            self._tts_obj.tts_to_file(text=text, file_path=str(output_path))
            return output_path

        if self._backend == "edge":
            return self._edge_synthesize(text, output_path)

        if self._backend == "pyttsx3":
            self._tts_obj.save_to_file(text, str(output_path))
            self._tts_obj.runAndWait()
            return output_path

        return None  # no backend

    # ------------------------------------------------------------------
    # edge-tts helper
    # ------------------------------------------------------------------

    def _edge_synthesize(self, text: str, output_path: Path) -> Path | None:
        try:
            import edge_tts  # type: ignore[import-untyped]  # noqa: PLC0415

            async def _run() -> None:
                communicate = edge_tts.Communicate(text, self._voice)
                # edge-tts always produces MP3; rename accordingly
                out = output_path.with_suffix(".mp3")
                await communicate.save(str(out))

            asyncio.run(_run())
            out = output_path.with_suffix(".mp3")
            return out if out.exists() else None
        except Exception as e:  # noqa: BLE001
            log.warning("edge-tts synthesis failed: %s", e)
            return None
