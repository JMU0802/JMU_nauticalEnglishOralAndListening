"""性能基准测试脚本。

测量关键路径耗时：模型加载 + 单次推理。

用法：
    python scripts/benchmark.py
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(ROOT / "src"))

from nautical_english.config import AppConfig
from nautical_english.corpus.repository import CorpusRepository


def measure(label: str, func, *args, **kwargs):
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"{label:<34s} {elapsed:7.2f}s")
    return result, elapsed


def main() -> None:
    cfg = AppConfig()
    print("=" * 60)
    print("Nautical English Trainer Benchmark")
    print("=" * 60)

    repo = CorpusRepository()
    phrases = [p.phrase_en for p in repo.get_all_phrases()]
    if not phrases:
        print("No phrases in database. Run scripts/seed_corpus.py first.")
        return

    from nautical_english.asr.recognizer import WhisperRecognizer
    from nautical_english.nlp.matcher import SentenceMatcher

    recognizer, _ = measure(
        "Load WhisperRecognizer",
        WhisperRecognizer,
        cfg.whisper_model_size,
        cfg.whisper_model_dir,
        device=cfg.whisper_device,
    )
    matcher, _ = measure(
        "Load SentenceMatcher",
        SentenceMatcher,
        phrases,
        cache_folder=str(cfg.sbert_model_dir),
        device=cfg.whisper_device,
    )

    dummy_audio = np.random.randn(cfg.sample_rate * 3).astype(np.float32) * 0.02
    _, _ = measure("ASR transcribe (3s audio)", recognizer.transcribe, dummy_audio)
    _, _ = measure("SBERT best match", matcher.find_best_match, "alter course to starboard")

    print("=" * 60)
    print("Benchmark done.")


if __name__ == "__main__":
    main()
