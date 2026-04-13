"""训练会话编排器 — 串联 ASR → NLP → 反馈 → TTS 完整流程"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nautical_english.feedback.generator import FeedbackResult


@dataclass
class SessionResult:
    """一次完整训练会话的输出。"""

    recognized_text: str
    matched_phrase: str
    feedback: FeedbackResult
    overall_score: float
    tts_audio_path: Path | None


class TrainingSession:
    """编排一次「录音 → 识别 → 匹配 → 评分 → 反馈 → 朗读」完整流程。

    所有依赖在构造时注入，便于测试时替换 mock 对象。

    Parameters
    ----------
    recognizer:
        :class:`~nautical_english.asr.recognizer.WhisperRecognizer`
    matcher:
        :class:`~nautical_english.nlp.matcher.SentenceMatcher`
    scorer:
        :class:`~nautical_english.nlp.scorer.PhraseScorer`
    feedback_gen:
        :class:`~nautical_english.feedback.generator.FeedbackGenerator`
    synthesizer:
        :class:`~nautical_english.tts.synthesizer.TTSSynthesizer`
    repository:
        :class:`~nautical_english.corpus.repository.CorpusRepository`
    phrase_zh_map:
        phrase_en → phrase_zh 映射（用于反馈）。
    """

    def __init__(
        self,
        recognizer,
        matcher,
        scorer,
        feedback_gen,
        synthesizer,
        repository,
        phrase_zh_map: dict[str, str] | None = None,
    ) -> None:
        self._asr = recognizer
        self._matcher = matcher
        self._scorer = scorer
        self._feedback = feedback_gen
        self._tts = synthesizer
        self._repo = repository
        self._phrase_zh_map: dict[str, str] = phrase_zh_map or {}

    def run(
        self,
        audio: np.ndarray | str | Path,
        student_id: str,
        output_dir: Path,
    ) -> SessionResult:
        """执行一次完整训练评估。

        Parameters
        ----------
        audio:
            学员音频（ndarray / 文件路径）。
        student_id:
            学员标识（用于记录成绩）。
        output_dir:
            TTS 反馈音频的输出目录。
        """
        # 1. ASR 识别
        recognized_text = self._asr.transcribe(audio)

        # 2. 语义匹配
        match = self._matcher.find_best_match(recognized_text)

        # 3. 评分
        score = self._scorer.compute(
            recognized_text, match.phrase, match.score
        )

        # 4. 反馈生成
        phrase_zh = self._phrase_zh_map.get(match.phrase, "")
        feedback = self._feedback.generate(
            recognized_text, match.phrase, score, phrase_zh
        )

        # 5. TTS 播报标准句
        tts_path = Path(output_dir) / f"{student_id}_feedback.wav"
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        self._tts.synthesize(feedback.standard_phrase_en, tts_path)

        # 6. 持久化训练记录
        self._repo.save_training_record(
            student_id=student_id,
            phrase_id=match.index + 1,   # 数据库 ID 从 1 开始
            recognized_text=recognized_text,
            wer_score=score.wer,
            similarity_score=score.similarity,
            overall_score=score.overall,
        )

        return SessionResult(
            recognized_text=recognized_text,
            matched_phrase=match.phrase,
            feedback=feedback,
            overall_score=score.overall,
            tts_audio_path=tts_path,
        )
