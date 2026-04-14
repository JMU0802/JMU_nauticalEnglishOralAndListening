"""完整训练流程演示脚本

功能：
  1. 从 corpus.db 随机选一个 SMCP 短语
  2. 播报提示（用 TTS 或打印文字）
  3. 录音 / 使用指定音频文件
  4. 运行 ASR → SBERT 匹配 → 评分 → 反馈 → TTS 回馈 完整 pipeline
  5. 打印结果报告

用法：
    python scripts/demo_session.py
        默认：从 corpus.db 随机选取一个带音频的短语，用其 MP3 作为"学员"输入

    python scripts/demo_session.py --audio path/to/audio.mp3
        使用指定音频文件

    python scripts/demo_session.py --mic --duration 5
        从默认麦克风录音 5 秒

    python scripts/demo_session.py --phrase-id 10
        指定练习 corpus.db id=10 的短语（随机音频输入）
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Windows 终端强制 UTF-8，以支持中文和 emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from nautical_english.config import AppConfig
from nautical_english.asr.recognizer import WhisperRecognizer
from nautical_english.corpus.repository import CorpusRepository
from nautical_english.feedback.generator import FeedbackGenerator
from nautical_english.nlp.matcher import SentenceMatcher
from nautical_english.nlp.scorer import PhraseScorer


# ── ANSI 颜色 ─────────────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED   = "\033[91m"
_CYAN  = "\033[96m"


def _grade_color(grade: str) -> str:
    return {
        "Excellent": _GREEN,
        "Good":      _GREEN,
        "Fair":      _YELLOW,
        "Poor":      _RED,
    }.get(grade, _RESET)


# ── 加载组件 ──────────────────────────────────────────────────────────────────

def load_components(cfg: AppConfig):
    """加载所有模型组件，返回 (recognizer, repo, matcher, scorer, feedback_gen, tts?)。"""

    print(f"{_CYAN}[1/4] 连接语料库数据库...{_RESET}")
    repo = CorpusRepository()
    phrases = repo.get_all_phrases()
    if not phrases:
        print("❌ corpus.db 中没有短语数据！请先运行 import_smcp_audio.py")
        sys.exit(1)
    print(f"      ✅ {len(phrases)} 条短语可用")

    phrase_texts = [p.phrase_en for p in phrases]

    print(f"{_CYAN}[2/4] 加载 SBERT 语义匹配模型...{_RESET}")
    t0 = time.time()
    matcher = SentenceMatcher(
        phrase_texts,
        cache_folder=str(cfg.sbert_model_dir),
    )
    print(f"      ✅ {len(phrase_texts)} 条短语向量已预计算 ({time.time()-t0:.1f}s)")

    print(f"{_CYAN}[3/4] 加载 Whisper ASR 模型...{_RESET}")
    t0 = time.time()
    recognizer = WhisperRecognizer(
        cfg.whisper_model_size, cfg.whisper_model_dir, device="cpu"
    )
    print(f"      ✅ Whisper {cfg.whisper_model_size} 加载完成 ({time.time()-t0:.1f}s)")

    scorer = PhraseScorer()
    feedback_gen = FeedbackGenerator()

    print(f"{_CYAN}[4/4] TTS 合成器（可选）...{_RESET}")
    tts = None
    try:
        from nautical_english.tts.synthesizer import TTSSynthesizer  # noqa: PLC0415
        tts = TTSSynthesizer()
        print(f"      ✅ TTS 已加载")
    except ImportError:
        print(f"      ⚠️  TTS 未安装（跳过），只显示文字反馈")
    except Exception as e:
        print(f"      ⚠️  TTS 加载失败：{e}（跳过）")

    return recognizer, repo, matcher, scorer, feedback_gen, tts, phrases


# ── 获取音频 ──────────────────────────────────────────────────────────────────

def get_audio(
    args: argparse.Namespace,
    phrases,
) -> tuple[str | Path, "Phrase"]:  # type: ignore[name-defined]
    """返回 (音频文件路径或 ndarray, 目标短语对象)。"""

    from nautical_english.corpus.models import Phrase

    if args.phrase_id:
        target = next((p for p in phrases if p.id == args.phrase_id), None)
        if target is None:
            print(f"❌ 找不到 phrase_id={args.phrase_id}")
            sys.exit(1)
    else:
        # 随机选取有音频的短语
        candidates = [p for p in phrases if p.audio_path]
        if not candidates:
            candidates = phrases
        target = random.choice(candidates)

    if args.audio:
        audio_input: str | Path = Path(args.audio)
    elif args.mic:
        from nautical_english.asr.audio_capture import AudioCapture
        cap = AudioCapture()
        print(f"\n{_BOLD}🎙  请朗读以下标准短语（{args.duration} 秒）：{_RESET}")
        print(f"\n   {_BOLD}{_CYAN}{target.phrase_en}{_RESET}\n")
        print("   录音开始...")
        audio_input = cap.record(args.duration)
        print("   ✅ 录音结束")
    elif target.audio_path:
        audio_path = ROOT / target.audio_path
        if not audio_path.exists():
            print(f"❌ 音频文件不存在: {audio_path}")
            sys.exit(1)
        audio_input = audio_path
        print(f"\n{_BOLD}📢  演示模式：使用参考音频{_RESET}")
        print(f"   目标短语: {_BOLD}{_CYAN}{target.phrase_en}{_RESET}")
        print(f"   音频文件: {audio_path.name}")
    else:
        print("❌ 无法获取音频（短语无音频路径，且未指定 --audio 或 --mic）")
        sys.exit(1)

    return audio_input, target


# ── 主流程 ────────────────────────────────────────────────────────────────────

def run_demo(args: argparse.Namespace) -> None:
    cfg = AppConfig()

    print(f"\n{'='*60}")
    print(f"{_BOLD}  航海英语口语训练系统 — 演示{_RESET}")
    print(f"{'='*60}\n")

    recognizer, repo, matcher, scorer, feedback_gen, tts, phrases = load_components(cfg)

    print()
    audio_input, target_phrase = get_audio(args, phrases)

    # ── 运行 pipeline ──────────────────────────────────────────────────────────
    print(f"\n{_CYAN}--- 运行评估 pipeline ---{_RESET}")

    print("  1. ASR 语音识别...", end=" ", flush=True)
    t0 = time.time()
    recognized = recognizer.transcribe(audio_input)
    print(f"({time.time()-t0:.1f}s)")
    print(f"     识别结果: {_BOLD}{recognized!r}{_RESET}")

    print("  2. SBERT 语义匹配...", end=" ", flush=True)
    t0 = time.time()
    match = matcher.find_best_match(recognized)
    print(f"({time.time()-t0:.1f}s)")
    print(f"     最佳匹配: {_BOLD}{match.phrase!r}{_RESET} (similarity={match.score:.3f})")

    print("  3. 评分计算...", end=" ", flush=True)
    score = scorer.compute(recognized, match.phrase, match.score)
    grade_c = _grade_color(score.grade)
    print(f"({grade_c}{score.grade}{_RESET})")

    feedback = feedback_gen.generate(recognized, match.phrase, score, "")

    output_dir = ROOT / "output" / "demo"
    tts_path = None
    if tts:
        print("  4. TTS 生成反馈音频...", end=" ", flush=True)
        t0 = time.time()
        tts_path = tts.synthesize(match.phrase, output_dir / "feedback.wav")
        print(f"({time.time()-t0:.1f}s) → {tts_path.name}")

    # ── 显示报告 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"{_BOLD}  评估报告{_RESET}")
    print(f"{'='*60}")
    print(f"  目标短语  : {_BOLD}{target_phrase.phrase_en}{_RESET}")
    print(f"  识别文本  : {_BOLD}{recognized}{_RESET}")
    print(f"  最佳匹配  : {match.phrase}")
    print(f"  语义相似度: {match.score:.3f}")
    print(f"  WER       : {score.wer:.3f}")
    print(f"  综合得分  : {grade_c}{_BOLD}{score.overall:.1f} / 100{_RESET}")
    print(f"  等级      : {grade_c}{_BOLD}{score.grade}{_RESET}")
    if feedback.error_words:
        print(f"  错误词    : {_RED}{', '.join(feedback.error_words)}{_RESET}")
    print(f"  反馈      : {feedback.feedback_en}")
    if tts_path:
        print(f"  TTS 音频  : {tts_path}")
    print(f"{'='*60}\n")

    # 保存演示记录到 DB
    try:
        repo.save_training_record(
            student_id="demo_user",
            phrase_id=target_phrase.id,
            recognized_text=recognized,
            wer_score=score.wer,
            similarity_score=score.similarity,
            overall_score=score.overall,
        )
        print(f"  ✅ 训练记录已保存到数据库")
    except Exception as e:
        print(f"  ⚠️  记录保存失败: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="航海英语口语训练系统 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audio", metavar="FILE", help="指定音频文件（mp3/wav）")
    group.add_argument("--mic", action="store_true", help="从麦克风录音")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="麦克风录音时长（秒，默认 5）")
    parser.add_argument("--phrase-id", type=int, metavar="ID",
                        help="指定 corpus.db 中的短语 ID")
    args = parser.parse_args()

    run_demo(args)


if __name__ == "__main__":
    main()
