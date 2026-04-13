# Phase 2 开发计划 — SMCP 语料库 + SBERT 匹配 + WER 评分

**周期：** 第 3-4 周（Sprint 3 & 4）  
**前置条件：** Phase 1 全部验收通过，Whisper 模型可用，`python src/main.py` 可正常启动。  
**目标：** 将 SMCP 标准句入库，实现语义匹配和评分引擎，使核心 NLP 管道完全可测试。  
**完成标准：** 给定任意英语句子，程序能在数据库中找到最接近的 SMCP 标准句，并输出 0-100 的综合评分。

---

## 📦 本阶段交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| ORM 数据模型 | `src/nautical_english/corpus/models.py` | Category / Phrase / TrainingRecord 三张表 |
| 数据访问层 | `src/nautical_english/corpus/repository.py` | CRUD 操作封装 |
| SMCP 种子数据 | `src/nautical_english/corpus/seed_data.py` | 60+ 标准航海英语短语 |
| 语料初始化脚本 | `scripts/seed_corpus.py` | 写入 SQLite 数据库 |
| 句子匹配模块 | `src/nautical_english/nlp/matcher.py` | SBERT 语义匹配 |
| 评分模块 | `src/nautical_english/nlp/scorer.py` | WER + 相似度融合评分 |
| 完整测试套件 | `tests/test_corpus/` + `tests/test_nlp/` | 覆盖所有 NLP 路径 |

---

## 🛠️ Task 2.1 — 验证 ORM 模型和语料库

> 文件已存在，本任务运行测试并写入数据库。

### Step 1：运行语料库测试

```bash
cd f:\AI_CODING\JMU_nauticalEnglishOralAndListening
pytest tests/test_corpus/ -v
```

**预期：** 5 tests passed

若有失败，逐项检查：

```bash
# 单独运行某个测试查看详细错误
pytest tests/test_corpus/test_repository.py::test_save_training_record -v -s
```

### Step 2：初始化 SMCP 语料数据库

```bash
python scripts/seed_corpus.py
```

**预期输出：**
```
[seed] Inserted 5 categories, 59 phrases.
✅ Corpus seeded successfully.
```

### Step 3：验证数据库内容

```python
# 临时验证脚本
import sys; sys.path.insert(0, "src")
from nautical_english.corpus.repository import CorpusRepository

repo = CorpusRepository()
cats = repo.get_all_categories()
phrases = repo.get_all_phrases()
print(f"类别数: {len(cats)}")
print(f"短语总数: {len(phrases)}")
for cat in cats:
    ps = repo.get_phrases_by_category(cat.id)
    print(f"  [{cat.name_en}] {len(ps)} 条短语")
```

**预期输出示例：**
```
类别数: 5
短语总数: 59
  [Navigation & Maneuvering] 15 条短语
  [Distress & Urgency] 12 条短语
  [Collision Avoidance] 12 条短语
  [Anchoring & Mooring] 8 条短语
  [VHF Communication] 12 条短语
```

### Step 4：提交

```bash
git add corpus/
git commit -m "feat(corpus): seed SMCP database with 59 standard phrases"
```

---

## 🛠️ Task 2.2 — 扩充 SMCP 种子数据（可选增强）

> 现有 `seed_data.py` 已有约 59 条短语。若需要增加，在 `SEED_DATA` 列表中补充。

### 推荐补充的 SMCP 场景

**场景 6：港口操作（Port Operations）**

编辑 `src/nautical_english/corpus/seed_data.py`，在列表末尾添加：

```python
(
    "Port Operations",
    "港口操作",
    [
        ("I require a berth.", "我需要一个泊位。", 2),
        ("When is my berth available?", "我的泊位何时可用？", 2),
        ("I am ready to berth.", "我准备好靠泊。", 2),
        ("I require port health clearance.", "我需要港口卫生检疫许可。", 3),
        ("I require customs clearance.", "我需要海关许可。", 3),
        ("I am cleared for departure.", "我已获准离港。", 2),
        ("I require a garbage reception facility.", "我需要垃圾接收设施。", 3),
        ("My estimated time of departure is [time].", "我预计离港时间为[时间]。", 2),
    ],
),
```

> 添加后重新运行 `python scripts/seed_corpus.py` 会因"已有数据"跳过。  
> 若要重新初始化：先删除 `corpus/db/corpus.db` 再运行。

---

## 🛠️ Task 2.3 — 利用现有 SMCP_DATA 音频文件

> ⭐ 项目中已有 `SMCP_DATA/audioFile/` 目录，包含真实标准发音音频！

### Step 1：查看现有音频资源

```bash
Get-ChildItem SMCP_DATA\audioFile -Recurse -File | Select-Object -First 20
```

### Step 2：将音频路径关联到数据库短语（扩展任务）

在 `repository.py` 中添加更新音频路径的方法：

```python
def update_phrase_audio(self, phrase_id: int, audio_path: str) -> None:
    with self._Session() as session:
        p = session.get(Phrase, phrase_id)
        if p:
            p.audio_path = audio_path
            session.commit()
```

> 完整音频关联映射可在 Phase 3（TTS 集成）时实现，本阶段了解资源即可。

---

## 🛠️ Task 2.4 — 句子匹配模块测试

> 文件已存在：`src/nautical_english/nlp/matcher.py`

### Step 1：运行现有测试

```bash
pytest tests/test_nlp/test_matcher.py -v
```

**预期：** 2 tests passed（使用 Mock，不加载真实 SBERT 模型）

### Step 2：集成冒烟测试（需要 SBERT 模型已下载）

```python
# smoke_test_matcher.py（临时脚本）
import sys; sys.path.insert(0, "src")
from nautical_english.nlp.matcher import SentenceMatcher
from nautical_english.corpus.repository import CorpusRepository

repo = CorpusRepository()
phrases = [p.phrase_en for p in repo.get_all_phrases()]

matcher = SentenceMatcher(phrases=phrases)

queries = [
    "turn right now",
    "help me I'm sinking",
    "I need to talk to you on channel 16",
    "there will be a collision",
]

for q in queries:
    result = matcher.find_best_match(q)
    print(f"Query:  {q}")
    print(f"Match:  {result.phrase} (score={result.score:.3f})")
    print()
```

**预期输出示例：**
```
Query:  turn right now
Match:  Alter course to starboard. (score=0.72)

Query:  help me I'm sinking
Match:  I am sinking. (score=0.89)
```

### Step 3：提交

```bash
git add tests/test_nlp/
git commit -m "test: verify SentenceMatcher with mock and smoke test"
```

---

## 🛠️ Task 2.5 — 评分模块测试

> 文件已存在：`src/nautical_english/nlp/scorer.py`

### Step 1：运行现有测试

```bash
pytest tests/test_nlp/test_scorer.py -v
```

**预期：** 6 tests passed（全部纯计算，无需 AI 模型）

### Step 2：手动理解评分公式

评分公式：`overall = 100 × (0.6 × similarity + 0.4 × (1 - WER))`

用 Python 验证理解：

```python
import sys; sys.path.insert(0, "src")
from nautical_english.nlp.scorer import PhraseScorer

scorer = PhraseScorer()

# 测试用例
cases = [
    ("Alter course to starboard", "Alter course to starboard", 0.99),  # 完美
    ("alter course to starboard", "Alter course to starboard", 0.99),  # 大小写
    ("alter course to port",      "Alter course to starboard", 0.65),  # 方向错
    ("hello world",               "Alter course to starboard", 0.05),  # 完全错误
]

for rec, ref, sim in cases:
    result = scorer.compute(rec, ref, sim)
    print(f"[{result.grade:9s}] {result.overall:5.1f}  WER={result.wer:.2f}  "
          f"Sim={result.similarity:.2f}  | {rec!r}")
```

### Step 3：提交

```bash
git add tests/test_nlp/
git commit -m "test: verify PhraseScorer with 6 edge cases"
```

---

## 🛠️ Task 2.6 — NLP 管道端到端冒烟测试

将 ASR → 匹配 → 评分 串联验证（手动）：

```python
# smoke_test_pipeline.py（临时脚本）
import sys; sys.path.insert(0, "src")
from nautical_english.asr.audio_capture import AudioCapture
from nautical_english.asr.recognizer import WhisperRecognizer
from nautical_english.nlp.matcher import SentenceMatcher
from nautical_english.nlp.scorer import PhraseScorer
from nautical_english.corpus.repository import CorpusRepository
from nautical_english.config import AppConfig

cfg = AppConfig()
repo = CorpusRepository()
phrases_en = [p.phrase_en for p in repo.get_all_phrases()]

rec = WhisperRecognizer(cfg.whisper_model_size, cfg.whisper_model_dir)
matcher = SentenceMatcher(phrases=phrases_en)
scorer = PhraseScorer(cfg.score_alpha, cfg.score_beta)
cap = AudioCapture()

print("请说一句航海英语（5秒）...")
audio = cap.record(5.0)

text = rec.transcribe(audio)
print(f"\nASR 识别: {text}")

match = matcher.find_best_match(text)
print(f"最佳匹配: {match.phrase} (similarity={match.score:.3f})")

score = scorer.compute(text, match.phrase, match.score)
print(f"综合评分: {score.overall} / 100  [{score.grade}]")
print(f"WER:      {score.wer:.3f}")
print(f"反馈:     {score.feedback_en}")
```

---

## ✅ Phase 2 验收标准

- [ ] `pytest tests/test_corpus/ tests/test_nlp/ -v` 全部通过
- [ ] `python scripts/seed_corpus.py` 成功写入 ≥50 条短语
- [ ] SBERT 管道冒烟测试：输入 "turn right" 能匹配到 "Alter course to starboard"
- [ ] 评分管道冒烟测试：完全匹配得分 ≥ 90
- [ ] Git 有至少 4 次规范提交记录

---

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| SBERT 首次加载慢 | 模型初始化 | 正常现象，约 30s，后续热启动更快 |
| `jiwer` WER 计算方式 | 单词级别 | WER > 1.0 是正常的（extra words），代码已 `min(wer, 1.0)` 截断 |
| 数据库已存在无法重置 | seed 跳过逻辑 | 删除 `corpus/db/corpus.db` 后重新运行 seed |
| 匹配得分过低 | 领域特异性 | 可在 Phase 3 后通过扩充语料库改善 |

---

## 📌 Phase 2 → Phase 3 交接检查

- **完成日期：** ______
- **数据库短语总数：** ______
- **SBERT 模型加载时间：** ______ 秒
- **管道冒烟测试是否通过：** ☐ 是 / ☐ 否
- **备注：** ______
