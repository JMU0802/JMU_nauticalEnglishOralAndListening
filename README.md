# Maritime English Trainer — 航海英语听说训练系统

> 集美大学航海技术学院 · 离线智能语音教练  
> **Offline Speech Coach for Maritime English (SMCP)**

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🎙 ASR 语音识别 | faster-whisper large-v3，含航海术语提示 |
| 📚 SMCP 语料库 | 标准海事通信英语标准句，SQLite 离线存储 |
| 🧠 AI 句子匹配 | Sentence-BERT 语义相似度匹配 |
| 📊 发音评分 | WER + 语义相似度双指标融合（0-100分） |
| 🔊 TTS 朗读 | Coqui TTS 英语标准发音播报 |
| 🖥️ 双语界面 | 学生端英文 / 管理端中文，PyQt6 原生 UI |
| 📦 离线部署 | 完全离线，支持 Windows 10/11 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载 AI 模型（首次运行）

```bash
python scripts/download_models.py
```

### 3. 初始化语料库

```bash
python scripts/seed_corpus.py
```

### 4. 启动程序

```bash
cd src
python main.py
```

---

## 🏗️ 项目结构

```
JMU_nauticalEnglishOralAndListening/
├── docs/superpowers/
│   ├── specs/   ← 设计规范
│   └── plans/   ← 实施计划
├── src/
│   ├── main.py
│   └── nautical_english/
│       ├── config.py          ← 全局配置
│       ├── asr/               ← 语音识别（Whisper）
│       ├── tts/               ← 语音合成（Coqui TTS）
│       ├── nlp/               ← 句子匹配 + 评分
│       ├── corpus/            ← SQLite 语料库
│       ├── feedback/          ← 反馈生成
│       ├── training/          ← 训练会话编排
│       └── ui/                ← PyQt6 界面
├── tests/                     ← pytest 单元测试
├── scripts/                   ← 工具脚本
├── models/                    ← AI 模型（git 忽略）
└── corpus/db/                 ← 数据库文件（git 忽略）
```

---

## 🧪 运行测试

```bash
pytest tests/ --cov=src/nautical_english --cov-report=html
```

---

## 📋 开发阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | 开发环境 + ASR + 基础窗口 | 🔲 待开始 |
| Phase 2 | SMCP 语料库 + 句子匹配 + 评分 | 🔲 待开始 |
| Phase 3 | TTS + 反馈 + 训练会话 | 🔲 待开始 |
| Phase 4 | 完整 PyQt6 UI | 🔲 待开始 |
| Phase 5 | 性能优化 + Windows 打包 | 🔲 待开始 |

详见 [阶段性实施计划](docs/superpowers/plans/2026-04-13-nautical-english-trainer-plan.md)

---

## ⚙️ 硬件要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| CPU | 4 核 | 8 核 |
| RAM | 8 GB | 16 GB |
| GPU | — | NVIDIA 6GB VRAM（可选，加速 Whisper） |
| 存储 | 8 GB | 16 GB |
| OS | Windows 10 64-bit | Windows 11 64-bit |

---

## 📚 参考资料

- [IMO SMCP — Standard Marine Communication Phrases](https://www.imo.org)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [Sentence Transformers](https://www.sbert.net)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)

---

## 🔑 LLM 配置

在项目根目录创建 `.env` 文件（已被 `.gitignore` 忽略，不会提交到 git）：

```env
# 选择 LLM 提供商: deepseek | kimi | zai
LLM_PROVIDER=zai

# Z.ai (ZhipuAI GLM) API Key
ZAI_API_KEY=<your-key-here>

# 可选
# DEEPSEEK_API_KEY=
# KIMI_API_KEY=
# LLM_TIMEOUT=30
# LLM_MAX_TOKENS=512
```