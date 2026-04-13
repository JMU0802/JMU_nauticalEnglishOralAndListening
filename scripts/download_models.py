"""一键下载 AI 模型到 models/ 目录

用法：
    python scripts/download_models.py [--model tiny|small|medium|large-v3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))


def download_whisper(model_size: str = "large-v3") -> None:
    from faster_whisper import WhisperModel  # noqa: PLC0415

    dest = ROOT / "models" / "whisper"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"[Whisper] Downloading '{model_size}' to {dest} ...")
    WhisperModel(model_size, device="cpu", download_root=str(dest))
    print("[Whisper] Done.")


def download_sbert(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> None:
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    dest = ROOT / "models" / "sbert"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"[SBERT] Downloading '{model_name}' to {dest} ...")
    SentenceTransformer(model_name, cache_folder=str(dest))
    print("[SBERT] Done.")


def download_tts(model_name: str = "tts_models/en/ljspeech/glow-tts") -> None:
    from TTS.api import TTS  # noqa: PLC0415

    print(f"[TTS] Downloading '{model_name}' ...")
    TTS(model_name=model_name, progress_bar=True)
    print("[TTS] Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download AI models for offline use.")
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["tiny", "small", "medium", "large", "large-v3"],
        help="Whisper model size (default: large-v3)",
    )
    parser.add_argument(
        "--skip-tts", action="store_true", help="Skip TTS model download"
    )
    args = parser.parse_args()

    download_whisper(args.model)
    download_sbert()
    if not args.skip_tts:
        download_tts()

    print("\n✅ All models downloaded successfully.")


if __name__ == "__main__":
    main()
