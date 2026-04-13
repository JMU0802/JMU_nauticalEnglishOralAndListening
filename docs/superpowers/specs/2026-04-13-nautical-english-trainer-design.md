# 航海英语听说训练系统 — 设计规范

**日期：** 2026-04-13  
**版本：** v1.0  
**作者：** JMU 航海技术学院  

---

## 1. 系统定位

**系统本质：离线智能语音教练（Offline Speech Coach for Maritime English）**

```
学员语音 → ASR识别 → 语义理解/评分 → 反馈生成 → TTS播报
```

| 维度 | 说明 |
|------|------|
| 目标用户 | 航海专业本科生（听说英语训练） |
| 部署场景 | 离线 Windows 实验室/教室 PC |
| 界面语言 | 双语：学生端英文，管理端中文 |
| 核心价值 | 标准航海英语（SMCP）听说对比训练 + 即时评分反馈 |

---

## 2. 核心技术选型

| 模块 | 技术 | 版本 / 选型理由 |
|------|------|----------------|
| UI 框架 | **PyQt6** | 跨版本稳定、原生 Windows 渲染 |
| ASR | **faster-whisper** | CTranslate2 后端，large-v3 模型，速度 3-4x 快于 openai-whisper |
| TTS | **Coqui TTS (XTTS-v2)** | 英文发音质量高，可本地推理 |
| 句子匹配 | **sentence-transformers (SBERT)** | `paraphrase-multilingual-MiniLM-L12-v2` |
| 发音评分 | **jiwer (WER)** + 余弦相似度 | 双指标融合评分 |
| 语料库 | **SQLite + SQLAlchemy** | 轻量离线，无需额外服务 |
| 音频 I/O | **sounddevice + soundfile** | 跨平台稳定，PyQt6 友好 |
| 包管理 | **pyproject.toml (PEP 517)** | 现代 Python 项目标准 |
| 测试框架 | **pytest + pytest-qt** | 单元测试 + UI 测试 |

---

## 3. 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     PyQt6 主窗口                         │
│  ┌─────────────────────┐  ┌────────────────────────────┐│
│  │   学生端 (英文 UI)    │  │   管理端 (中文 UI)          ││
│  │  - PracticeView     │  │  - CorpusManager           ││
│  │  - ResultView       │  │  - ProgressDashboard       ││
│  │  - ProgressView     │  │                            ││
│  └──────────┬──────────┘  └────────────────────────────┘│
└─────────────┼───────────────────────────────────────────┘
              │ 调用
┌─────────────▼───────────────────────────────────────────┐
│                    业务逻辑层                             │
│  TrainingSession                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │  ASR     │ │  NLP     │ │ Feedback │ │   TTS      │ │
│  │Recognizer│ │ Matcher  │ │Generator │ │Synthesizer │ │
│  │          │ │ Scorer   │ │          │ │            │ │
│  └──────────┘ └────┬─────┘ └──────────┘ └────────────┘ │
└────────────────────┼────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    数据层                                │
│  SQLite (corpus.db)  │  models/ (Whisper, SBERT, TTS)  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 数据库设计（SQLite）

### 4.1 表：`categories`（SMCP 场景类别）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name_en | TEXT | 英文类别名 |
| name_zh | TEXT | 中文类别名 |
| description | TEXT | |

### 4.2 表：`phrases`（标准航海英语短语）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| category_id | INTEGER FK | 归属类别 |
| phrase_en | TEXT | 标准英语短语 |
| phrase_zh | TEXT | 中文释义 |
| phonetic | TEXT | 音标（可选） |
| difficulty | INTEGER | 1=基础, 2=中级, 3=高级 |
| audio_path | TEXT | 预录标准音频路径（可选） |

### 4.3 表：`training_records`（训练记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| student_id | TEXT | 学生标识 |
| phrase_id | INTEGER FK | 练习的短语 |
| recognized_text | TEXT | ASR 识别结果 |
| wer_score | REAL | 词错误率 (0-1) |
| similarity_score | REAL | 语义相似度 (0-1) |
| overall_score | REAL | 综合分数 (0-100) |
| created_at | DATETIME | 记录时间 |

---

## 5. 评分算法设计

### 5.1 综合评分公式

```
overall_score = 100 × (α × semantic_sim + β × (1 - WER))
```

其中：
- `α = 0.6`（语义相似度权重）
- `β = 0.4`（发音准确度权重）
- `semantic_sim` ∈ [0, 1]：学员文本与标准句的余弦相似度
- `WER` ∈ [0, 1]：词错误率（越低越好）

### 5.2 反馈等级

| 分数 | 等级 | 反馈文本 |
|------|------|--------|
| 90-100 | Excellent | Perfect! Standard pronunciation. |
| 70-89 | Good | Good attempt. Minor errors detected. |
| 50-69 | Fair | Partially correct. Keep practicing. |
| 0-49 | Poor | Incorrect. Please try again. |

---

## 6. 关键约束

1. **完全离线** — 不依赖任何网络 API，模型需预下载至 `models/` 目录
2. **Windows 7/10/11 兼容** — 避免使用 Windows 11 专有 API
3. **内存限制** — 目标运行内存 < 4GB（Whisper large-v3 约 1.5GB VRAM/RAM）
4. **延迟目标** — ASR 识别响应 < 3 秒（针对 5-15 词的短语）
5. **数据隐私** — 训练记录仅存本地 SQLite，不上传

---

## 7. 项目目录结构

```
JMU_nauticalEnglishOralAndListening/
├── docs/                          # 项目文档
│   ├── superpowers/specs/         # 设计规范
│   └── superpowers/plans/         # 实施计划
├── assets/                        # 静态资源
│   ├── icons/                     # 应用图标
│   ├── audio/                     # 示例音频
│   └── fonts/                     # 字体
├── corpus/                        # 语料库数据
│   ├── raw/                       # 原始 SMCP 文本
│   └── db/                        # SQLite 数据库文件
├── models/                        # AI 模型（不纳入 git）
│   ├── whisper/                   # faster-whisper 模型
│   └── tts/                       # Coqui TTS 模型
├── src/
│   ├── main.py                    # 程序入口
│   └── nautical_english/          # 主包
│       ├── config.py              # 全局配置
│       ├── asr/                   # 语音识别模块
│       │   ├── recognizer.py      # Whisper 封装
│       │   └── audio_capture.py   # 麦克风录音
│       ├── tts/                   # 语音合成模块
│       │   └── synthesizer.py     # Coqui TTS 封装
│       ├── nlp/                   # NLP 模块
│       │   ├── matcher.py         # SBERT 句子匹配
│       │   └── scorer.py          # WER + 相似度评分
│       ├── corpus/                # 语料库模块
│       │   ├── models.py          # SQLAlchemy ORM 模型
│       │   ├── repository.py      # 数据访问层
│       │   └── seed_data.py       # SMCP 种子数据
│       ├── feedback/              # 反馈生成模块
│       │   └── generator.py
│       ├── training/              # 训练会话逻辑
│       │   └── session.py
│       └── ui/                    # 界面层
│           ├── main_window.py     # 主窗口
│           ├── student/           # 学生端界面（英文）
│           ├── admin/             # 管理端界面（中文）
│           ├── components/        # 可复用组件
│           └── resources/         # QSS 样式
├── tests/                         # 单元测试
├── scripts/                       # 工具脚本
│   ├── download_models.py         # 模型下载
│   ├── seed_corpus.py             # 语料初始化
│   └── build_installer.py         # Windows 打包
├── pyproject.toml                 # 项目元数据
├── requirements.txt               # 运行依赖
├── requirements-dev.txt           # 开发依赖
└── README.md
```

---

## 8. 超出范围（本期不做）

- 网络多人协作
- 移动端（Android / iOS）
- 深度学习发音模型（GOP）微调
- 视频/字幕同步功能
