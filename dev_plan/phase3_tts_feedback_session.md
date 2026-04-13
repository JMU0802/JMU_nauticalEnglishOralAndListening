# Phase 3 开发计划 — TTS + 反馈生成 + 训练会话编排

**周期：** 第 5-6 周（Sprint 5 & 6）  
**前置条件：** Phase 2 全部验收通过，数据库中有 ≥50 条 SMCP 短语，NLP 管道冒烟测试通过。  
**目标：** 集成 TTS 语音合成，完成反馈生成模块，实现端到端训练会话编排器（无 UI）。  
**完成标准：** 在命令行可完整运行一次「录音 → 识别 → 匹配 → 评分 → 反馈 → TTS 播放」全流程，结果保存到数据库。

---

## 📦 本阶段交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| TTS 合成模块 | `src/nautical_english/tts/synthesizer.py` | Coqui TTS 封装 |
| 反馈生成模块 | `src/nautical_english/feedback/generator.py` | 结构化反馈对象 |
| 训练会话编排器 | `src/nautical_english/training/session.py` | 端到端流程 |
| 关联音频功能 | `src/nautical_english/corpus/repository.py` | SMCP_DATA 音频路径关联 |
| TTS 测试 | `tests/test_tts/` | 使用 Mock 验证 |
| 反馈测试 | `tests/test_feedback/test_generator.py` | 已存在，确认通过 |
| 集成测试 | `tests/test_training/` | TrainingSession 集成测试 |
| 命令行演示脚本 | `scripts/demo_session.py` | 端到端演示（无 UI） |

---

## 🛠️ Task 3.1 — 反馈生成模块测试

> 文件已存在：`src/nautical_english/feedback/generator.py`

### Step 1：运行现有测试

```bash
cd f:\AI_CODING\JMU_nauticalEnglishOralAndListening
pytest tests/test_feedback/ -v
```

**预期：** 5 tests passed

### Step 2：手动验证 HTML 差异输出

```python
import sys; sys.path.insert(0, "src")
from nautical_english.feedback.generator import FeedbackGenerator
from nautical_english.nlp.scorer import ScoreResult

gen = FeedbackGenerator()
score = ScoreResult(wer=0.25, similarity=0.72, overall=71.2,
                    grade="Good", feedback_en="Good attempt. Minor errors detected.")

fb = gen.generate(
    recognized="alter course to port",
    reference="Alter course to starboard",
    score=score,
    reference_zh="向右转向",
)

print(f"评分展示: {fb.score_display}")
print(f"等级:     {fb.grade}")
print(f"错误词:   {fb.error_words}")
print(f"HTML差异: {fb.diff_html}")
```

**预期输出示例：**
```
评分展示: 71.2 / 100
等级:     Good
错误词:   ['port']
HTML差异: Alter course to <span style="color:#E74C3C">port</span> <span style="color:#2ECC71">(starboard)</span>
```

### Step 3：提交

```bash
git add tests/test_feedback/
git commit -m "test: verify FeedbackGenerator diff HTML and error words"
```

---

## 🛠️ Task 3.2 — TTS 模块

> 文件已存在：`src/nautical_english/tts/synthesizer.py`

### Step 2.1：新建 TTS 测试目录

```bash
New-Item -ItemType Directory -Path tests\test_tts -Force
New-Item -ItemType File -Path tests\test_tts\__init__.py -Force
```

### Step 2.2：创建 TTS 测试文件

新建 `tests/test_tts/test_synthesizer.py`：

```python
from unittest.mock import MagicMock, patch
from pathlib import Path
from nautical_english.tts.synthesizer import TTSSynthesizer

def test_synthesizer_creates_instance():
    with patch("nautical_english.tts.synthesizer.TTS") as MockTTS:
        MockTTS.return_value = MagicMock()
        synth = TTSSynthesizer.__new__(TTSSynthesizer)
        synth._tts = MockTTS.return_value
        assert synth._tts is not None

def test_synthesize_calls_tts_to_file(tmp_path):
    with patch("nautical_english.tts.synthesizer.TTS") as MockTTS:
        mock_tts_instance = MagicMock()
        MockTTS.return_value = mock_tts_instance

        synth = TTSSynthesizer.__new__(TTSSynthesizer)
        synth._tts = mock_tts_instance

        out_path = tmp_path / "output.wav"
        result = synth.synthesize("Alter course to starboard", out_path)

        mock_tts_instance.tts_to_file.assert_called_once_with(
            text="Alter course to starboard",
            file_path=str(out_path),
        )
        assert result == out_path

def test_synthesize_creates_parent_dir(tmp_path):
    with patch("nautical_english.tts.synthesizer.TTS") as MockTTS:
        mock_tts_instance = MagicMock()
        MockTTS.return_value = mock_tts_instance

        synth = TTSSynthesizer.__new__(TTSSynthesizer)
        synth._tts = mock_tts_instance

        deep_path = tmp_path / "new_dir" / "sub" / "output.wav"
        synth.synthesize("Test", deep_path)
        assert deep_path.parent.exists()
```

### Step 2.3：运行测试

```bash
pytest tests/test_tts/ -v
```

**预期：** 3 tests passed

### Step 2.4：下载 TTS 模型（如 Phase 1 未下载）

```bash
python scripts/download_models.py --skip-tts  # 若已有 Whisper 模型，跳过重复下载
# 或者只下载 TTS：
python -c "from TTS.api import TTS; TTS('tts_models/en/ljspeech/glow-tts', progress_bar=True)"
```

### Step 2.5：TTS 冒烟测试

```python
# smoke_test_tts.py（临时脚本）
import sys; sys.path.insert(0, "src")
from pathlib import Path
from nautical_english.tts.synthesizer import TTSSynthesizer

synth = TTSSynthesizer()
out = Path("test_tts_output.wav")
synth.synthesize("Alter course to starboard.", out)
print(f"TTS 输出文件: {out} ({out.stat().st_size} bytes)")

# 播放验证（Windows）
import subprocess
subprocess.Popen(["start", str(out)], shell=True)
```

### Step 2.6：提交

```bash
git add tests/test_tts/ src/nautical_english/tts/
git commit -m "feat(tts): add TTSSynthesizer with mock tests"
```

---

## 🛠️ Task 3.3 — 关联 SMCP_DATA 现有音频

> 利用项目中已有的 `SMCP_DATA/audioFile/` 音频文件替代 TTS 合成（质量更好）。

### Step 1：探查现有音频文件结构

```python
import sys; sys.path.insert(0, "src")
from pathlib import Path

smcp_dir = Path("SMCP_DATA/audioFile")
audio_files = list(smcp_dir.rglob("*.mp3")) + list(smcp_dir.rglob("*.wav"))
print(f"共找到 {len(audio_files)} 个音频文件")
for f in audio_files[:10]:
    print(f"  {f}")
```

### Step 2：在 `CorpusRepository` 中关联音频路径

在 `src/nautical_english/corpus/repository.py` 中已有 `update_phrase_audio` 方法（如无，参考 Phase 2 Task 2.2 添加），运行关联脚本：

> 此为扩展任务，可在 Phase 3 后半段完成

```python
# scripts/link_smcp_audio.py（新建）
"""将 SMCP_DATA 音频与数据库短语关联"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nautical_english.corpus.repository import CorpusRepository

# 根据实际文件名规则建立映射
# 示例：文件名包含短语关键词
repo = CorpusRepository()
phrases = repo.get_all_phrases()
smcp_dir = Path("SMCP_DATA/audioFile")

matched = 0
for phrase in phrases:
    # 简单启发式：文件名含短语前几个词
    key = "_".join(phrase.phrase_en.lower().split()[:3])
    candidates = list(smcp_dir.rglob(f"*{key}*"))
    if candidates:
        repo.update_phrase_audio(phrase.id, str(candidates[0]))
        matched += 1
        print(f"  Link: {phrase.phrase_en[:40]:40s} → {candidates[0].name}")

print(f"\n共关联 {matched}/{len(phrases)} 条短语音频")
```

---

## 🛠️ Task 3.4 — 训练会话编排器测试

> 文件已存在：`src/nautical_english/training/session.py`

### Step 1：新建训练会话测试目录

```bash
New-Item -ItemType Directory -Path tests\test_training -Force
New-Item -ItemType File -Path tests\test_training\__init__.py -Force
```

### Step 2：创建集成测试文件

新建 `tests/test_training/test_session.py`：

```python
from unittest.mock import MagicMock, patch
from pathlib import Path
import numpy as np
from nautical_english.training.session import TrainingSession, SessionResult

def _make_session(tmp_path):
    """创建注入了 Mock 依赖的 TrainingSession"""
    mock_asr = MagicMock()
    mock_asr.transcribe.return_value = "alter course to starboard"

    mock_matcher = MagicMock()
    mock_matcher.find_best_match.return_value = MagicMock(
        phrase="Alter course to starboard",
        score=0.95,
        index=0,
    )

    mock_scorer = MagicMock()
    mock_scorer.compute.return_value = MagicMock(
        wer=0.05, similarity=0.95, overall=87.0,
        grade="Good", feedback_en="Good attempt.",
    )

    mock_feedback_gen = MagicMock()
    mock_feedback_gen.generate.return_value = MagicMock(
        standard_phrase_en="Alter course to starboard",
        score_display="87.0 / 100",
        grade="Good",
        feedback_en="Good attempt.",
        diff_html="<span>...</span>",
    )

    mock_tts = MagicMock()
    mock_tts.synthesize.return_value = tmp_path / "feedback.wav"

    mock_repo = MagicMock()
    mock_repo.save_training_record.return_value = 1

    return TrainingSession(
        recognizer=mock_asr,
        matcher=mock_matcher,
        scorer=mock_scorer,
        feedback_gen=mock_feedback_gen,
        synthesizer=mock_tts,
        repository=mock_repo,
        phrase_zh_map={"Alter course to starboard": "向右转向"},
    )

def test_session_run_returns_session_result(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    result = session.run(audio, student_id="stu001", output_dir=tmp_path)
    assert isinstance(result, SessionResult)
    assert result.recognized_text == "alter course to starboard"
    assert result.matched_phrase == "Alter course to starboard"
    assert result.overall_score == 87.0

def test_session_calls_all_components(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    session.run(audio, student_id="stu001", output_dir=tmp_path)

    session._asr.transcribe.assert_called_once()
    session._matcher.find_best_match.assert_called_once_with("alter course to starboard")
    session._scorer.compute.assert_called_once()
    session._feedback.generate.assert_called_once()
    session._tts.synthesize.assert_called_once()
    session._repo.save_training_record.assert_called_once()

def test_session_saves_training_record(tmp_path):
    session = _make_session(tmp_path)
    audio = np.zeros(16000, dtype=np.float32)
    session.run(audio, student_id="student_007", output_dir=tmp_path)

    call_kwargs = session._repo.save_training_record.call_args
    assert call_kwargs.kwargs["student_id"] == "student_007"
    assert call_kwargs.kwargs["overall_score"] == 87.0
```

### Step 3：运行测试

```bash
pytest tests/test_training/ -v
```

**预期：** 3 tests passed

### Step 4：提交

```bash
git add tests/test_training/ src/nautical_english/training/
git commit -m "test: add TrainingSession integration tests with mocks"
```

---

## 🛠️ Task 3.5 — 端到端命令行演示脚本

新建 `scripts/demo_session.py`：

```python
"""端到端命令行演示 — 无 UI 验证完整流程

用法：
    python scripts/demo_session.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nautical_english.config import AppConfig
from nautical_english.asr.audio_capture import AudioCapture
from nautical_english.asr.recognizer import WhisperRecognizer
from nautical_english.tts.synthesizer import TTSSynthesizer
from nautical_english.nlp.matcher import SentenceMatcher
from nautical_english.nlp.scorer import PhraseScorer
from nautical_english.feedback.generator import FeedbackGenerator
from nautical_english.corpus.repository import CorpusRepository
from nautical_english.training.session import TrainingSession

def main():
    cfg = AppConfig()
    print("⚙️  Loading models...")
    repo = CorpusRepository()
    phrases = repo.get_all_phrases()
    phrases_en = [p.phrase_en for p in phrases]
    phrase_zh_map = {p.phrase_en: p.phrase_zh for p in phrases}

    recognizer = WhisperRecognizer(cfg.whisper_model_size, cfg.whisper_model_dir)
    matcher = SentenceMatcher(phrases=phrases_en)
    scorer = PhraseScorer(cfg.score_alpha, cfg.score_beta)
    feedback_gen = FeedbackGenerator()
    synthesizer = TTSSynthesizer(cfg.tts_model_name)
    cap = AudioCapture(cfg.sample_rate)

    session = TrainingSession(
        recognizer=recognizer,
        matcher=matcher,
        scorer=scorer,
        feedback_gen=feedback_gen,
        synthesizer=synthesizer,
        repository=repo,
        phrase_zh_map=phrase_zh_map,
    )

    output_dir = Path("corpus/db/tmp")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n🎙️  请说一句航海英语（5秒）...\n")
    audio = cap.record(5.0)

    print("🔍  识别中...")
    result = session.run(audio, student_id="demo_user", output_dir=output_dir)

    print("\n" + "═" * 50)
    print(f"识别文本:  {result.recognized_text}")
    print(f"最佳匹配:  {result.matched_phrase}")
    print(f"综合评分:  {result.overall_score} / 100  [{result.feedback.grade}]")
    print(f"反馈:      {result.feedback.feedback_en}")
    print(f"标准中文:  {result.feedback.standard_phrase_zh}")
    if result.feedback.error_words:
        print(f"错误词汇:  {', '.join(result.feedback.error_words)}")
    print("═" * 50)

    # 播放 TTS 反馈音频
    if result.tts_audio_path and result.tts_audio_path.exists():
        import subprocess
        print(f"\n🔊  播放标准发音: {result.tts_audio_path}")
        subprocess.Popen(["start", "", str(result.tts_audio_path)], shell=True)

if __name__ == "__main__":
    main()
```

### 运行演示

```bash
python scripts/demo_session.py
```

---

## ✅ Phase 3 验收标准

- [ ] `pytest tests/test_feedback/ tests/test_tts/ tests/test_training/ -v` 全部通过（9+ tests）
- [ ] TTS 冒烟测试：`synthesize("Alter course to starboard", ...)` 能生成音频文件
- [ ] 端到端演示脚本 `demo_session.py` 能完整运行
- [ ] 训练记录写入数据库（验证 `corpus/db/corpus.db` 中 `training_records` 表有数据）
- [ ] Git 有至少 5 次规范提交记录

---

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Coqui TTS 安装报错 | `espeak-ng` 缺失（Windows） | 参考 [Coqui TTS Windows 安装](https://github.com/coqui-ai/TTS#installation) |
| TTS 音频质量差 | 默认 glow-tts 模型 | Phase 5 可换更好的模型，Phase 3 够用 |
| `TrainingSession` 中 phrase_id 偏移 | 数据库 ID 从 1 开始 | 确认 `match.index + 1` 逻辑正确 |
| 演示脚本无声音 | Windows 音频设备 | 用系统播放器手动打开生成的 `.wav` 文件 |

---

## 📌 Phase 3 → Phase 4 交接检查

- **完成日期：** ______
- **TTS 模型名称：** ______
- **端到端延迟（录音到反馈）：** ______ 秒
- **demo_session.py 是否通过：** ☐ 是 / ☐ 否
- **备注：** ______
