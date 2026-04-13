"""AppConfig 单元测试"""

from __future__ import annotations

from nautical_english.config import AppConfig


def test_whisper_model_size_valid():
    cfg = AppConfig()
    assert cfg.whisper_model_size in ("tiny", "small", "medium", "large", "large-v3")


def test_db_path_is_absolute():
    cfg = AppConfig()
    assert cfg.db_path.is_absolute()


def test_score_weights_sum_to_one():
    cfg = AppConfig()
    assert abs(cfg.score_alpha + cfg.score_beta - 1.0) < 1e-6


def test_sample_rate_is_16k():
    cfg = AppConfig()
    assert cfg.sample_rate == 16_000


def test_whisper_model_dir_under_models():
    cfg = AppConfig()
    assert "whisper" in str(cfg.whisper_model_dir)


def test_db_path_ends_with_sqlite():
    cfg = AppConfig()
    assert cfg.db_path.suffix == ".db"
