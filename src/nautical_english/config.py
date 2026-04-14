"""全局配置模块 — 所有路径、模型参数、评分超参数集中管理"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ── 项目根目录（src/nautical_english/config.py → 上三级）────────
BASE_DIR: Path = Path(__file__).parent.parent.parent
MODELS_DIR: Path = BASE_DIR / "models"
CORPUS_DIR: Path = BASE_DIR / "corpus"
ASSETS_DIR: Path = BASE_DIR / "assets"


@dataclass
class AppConfig:
    # ── ASR 配置 ──────────────────────────────────────────────────
    whisper_model_size: str = "large-v3"
    whisper_model_dir: Path = field(
        default_factory=lambda: MODELS_DIR / "whisper"
    )
    whisper_device: str = "auto"          # "cpu" | "cuda" | "auto"
    whisper_language: str = "en"

    # ── TTS 配置 ──────────────────────────────────────────────────
    tts_model_name: str = "tts_models/en/ljspeech/glow-tts"
    tts_model_dir: Path = field(
        default_factory=lambda: MODELS_DIR / "tts"
    )

    # ── NLP / 匹配配置 ────────────────────────────────────────────
    sbert_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    sbert_model_dir: Path = field(
        default_factory=lambda: MODELS_DIR / "sbert"
    )

    # ── 数据库 ────────────────────────────────────────────────────
    db_path: Path = field(
        default_factory=lambda: CORPUS_DIR / "db" / "corpus.db"
    )

    # ── 音频录制 ──────────────────────────────────────────────────
    sample_rate: int = 16_000
    max_record_seconds: int = 30

    # ── 评分超参数（α·语义相似度 + β·(1-WER)）───────────────────
    score_alpha: float = 0.6
    score_beta: float = 0.4


# 默认单例（可在 main.py 覆盖）
default_config = AppConfig()
