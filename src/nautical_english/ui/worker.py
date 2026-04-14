"""后台工作线程 — 在 QThread 中运行耗时的 AI 推理管道

避免 UI 卡顿：AudioCapture → WhisperRecognizer → SentenceMatcher
→ PhraseScorer → FeedbackGenerator → (可选 TTS) 全部在工作线程运行。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class ModelLoader(QThread):
    """启动时异步加载所有 AI 模型，完成后发信号。"""

    progress = pyqtSignal(str)   # status message
    finished = pyqtSignal(object, object, object, object, object)
    # finished(recognizer, matcher, scorer, feedback_gen, synthesizer)
    error = pyqtSignal(str)

    def __init__(
        self,
        cfg,
        phrase_texts: list[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._cfg = cfg
        self._phrase_texts = phrase_texts

    def run(self) -> None:
        try:
            import sys
            from pathlib import Path as P
            root = P(__file__).parent.parent.parent.parent
            if str(root / "src") not in sys.path:
                sys.path.insert(0, str(root / "src"))

            self.progress.emit("Loading SBERT model...")
            from nautical_english.nlp.matcher import SentenceMatcher
            import torch

            sbert_device = self._cfg.whisper_device
            if sbert_device == "auto":
                sbert_device = "cuda" if torch.cuda.is_available() else "cpu"

            matcher = SentenceMatcher(
                self._phrase_texts,
                cache_folder=str(self._cfg.sbert_model_dir),
                device=sbert_device,
            )

            self.progress.emit("Loading Whisper ASR model...")
            from nautical_english.asr.recognizer import WhisperRecognizer
            recognizer = WhisperRecognizer(
                self._cfg.whisper_model_size,
                self._cfg.whisper_model_dir,
                device=self._cfg.whisper_device,
            )

            self.progress.emit("Initializing scorer & feedback...")
            from nautical_english.nlp.scorer import PhraseScorer
            from nautical_english.feedback.generator import FeedbackGenerator
            from nautical_english.tts.synthesizer import TTSSynthesizer
            scorer = PhraseScorer()
            feedback_gen = FeedbackGenerator()
            try:
                synthesizer = TTSSynthesizer(model_name=self._cfg.tts_model_name)
            except Exception:  # noqa: BLE001
                synthesizer = TTSSynthesizer.__new__(TTSSynthesizer)
                synthesizer._backend = "none"
                synthesizer._tts_obj = None
                synthesizer._voice = "en-GB-RyanNeural"

            self.progress.emit("Ready.")
            self.finished.emit(recognizer, matcher, scorer, feedback_gen, synthesizer)

        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class SessionWorker(QThread):
    """对一段音频执行完整 ASR → 匹配 → 评分 → 反馈 流程。"""

    finished = pyqtSignal(object)   # SessionResult
    error    = pyqtSignal(str)

    def __init__(
        self,
        audio: np.ndarray | str | Path,
        phrase_id: int,
        recognizer,
        matcher,
        scorer,
        feedback_gen,
        synthesizer,
        repo,
        student_id: str,
        output_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._audio        = audio
        self._phrase_id    = phrase_id
        self._recognizer   = recognizer
        self._matcher      = matcher
        self._scorer       = scorer
        self._feedback_gen = feedback_gen
        self._synthesizer  = synthesizer
        self._repo         = repo
        self._student_id   = student_id
        self._output_dir   = output_dir

    def run(self) -> None:
        try:
            # 1. ASR
            recognized = self._recognizer.transcribe(self._audio)

            # 2. 语义匹配
            match = self._matcher.find_best_match(recognized)

            # 3. 评分
            score = self._scorer.compute(recognized, match.phrase, match.score)

            # 4. 反馈
            feedback = self._feedback_gen.generate(
                recognized, match.phrase, score, ""
            )

            tts_path = None
            if self._synthesizer is not None:
                try:
                    target = feedback.standard_phrase_en if hasattr(feedback, "standard_phrase_en") else match.phrase
                    tts_path = self._output_dir / f"{self._student_id}_{self._phrase_id}_standard.wav"
                    self._synthesizer.synthesize(target, tts_path)
                except Exception:  # noqa: BLE001
                    tts_path = None

            # 5. 持久化
            try:
                self._repo.save_training_record(
                    student_id=self._student_id,
                    phrase_id=self._phrase_id,
                    recognized_text=recognized,
                    wer_score=score.wer,
                    similarity_score=score.similarity,
                    overall_score=score.overall,
                )
            except Exception:  # noqa: BLE001
                pass  # DB 写入失败不影响 UI 显示

            from nautical_english.training.session import SessionResult
            result = SessionResult(
                recognized_text=recognized,
                matched_phrase=match.phrase,
                feedback=feedback,
                overall_score=score.overall,
                tts_audio_path=tts_path,
            )
            self.finished.emit(result)

        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))
