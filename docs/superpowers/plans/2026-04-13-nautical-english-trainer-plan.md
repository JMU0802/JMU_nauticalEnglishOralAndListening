# 航海英语听说训练系统 — 阶段性实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一套基于 Python + PyQt6 的离线航海英语听说训练系统，涵盖 ASR 识别、SMCP 语料匹配、评分反馈和 TTS 播报四大核心功能。

**Architecture:** 分层架构——UI 层（PyQt6）→ 业务逻辑层（TrainingSession）→ AI 引擎层（ASR/NLP/TTS）→ 数据层（SQLite）。各层通过明确接口解耦，支持独立测试。

**Tech Stack:** Python 3.11+, PyQt6, faster-whisper, sentence-transformers, Coqui TTS (XTTS-v2), SQLAlchemy, SQLite, jiwer, sounddevice, pytest

---

## 总体里程碑

| 阶段 | Sprint | 周期 | 交付物 |
|------|--------|------|--------|
| Phase 1 | Sprint 1-2 | 第 1-2 周 | 开发环境 + 音频录制 + ASR 最小可用版 |
| Phase 2 | Sprint 3-4 | 第 3-4 周 | SMCP 语料库 + 句子匹配 + 评分引擎 |
| Phase 3 | Sprint 5-6 | 第 5-6 周 | TTS 集成 + 反馈模块 + 训练会话逻辑 |
| Phase 4 | Sprint 7-8 | 第 7-8 周 | 完整 PyQt6 UI（学生端 + 管理端） |
| Phase 5 | Sprint 9-10 | 第 9-10 周 | 性能优化 + Windows 打包 + 测试覆盖 |

---

## Phase 1：基础设施 + ASR（第 1-2 周）

**目标：** 能录音、能识别、有基础窗口。

### Task 1.1：开发环境配置

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`

- [ ] **Step 1: 创建 `pyproject.toml`**

```toml
[project]
name = "nautical-english-trainer"
version = "0.1.0"
requires-python = ">=3.11"
```

- [ ] **Step 2: 创建 `requirements.txt`（核心依赖）**

```
PyQt6>=6.7.0
faster-whisper>=1.0.3
sentence-transformers>=3.0.0
TTS>=0.22.0
SQLAlchemy>=2.0.0
jiwer>=3.0.0
sounddevice>=0.4.6
soundfile>=0.12.1
numpy>=1.26.0
```

- [ ] **Step 3: 创建 `requirements-dev.txt`（开发依赖）**

```
pytest>=8.0.0
pytest-qt>=4.4.0
pytest-cov>=5.0.0
ruff>=0.4.0
pyinstaller>=6.0.0
```

- [ ] **Step 4: 初始化 git 仓库**

```bash
git init
git add pyproject.toml requirements.txt requirements-dev.txt .gitignore
git commit -m "chore: init project structure"
```

- [ ] **Step 5: 安装依赖并验证**

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -c "import faster_whisper; import PyQt6; print('OK')"
```

---

### Task 1.2：全局配置模块

**Files:**
- Create: `src/nautical_english/config.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_config.py
from nautical_english.config import AppConfig

def test_whisper_model_path_exists():
    cfg = AppConfig()
    assert cfg.whisper_model_size in ("tiny", "small", "medium", "large-v3")

def test_db_path_is_absolute():
    cfg = AppConfig()
    assert cfg.db_path.is_absolute()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd src && pytest ../tests/test_config.py -v
```

- [ ] **Step 3: 实现 `config.py`**

```python
from pathlib import Path
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
CORPUS_DIR = BASE_DIR / "corpus"

@dataclass
class AppConfig:
    whisper_model_size: str = "large-v3"
    whisper_model_dir: Path = field(default_factory=lambda: MODELS_DIR / "whisper")
    tts_model_dir: Path = field(default_factory=lambda: MODELS_DIR / "tts")
    db_path: Path = field(default_factory=lambda: CORPUS_DIR / "db" / "corpus.db")
    sample_rate: int = 16000
    max_record_seconds: int = 30
    score_alpha: float = 0.6   # 语义相似度权重
    score_beta: float = 0.4    # WER 权重
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd src && pytest ../tests/test_config.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/nautical_english/config.py tests/test_config.py
git commit -m "feat: add AppConfig with model and db path config"
```

---

### Task 1.3：音频录制模块

**Files:**
- Create: `src/nautical_english/asr/audio_capture.py`
- Test: `tests/test_asr/test_audio_capture.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_asr/test_audio_capture.py
import numpy as np
from nautical_english.asr.audio_capture import AudioCapture

def test_audio_capture_creates_instance():
    cap = AudioCapture(sample_rate=16000)
    assert cap.sample_rate == 16000

def test_get_available_devices_returns_list():
    cap = AudioCapture()
    devices = cap.get_available_devices()
    assert isinstance(devices, list)
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `audio_capture.py`**（见 Task 1.3 实现细节）

```python
import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path

class AudioCapture:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._recording: np.ndarray | None = None

    def get_available_devices(self) -> list[dict]:
        devices = sd.query_devices()
        return [{"index": i, "name": d["name"]} 
                for i, d in enumerate(devices) if d["max_input_channels"] > 0]

    def record(self, duration: float) -> np.ndarray:
        audio = sd.rec(int(duration * self.sample_rate),
                       samplerate=self.sample_rate, channels=1, dtype="float32")
        sd.wait()
        self._recording = audio.flatten()
        return self._recording

    def save(self, path: Path) -> None:
        if self._recording is None:
            raise ValueError("No recording available")
        sf.write(str(path), self._recording, self.sample_rate)
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(asr): add AudioCapture with sounddevice backend"
```

---

### Task 1.4：ASR 识别模块（Whisper）

**Files:**
- Create: `src/nautical_english/asr/recognizer.py`
- Test: `tests/test_asr/test_recognizer.py`
- Create: `scripts/download_models.py`

- [ ] **Step 1: 编写失败测试（使用 mock）**

```python
# tests/test_asr/test_recognizer.py
from unittest.mock import MagicMock, patch
from nautical_english.asr.recognizer import WhisperRecognizer

def test_recognizer_transcribe_returns_string():
    with patch("nautical_english.asr.recognizer.WhisperModel") as MockModel:
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = (
            [MagicMock(text=" alter course to starboard")], {}
        )
        MockModel.return_value = mock_instance
        rec = WhisperRecognizer(model_size="tiny", model_dir=None)
        result = rec.transcribe(b"fake_audio_bytes")
        assert isinstance(result, str)
        assert "starboard" in result.lower()
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `recognizer.py`**

```python
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

# SMCP 专业术语提示词，提升识别准确率
MARITIME_PROMPT = (
    "Maritime English, SMCP. "
    "Terms: starboard, port, bow, stern, bearing, course, vessel, "
    "collision, distress, mayday, navigating, anchoring, mooring."
)

class WhisperRecognizer:
    def __init__(self, model_size: str = "large-v3",
                 model_dir: Path | None = None,
                 device: str = "auto"):
        self._model = WhisperModel(
            model_size,
            device=device,
            download_root=str(model_dir) if model_dir else None,
        )

    def transcribe(self, audio: np.ndarray | str | Path) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language="en",
            initial_prompt=MARITIME_PROMPT,
            beam_size=5,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
```

- [ ] **Step 4: 创建 `scripts/download_models.py`**

```python
"""一键下载所需 AI 模型到 models/ 目录"""
from pathlib import Path
from faster_whisper import WhisperModel

MODELS_DIR = Path(__file__).parent.parent / "models"

def download_whisper(model_size: str = "large-v3"):
    print(f"Downloading Whisper {model_size}...")
    WhisperModel(model_size, download_root=str(MODELS_DIR / "whisper"))
    print("Done.")

if __name__ == "__main__":
    download_whisper()
```

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git commit -m "feat(asr): add WhisperRecognizer with maritime prompt"
```

---

### Task 1.5：最小 PyQt6 主窗口

**Files:**
- Create: `src/main.py`
- Create: `src/nautical_english/ui/main_window.py`

- [ ] **Step 1: 实现最小主窗口**

```python
# src/nautical_english/ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maritime English Trainer — JMU")
        self.setMinimumSize(1024, 768)
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Maritime English Trainer\n(UI loading...)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
```

- [ ] **Step 2: 实现入口 `src/main.py`**

```python
import sys
from PyQt6.QtWidgets import QApplication
from nautical_english.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 手动启动验证窗口可打开**

```bash
cd src && python main.py
```

- [ ] **Step 4: 提交**

```bash
git commit -m "feat(ui): add minimal MainWindow scaffold"
```

---

## Phase 2：语料库 + NLP 匹配 + 评分（第 3-4 周）

**目标：** SMCP 语料入库，句子匹配和评分可用。

### Task 2.1：数据库 ORM 模型

**Files:**
- Create: `src/nautical_english/corpus/models.py`
- Test: `tests/test_corpus/test_models.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_corpus/test_models.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from nautical_english.corpus.models import Base, Category, Phrase

def test_create_tables_and_insert():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        cat = Category(name_en="Navigation", name_zh="航行")
        session.add(cat)
        session.flush()
        phrase = Phrase(category_id=cat.id,
                        phrase_en="Alter course to starboard",
                        phrase_zh="向右转向", difficulty=1)
        session.add(phrase)
        session.commit()
        result = session.query(Phrase).first()
        assert result.phrase_en == "Alter course to starboard"
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `models.py`**

```python
from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100))
    name_zh: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    phrases: Mapped[list["Phrase"]] = relationship(back_populates="category")

class Phrase(Base):
    __tablename__ = "phrases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    phrase_en: Mapped[str] = mapped_column(Text)
    phrase_zh: Mapped[str] = mapped_column(Text)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    audio_path: Mapped[str | None] = mapped_column(String(500))
    category: Mapped["Category"] = relationship(back_populates="phrases")

class TrainingRecord(Base):
    __tablename__ = "training_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(100))
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id"))
    recognized_text: Mapped[str] = mapped_column(Text)
    wer_score: Mapped[float] = mapped_column(Float)
    similarity_score: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(corpus): add SQLAlchemy ORM models"
```

---

### Task 2.2：语料库数据访问层

**Files:**
- Create: `src/nautical_english/corpus/repository.py`
- Test: `tests/test_corpus/test_repository.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_corpus/test_repository.py
import pytest
from nautical_english.corpus.repository import CorpusRepository

@pytest.fixture
def repo():
    return CorpusRepository(db_url="sqlite:///:memory:", seed=True)

def test_get_all_phrases_returns_list(repo):
    phrases = repo.get_all_phrases()
    assert len(phrases) > 0

def test_get_phrases_by_difficulty(repo):
    easy = repo.get_phrases_by_difficulty(1)
    assert all(p.difficulty == 1 for p in easy)

def test_save_training_record(repo):
    phrases = repo.get_all_phrases()
    record_id = repo.save_training_record(
        student_id="test_student",
        phrase_id=phrases[0].id,
        recognized_text="alter course to starboard",
        wer_score=0.1,
        similarity_score=0.95,
        overall_score=87.0,
    )
    assert record_id > 0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `repository.py`**（含内存初始化种子数据逻辑）

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(corpus): add CorpusRepository with CRUD operations"
```

---

### Task 2.3：SMCP 种子数据

**Files:**
- Create: `src/nautical_english/corpus/seed_data.py`
- Create: `scripts/seed_corpus.py`

- [ ] **Step 1: 在 `seed_data.py` 整理第一批 SMCP 标准句（≥50条）**

覆盖以下场景类别：
  - Navigation & Maneuvering（航行与机动）
  - Distress & Urgency（遇险与紧急）
  - Collision Avoidance（避碰）
  - Anchoring & Mooring（锚泊与系泊）
  - VHF Communication（甚高频通信）

- [ ] **Step 2: 运行 `scripts/seed_corpus.py` 写入数据库**

```bash
python scripts/seed_corpus.py
```

- [ ] **Step 3: 验证数据库行数**

```python
python -c "
from nautical_english.corpus.repository import CorpusRepository
r = CorpusRepository()
print(len(r.get_all_phrases()), 'phrases loaded')
"
```

- [ ] **Step 4: 提交**

```bash
git commit -m "feat(corpus): add SMCP seed data (50+ phrases)"
```

---

### Task 2.4：句子匹配模块（SBERT）

**Files:**
- Create: `src/nautical_english/nlp/matcher.py`
- Test: `tests/test_nlp/test_matcher.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_nlp/test_matcher.py
from nautical_english.nlp.matcher import SentenceMatcher

PHRASES = [
    "Alter course to starboard",
    "Keep clear of me",
    "What are your intentions",
    "I am on fire and require assistance",
]

def test_best_match_finds_correct_phrase():
    matcher = SentenceMatcher(phrases=PHRASES)
    result = matcher.find_best_match("turn right immediately")
    assert result.phrase == "Alter course to starboard"
    assert result.score > 0.5

def test_similarity_score_is_normalized():
    matcher = SentenceMatcher(phrases=PHRASES)
    result = matcher.find_best_match("Alter course to starboard")
    assert 0.0 <= result.score <= 1.0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `matcher.py`**

```python
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

@dataclass
class MatchResult:
    phrase: str
    score: float
    index: int

class SentenceMatcher:
    def __init__(self, phrases: list[str],
                 model_name: str = MODEL_NAME):
        self._model = SentenceTransformer(model_name)
        self._phrases = phrases
        self._embeddings = self._model.encode(phrases, normalize_embeddings=True)

    def find_best_match(self, query: str) -> MatchResult:
        q_emb = self._model.encode([query], normalize_embeddings=True)
        scores = (self._embeddings @ q_emb.T).flatten()
        idx = int(np.argmax(scores))
        return MatchResult(phrase=self._phrases[idx],
                           score=float(scores[idx]),
                           index=idx)
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(nlp): add SentenceMatcher with SBERT embeddings"
```

---

### Task 2.5：评分模块

**Files:**
- Create: `src/nautical_english/nlp/scorer.py`
- Test: `tests/test_nlp/test_scorer.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_nlp/test_scorer.py
from nautical_english.nlp.scorer import PhraseScorer

def test_perfect_match_scores_high():
    scorer = PhraseScorer()
    score = scorer.compute(
        recognized="alter course to starboard",
        reference="Alter course to starboard",
        similarity=0.99,
    )
    assert score.overall >= 90

def test_wrong_direction_scores_lower():
    scorer = PhraseScorer()
    score = scorer.compute(
        recognized="alter course to port",
        reference="Alter course to starboard",
        similarity=0.65,
    )
    assert score.overall < 80

def test_score_is_in_range():
    scorer = PhraseScorer()
    score = scorer.compute("random noise words", "Mayday mayday mayday", 0.1)
    assert 0 <= score.overall <= 100
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `scorer.py`**

```python
from dataclasses import dataclass
import jiwer

GRADE_MAP = [
    (90, "Excellent", "Perfect! Standard pronunciation."),
    (70, "Good",      "Good attempt. Minor errors detected."),
    (50, "Fair",      "Partially correct. Keep practicing."),
    (0,  "Poor",      "Incorrect. Please try again."),
]

@dataclass
class ScoreResult:
    wer: float
    similarity: float
    overall: float
    grade: str
    feedback_en: str

class PhraseScorer:
    def __init__(self, alpha: float = 0.6, beta: float = 0.4):
        self.alpha = alpha
        self.beta = beta

    def compute(self, recognized: str, reference: str, similarity: float) -> ScoreResult:
        wer = jiwer.wer(reference.lower(), recognized.lower())
        wer = min(wer, 1.0)
        overall = 100 * (self.alpha * similarity + self.beta * (1 - wer))
        overall = round(max(0.0, min(100.0, overall)), 1)
        grade, feedback = next(
            (g, f) for threshold, g, f in GRADE_MAP if overall >= threshold
        )
        return ScoreResult(wer=wer, similarity=similarity,
                           overall=overall, grade=grade, feedback_en=feedback)
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(nlp): add PhraseScorer with WER + similarity fusion"
```

---

## Phase 3：TTS + 反馈 + 训练会话（第 5-6 周）

**目标：** 端到端管道可运行（语音 → 识别 → 匹配 → 评分 → 反馈 → 朗读）。

### Task 3.1：TTS 合成模块

**Files:**
- Create: `src/nautical_english/tts/synthesizer.py`
- Test: `tests/test_tts/test_synthesizer.py`

- [ ] **Step 1: 编写失败测试（mock TTS 模型）**

```python
from unittest.mock import patch, MagicMock
from nautical_english.tts.synthesizer import TTSSynthesizer

def test_synthesize_returns_audio_path(tmp_path):
    with patch("nautical_english.tts.synthesizer.TTS") as MockTTS:
        mock_tts = MagicMock()
        MockTTS.return_value = mock_tts
        synth = TTSSynthesizer()
        out_path = tmp_path / "output.wav"
        synth.synthesize("Alter course to starboard", out_path)
        mock_tts.tts_to_file.assert_called_once()
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `synthesizer.py`**

```python
from pathlib import Path
from TTS.api import TTS

DEFAULT_MODEL = "tts_models/en/ljspeech/glow-tts"

class TTSSynthesizer:
    def __init__(self, model_name: str = DEFAULT_MODEL,
                 model_dir: Path | None = None):
        self._tts = TTS(model_name=model_name, progress_bar=False)

    def synthesize(self, text: str, output_path: Path) -> Path:
        self._tts.tts_to_file(text=text, file_path=str(output_path))
        return output_path
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(tts): add TTSSynthesizer with Coqui TTS backend"
```

---

### Task 3.2：反馈生成模块

**Files:**
- Create: `src/nautical_english/feedback/generator.py`
- Test: `tests/test_feedback/test_generator.py`

- [ ] **Step 1: 编写失败测试**

```python
from nautical_english.feedback.generator import FeedbackGenerator
from nautical_english.nlp.scorer import ScoreResult

def test_feedback_contains_standard_phrase():
    gen = FeedbackGenerator()
    score = ScoreResult(wer=0.2, similarity=0.85, overall=75.0,
                        grade="Good", feedback_en="Good attempt.")
    fb = gen.generate(
        recognized="alter course port",
        reference="Alter course to starboard",
        score=score,
        reference_zh="向右转向",
    )
    assert "starboard" in fb.standard_phrase_en
    assert fb.score_display == "75.0 / 100"
    assert fb.grade == "Good"

def test_feedback_highlights_errors():
    gen = FeedbackGenerator()
    score = ScoreResult(wer=0.5, similarity=0.4, overall=46.0,
                        grade="Poor", feedback_en="Incorrect.")
    fb = gen.generate("wrong text", "Keep clear of me", score, "让开")
    assert len(fb.error_words) > 0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 `generator.py`**

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(feedback): add FeedbackGenerator with error highlighting"
```

---

### Task 3.3：训练会话编排器

**Files:**
- Create: `src/nautical_english/training/session.py`

- [ ] **Step 1: 实现 `TrainingSession`（串联 ASR → NLP → 反馈 → TTS）**

```python
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class SessionResult:
    recognized_text: str
    matched_phrase: str
    feedback: object  # FeedbackResult
    tts_audio_path: Path | None

class TrainingSession:
    """编排一次完整的"录音→识别→匹配→评分→反馈→朗读"流程"""

    def __init__(self, recognizer, matcher, scorer, feedback_gen, synthesizer,
                 repository, config):
        self._asr = recognizer
        self._matcher = matcher
        self._scorer = scorer
        self._feedback = feedback_gen
        self._tts = synthesizer
        self._repo = repository
        self._config = config

    def run(self, audio: np.ndarray, student_id: str,
            output_dir: Path) -> SessionResult:
        text = self._asr.transcribe(audio)
        match = self._matcher.find_best_match(text)
        score = self._scorer.compute(text, match.phrase, match.score)
        feedback = self._feedback.generate(text, match.phrase, score, "")
        tts_path = output_dir / "feedback.wav"
        self._tts.synthesize(feedback.standard_phrase_en, tts_path)
        self._repo.save_training_record(
            student_id=student_id,
            phrase_id=match.index,
            recognized_text=text,
            wer_score=score.wer,
            similarity_score=score.similarity,
            overall_score=score.overall,
        )
        return SessionResult(
            recognized_text=text,
            matched_phrase=match.phrase,
            feedback=feedback,
            tts_audio_path=tts_path,
        )
```

- [ ] **Step 2: 编写集成测试（mock AI 模型）**

- [ ] **Step 3: 运行测试确认通过**

- [ ] **Step 4: 提交**

```bash
git commit -m "feat(training): add TrainingSession orchestrator"
```

---

## Phase 4：完整 PyQt6 界面（第 7-8 周）

**目标：** 学生端英文练习界面 + 管理端中文语料管理界面全部完成。

### Task 4.1：QSS 样式系统

**Files:**
- Create: `src/nautical_english/ui/resources/styles.qss`

- [ ] **Step 1: 设计深海主题配色**

```css
/* Ocean Blue Theme */
QMainWindow { background-color: #0A1628; }
QPushButton#recordBtn {
    background-color: #E74C3C; border-radius: 30px;
    color: white; font-size: 16px; min-width: 60px; min-height: 60px;
}
QPushButton#recordBtn:hover { background-color: #C0392B; }
QLabel#scoreLabel { color: #F39C12; font-size: 48px; font-weight: bold; }
QLabel#gradeLabel { color: #2ECC71; font-size: 18px; }
```

- [ ] **Step 2: 在 MainWindow 中加载 QSS**

- [ ] **Step 3: 提交**

---

### Task 4.2：学生端 — 练习视图

**Files:**
- Create: `src/nautical_english/ui/student/practice_view.py`

核心 UI 元素：
- 当前练习短语展示区（大字体英文）
- 录音按钮（圆形，红色，按住录音）
- 音频波形可视化组件
- "提交"按钮

- [ ] **Step 1: 布局草图设计（文本描述）**

```
┌─────────────────────────────────────┐
│  Category: Navigation               │
│  Difficulty: ★☆☆                    │
│                                     │
│  "Alter course to starboard"        │
│  向右转向                            │
│                                     │
│       [    🎙 HOLD TO SPEAK    ]    │
│       ▁▂▃▄▅▄▃▂▁  (波形)           │
│                                     │
│           [Submit]                  │
└─────────────────────────────────────┘
```

- [ ] **Step 2: 实现 `PracticeView(QWidget)`**（完整 PyQt6 代码）

- [ ] **Step 3: 连接 TrainingSession 信号槽**

- [ ] **Step 4: 手动测试 UI 可交互**

- [ ] **Step 5: 提交**

```bash
git commit -m "feat(ui/student): add PracticeView with record button"
```

---

### Task 4.3：学生端 — 结果视图

**Files:**
- Create: `src/nautical_english/ui/student/result_view.py`

核心 UI 元素：
- 综合评分大字显示（0-100）
- 等级标签（Excellent / Good / Fair / Poor）
- 识别文本 vs 标准文本对比（差异高亮）
- 错误词列表
- "再练一次" / "下一题" 按钮

- [ ] **Step 1: 实现 `ResultView(QWidget)`**

- [ ] **Step 2: 实现差异高亮（使用 QTextEdit + HTML）**

- [ ] **Step 3: 提交**

```bash
git commit -m "feat(ui/student): add ResultView with diff highlighting"
```

---

### Task 4.4：学生端 — 进度视图

**Files:**
- Create: `src/nautical_english/ui/student/progress_view.py`

核心 UI 元素：
- 练习次数统计
- 近 10 次评分折线图（使用 PyQt6 QPainter 或 matplotlib 嵌入）
- 按类别正确率柱状图

- [ ] **Step 1: 实现图表组件**

- [ ] **Step 2: 连接 CorpusRepository 查询训练记录**

- [ ] **Step 3: 提交**

```bash
git commit -m "feat(ui/student): add ProgressView with charts"
```

---

### Task 4.5：管理端 — 语料管理

**Files:**
- Create: `src/nautical_english/ui/admin/corpus_manager.py`

核心 UI 元素（中文界面）：
- 短语列表（QTableView + SQLAlchemy）
- 添加/编辑/删除短语
- 按类别筛选
- 导入 CSV 功能

- [ ] **Step 1: 实现语料管理界面**

- [ ] **Step 2: 提交**

```bash
git commit -m "feat(ui/admin): add CorpusManager with CRUD table"
```

---

### Task 4.6：主窗口路由集成

**Files:**
- Modify: `src/nautical_english/ui/main_window.py`

- [ ] **Step 1: 实现 Tab 切换（学生端/管理端）**

- [ ] **Step 2: 实现依赖注入（将 TrainingSession 注入视图）**

- [ ] **Step 3: 集成测试主窗口各页面可切换**

- [ ] **Step 4: 提交**

```bash
git commit -m "feat(ui): integrate all views into MainWindow with tabs"
```

---

## Phase 5：优化 + 打包 + 测试覆盖（第 9-10 周）

**目标：** 可交付的 Windows 安装包，测试覆盖率 ≥ 70%。

### Task 5.1：性能优化

- [ ] **Step 1: 将 ASR 和 TTS 移入 QThread，避免 UI 冻结**

```python
class ASRWorker(QThread):
    result_ready = pyqtSignal(str)
    def run(self):
        text = self._recognizer.transcribe(self._audio)
        self.result_ready.emit(text)
```

- [ ] **Step 2: 添加加载动画（QMovie 或自绘）**

- [ ] **Step 3: 提交**

---

### Task 5.2：Windows 打包

**Files:**
- Create: `scripts/build_installer.py`
- Create: `nautical_trainer.spec`（PyInstaller spec）

- [ ] **Step 1: 编写 PyInstaller spec 文件**

```python
# nautical_trainer.spec
block_cipher = None
a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("corpus/db/*.db", "corpus/db"),
        ("assets", "assets"),
        ("src/nautical_english/ui/resources/*.qss", "nautical_english/ui/resources"),
    ],
    ...
)
```

- [ ] **Step 2: 构建并验证 exe 可独立运行**

```bash
python scripts/build_installer.py
dist\nautical_english_trainer\nautical_english_trainer.exe
```

- [ ] **Step 3: 提交**

```bash
git commit -m "build: add PyInstaller spec for Windows packaging"
```

---

### Task 5.3：测试覆盖率检查

- [ ] **Step 1: 运行全量测试 + 覆盖率报告**

```bash
pytest tests/ --cov=src/nautical_english --cov-report=html -v
```

- [ ] **Step 2: 确认覆盖率 ≥ 70%**

- [ ] **Step 3: 补充缺失的边界情况测试**

- [ ] **Step 4: 提交**

```bash
git commit -m "test: achieve 70%+ coverage across all modules"
```

---

### Task 5.4：用户手册

**Files:**
- Create: `docs/user_manual/README_student.md`（英文，学生用）
- Create: `docs/user_manual/README_admin.md`（中文，教师用）

- [ ] **Step 1: 撰写学生操作手册（安装 → 练习流程 → 查看成绩）**

- [ ] **Step 2: 撰写管理员手册（导入语料 → 查看统计 → 模型管理）**

- [ ] **Step 3: 提交**

```bash
git commit -m "docs: add user manual for student and admin"
```

---

## 附录 A：技术依赖版本锁定

```
Python        3.11+
PyQt6         6.7.x
faster-whisper 1.0.3+
Whisper 模型   large-v3（离线，约 3GB）
sentence-transformers 3.x
  - 模型：paraphrase-multilingual-MiniLM-L12-v2
TTS (Coqui)   0.22.x
  - 模型：tts_models/en/ljspeech/glow-tts
SQLAlchemy    2.0.x
jiwer         3.0.x
sounddevice   0.4.6+
PyInstaller   6.x
```

---

## 附录 B：目录与职责速查

| 路径 | 职责 |
|------|------|
| `src/nautical_english/config.py` | 全局配置（路径、超参数） |
| `src/nautical_english/asr/` | 录音 + Whisper 识别 |
| `src/nautical_english/tts/` | Coqui TTS 合成 |
| `src/nautical_english/nlp/` | SBERT 匹配 + 评分 |
| `src/nautical_english/corpus/` | SQLite ORM + 数据访问 + 种子数据 |
| `src/nautical_english/feedback/` | 反馈文本生成 |
| `src/nautical_english/training/` | 端到端训练流程编排 |
| `src/nautical_english/ui/` | PyQt6 界面（学生端 + 管理端） |
| `tests/` | pytest 单元/集成测试 |
| `scripts/` | 模型下载、语料初始化、打包脚本 |
| `docs/superpowers/` | 设计规范 + 实施计划 |
