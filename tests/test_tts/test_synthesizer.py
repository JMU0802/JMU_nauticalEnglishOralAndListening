"""TTSSynthesizer 单元测试 — 使用 Mock，无需加载真实 TTS 模型"""

from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from nautical_english.tts.synthesizer import TTSSynthesizer


def _make_synth() -> TTSSynthesizer:
    """创建注入 Mock _tts 的 TTSSynthesizer 实例。"""
    synth = TTSSynthesizer.__new__(TTSSynthesizer)
    synth._tts = MagicMock()
    return synth


def test_synthesizer_creates_instance():
    synth = _make_synth()
    assert synth._tts is not None


def test_synthesize_calls_tts_to_file(tmp_path):
    synth = _make_synth()
    out_path = tmp_path / "output.wav"
    result = synth.synthesize("Alter course to starboard", out_path)

    synth._tts.tts_to_file.assert_called_once_with(
        text="Alter course to starboard",
        file_path=str(out_path),
    )
    assert result == out_path


def test_synthesize_creates_parent_dir(tmp_path):
    synth = _make_synth()
    deep_path = tmp_path / "new_dir" / "sub" / "output.wav"
    synth.synthesize("Test", deep_path)
    assert deep_path.parent.exists()


def test_synthesize_returns_path_object(tmp_path):
    synth = _make_synth()
    out_path = tmp_path / "test.wav"
    result = synth.synthesize("Hello", out_path)
    assert isinstance(result, Path)
