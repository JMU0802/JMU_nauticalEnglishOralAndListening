"""ASR 模块测试"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np


def test_recognizer_transcribe_returns_string():
    from nautical_english.asr.recognizer import WhisperRecognizer

    mock_instance = MagicMock()
    mock_instance.transcribe.return_value = (
        [MagicMock(text=" Alter course to starboard")],
        MagicMock(language="en"),
    )

    rec = WhisperRecognizer.__new__(WhisperRecognizer)
    rec._model = mock_instance

    result = rec.transcribe(np.zeros(16000, dtype=np.float32))
    assert isinstance(result, str)
    assert "starboard" in result.lower()


def test_audio_capture_creates_instance():
    from nautical_english.asr.audio_capture import AudioCapture

    cap = AudioCapture(sample_rate=16000)
    assert cap.sample_rate == 16000


def test_audio_capture_get_devices_returns_list():
    with patch("nautical_english.asr.audio_capture.sd.query_devices") as mock_qd:
        mock_qd.return_value = [
            {"name": "Microphone", "max_input_channels": 2},
            {"name": "Line In", "max_input_channels": 1},
        ]
        from nautical_english.asr.audio_capture import AudioCapture

        cap = AudioCapture()
        devices = cap.get_available_devices()
        assert isinstance(devices, list)
        assert len(devices) == 2
