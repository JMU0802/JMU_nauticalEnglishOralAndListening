"""AudioCapture 单元测试"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import soundfile as sf


def test_audio_capture_init():
    from nautical_english.asr.audio_capture import AudioCapture

    cap = AudioCapture(sample_rate=16000)
    assert cap.sample_rate == 16000
    assert cap.channels == 1


def test_get_available_devices_returns_list():
    with patch("nautical_english.asr.audio_capture.sd.query_devices") as mock_qd:
        mock_qd.return_value = [
            {"name": "Mic A", "max_input_channels": 1},
            {"name": "Mic B", "max_input_channels": 2},
            {"name": "Speaker", "max_input_channels": 0},  # 输出设备，应被过滤
        ]
        from nautical_english.asr.audio_capture import AudioCapture

        cap = AudioCapture()
        devices = cap.get_available_devices()
        assert len(devices) == 2  # Speaker 被过滤掉
        assert all(d["channels"] > 0 for d in devices)


def test_save_without_record_raises():
    from nautical_english.asr.audio_capture import AudioCapture

    cap = AudioCapture()
    with pytest.raises(ValueError, match="No recording"):
        cap.save(Path("test.wav"))


def test_load_returns_ndarray(tmp_path):
    from nautical_english.asr.audio_capture import AudioCapture

    wav_path = tmp_path / "test.wav"
    data = np.zeros(16000, dtype=np.float32)
    sf.write(str(wav_path), data, 16000)
    loaded = AudioCapture.load(wav_path)
    assert isinstance(loaded, np.ndarray)
    assert len(loaded) == 16000


def test_default_channels_is_mono():
    from nautical_english.asr.audio_capture import AudioCapture

    cap = AudioCapture()
    assert cap.channels == 1
