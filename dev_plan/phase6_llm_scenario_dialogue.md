# Phase 6 开发计划 — 大语言模型场景对话教练

**周期：** 第 10-13 周  
**前置条件：** Phase 4 / Phase 5 全部验收通过；学员端单次练习流程可正常运行。  
**目标：** 在现有 ASR + 评分引擎之上，引入 LLM 驱动的"场景对话教练"，学员在给定航海英语场景（如"引航""遇险""货物装卸"等）中，与 LLM 扮演的对方船员 / 港控人员自由对话，并获得即时 SMCP 规范点评与评分。

**完成标准：**  
- 学员可从场景库选择场景并启动对话  
- LLM 自动根据 SMCP 标准扮演对方角色发起问题或回复  
- 学员可以语音（ASR）或文本作答  
- 每轮对话结束后 LLM 输出：内容评判 / 规范修正 / 参考用语  
- 会话结束后生成完整对话成绩报告  
- 至少支持 DeepSeek / Kimi 两家 Provider（OpenAI 兼容接口）

---

## 📐 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                     Student UI                               │
│  ScenarioSelectorView → DialogueView ← DialogueSummaryView  │
└──────────┬───────────────────┬────────────────────┬─────────┘
           │                   │                    │
    ASR (Whisper)     DialogueController     TTSSynthesizer
           │                   │ 
           │         ┌─────────▼──────────┐
           │         │  CoachService       │
           │         │  (场景逻辑 + 回合管理)│
           │         └─────────┬──────────┘
           │                   │
           │         ┌─────────▼──────────┐
           │         │  LLMProvider       │
           │         │  (DeepSeek/Kimi)   │
           │         └────────────────────┘
           │
    CorpusRepository  ←  ScenarioRepository
```

---

## 📦 交付物清单

| 文件 | 说明 |
|------|------|
| `src/nautical_english/llm/__init__.py` | LLM 子包 |
| `src/nautical_english/llm/provider.py` | LLMProvider 协议 + BaseLLMProvider |
| `src/nautical_english/llm/deepseek_provider.py` | DeepSeek API 实现 |
| `src/nautical_english/llm/kimi_provider.py` | Kimi (moonshot-v1) API 实现 |
| `src/nautical_english/llm/config.py` | Provider 配置（apikey / model / timeout） |
| `src/nautical_english/scenario/models.py` | Scenario / DialogueTurn ORM 模型 |
| `src/nautical_english/scenario/repository.py` | ScenarioRepository CRUD |
| `src/nautical_english/scenario/seed_data.py` | 10 条初始场景种子数据 |
| `src/nautical_english/coach/service.py` | CoachService：多轮对话状态机 + SMCP 提示策略 |
| `src/nautical_english/coach/prompts.py` | 系统提示词模板（SMCP 规范注入） |
| `src/nautical_english/ui/student/scenario_selector.py` | 场景选择界面 |
| `src/nautical_english/ui/student/dialogue_view.py` | 对话练习主界面 |
| `src/nautical_english/ui/student/dialogue_summary.py` | 对话总结/成绩界面 |
| `src/nautical_english/ui/dialogue_controller.py` | 新对话控制器 |
| `src/nautical_english/ui/dialogue_worker.py` | LLM 推理 QThread 工作线程 |
| `tests/test_llm/test_provider.py` | Provider 单元测试（mock HTTP） |
| `tests/test_coach/test_service.py` | CoachService 状态机测试 |
| `tests/test_scenario/test_repository.py` | ScenarioRepository CRUD 测试 |

---

## 🛠️ Task 6.1 — LLM Provider 抽象层

### 目标
统一多家 LLM 服务接口，使 CoachService 不感知底层供应商细节。

### 接口设计

```python
class LLMMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str

class LLMResponse:
    content: str          # 回复文本
    usage: dict           # token 消耗

class BaseLLMProvider:
    def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse: ...
    def stream_chat(self, messages, **kwargs) -> Iterator[str]: ...
```

### 支持的 Provider

| Provider | Base URL | 推荐模型 |
|----------|---------|---------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Z.ai | `https://api.z.ai/v1` | （视供应商文档） |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |

所有 Provider 均走 OpenAI Chat Completions 兼容接口，只需切换 `base_url` + `api_key`。

### 实现步骤

1. 新建 `src/nautical_english/llm/` 子包
2. 实现 `provider.py`：`BaseLLMProvider` + `LLMMessage` dataclass
3. 实现 `deepseek_provider.py`（使用 `openai` SDK + 自定义 base_url）
4. 实现 `kimi_provider.py`（同上，base_url 不同）
5. 实现 `config.py`：从环境变量 / `config.yaml` 读取密钥
6. 写 `tests/test_llm/test_provider.py`（mock HTTP，不实际消耗 API）
7. 运行测试，全绿后提交

---

## 🛠️ Task 6.2 — 场景库数据模型

### Scenario ORM 模型

```python
class Scenario(Base):
    id: int
    name_en: str          # "Pilot boarding request"
    name_zh: str          # "引航员登轮请求"
    category: str         # "Navigation" / "Distress" / "Cargo" ...
    difficulty: int       # 1-3
    description_en: str   # 场景背景说明
    description_zh: str
    system_role_en: str   # LLM 扮演的角色（如 "You are a VTS officer..."）
    opening_line_en: str  # LLM 开场白
    max_turns: int        # 最大对话回合数，默认 8

class DialogueTurn(Base):
    id: int
    session_id: str
    student_id: str
    scenario_id: int
    turn_index: int
    role: str             # "coach" | "student"
    content: str          # 文本内容
    audio_path: str | None
    llm_judgement: str | None  # LLM 点评（仅 student 轮）
    score: float | None
    created_at: datetime
```

### 种子场景（10 条）

| 编号 | 名称 | 类别 |
|------|------|------|
| 1 | Pilot boarding request | Navigation |
| 2 | VTS position report | Navigation |
| 3 | Distress call (Mayday) | Distress |
| 4 | Man overboard | Distress |
| 5 | Anchoring permission | Port Operations |
| 6 | Cargo damage report | Cargo |
| 7 | Fire on board | Emergency |
| 8 | Weather report request | Navigation |
| 9 | Tug assistance request | Port Operations |
| 10 | Medical assistance (PAN PAN) | Emergency |

---

## 🛠️ Task 6.3 — SMCP 教练服务（CoachService）

### 核心职责
- 维护对话状态（round index、历史 messages、结束条件）
- 把场景系统提示 + SMCP 规范注入到 LLM 上下文
- 生成"教练点评"专用 Prompt，引导 LLM 对学员用语给出：
  - ✅ 规范用语 / ❌ 错误点 / 💡 SMCP 参考修正
- 生成会话总结（整体评分、薄弱点、推荐练习）

### SMCP 系统提示（核心片段）

```
You are an experienced maritime English coach and SMCP (Standard Marine Communication Phrases) expert.
Your role in this scenario: {scenario.system_role_en}

IMPORTANT RULES:
1. Always communicate in Standard Marine English following SMCP guidelines.
2. After each student turn, respond in two parts:
   [REPLY] Your in-character response (1-2 sentences max)
   [JUDGE] Brief assessment: was the student's phrase SMCP-compliant?
            - Quote the correct SMCP phrase if the student's was wrong/informal.
3. Keep [REPLY] concise, realistic, and in character.
4. Keep [JUDGE] constructive and educational.
```

### 状态机

```
IDLE → SCENARIO_SELECTED → IN_DIALOGUE(turn 1..N) → SUMMARIZING → DONE
```

---

## 🛠️ Task 6.4 — 对话 UI 三屏

### ScenarioSelectorView（场景选择）
```
┌─────────────────────────────────────────────────┐
│  Scene Category: [▾ All]   Difficulty: [▾ All]  │
├──────────────────┬──────────────────────────────┤
│  🧭 Pilot boarding | VTS 引航请求               │
│  📡 VTS Report     | VTS 位置报告               │
│  🆘 Mayday Call    | 遇险呼叫                   │
│  ⚓ Anchoring      | 锚泊申请                   │
│  ...                                            │
├─────────────────────────────────────────────────┤
│  Description: ...（选中场景说明）               │
│            [ ▶ Start Dialogue ]                │
└─────────────────────────────────────────────────┘
```

### DialogueView（对话练习）
```
┌──────────────────────────────────────────────────┐
│  🧭 Pilot boarding   Turn 3/8     [End Session] │
├──────────────────────────────────────────────────┤
│  Coach: "Please state your vessel name and ETA." │
│  You:   "This is MV Ocean Star, ETA 0800 UTC."  │
│  ✅ Good: "ETA" used correctly per SMCP.         │
│  Coach: "Roger. Proceed to anchorage Alpha."     │
│  ▷ You:  [recording waveform / text input]      │
├──────────────────────────────────────────────────┤
│  [ 🎙 Speak ]  [ ✍ Type instead ]  [ 💡 Hint ] │
└──────────────────────────────────────────────────┘
```

### DialogueSummaryView（会话总结）
```
┌──────────────────────────────────────────────────┐
│         Session Complete — 6 turns               │
│              Overall Score: 78.5                 │
│  SMCP Compliance: 4/6 turns fully correct        │
├──────────────────────────────────────────────────┤
│  Turn-by-turn breakdown (collapsible)            │
│  Key errors:                                     │
│  • Turn 2: "What is the time?" → SMCP: "Time?"  │
│  • Turn 5: non-standard EOT phrasing             │
├──────────────────────────────────────────────────┤
│  [ 🔁 Retry Same Scene ]  [ 📋 New Scene ]       │
└──────────────────────────────────────────────────┘
```

---

## 🛠️ Task 6.5 — 管理员端扩展

- 场景管理（ScenarioManager）：在管理后台新增"场景库"标签，支持新增/编辑场景
- 对话历史：管理端可查看所有学员的对话记录与回合评分

---

## ✅ Phase 6 验收标准

- [ ] 学员可选场景并与 LLM 完成 ≥ 3 回合对话
- [ ] ASR 语音输入与纯文字输入均可正常发送
- [ ] LLM 回复包含 `[REPLY]` + `[JUDGE]` 两部分，UI 分区展示
- [ ] 会话结束后 SummaryView 显示各轮详情与总分
- [ ] DeepSeek 和 Kimi 两家 Provider 均可通过配置切换
- [ ] 网络超时或 API 错误时 UI 有明确提示，不崩溃
- [ ] `pytest tests/ -v` 全部通过（含 mock LLM 测试）
- [ ] `DEEPSEEK_API_KEY` / `KIMI_API_KEY` 只从环境变量读取，不写入代码

---

## ⚠️ 配置说明

在项目根目录创建 `.env`（不提交到 git）：

```dotenv
# LLM Provider 配置
LLM_PROVIDER=deepseek          # deepseek | kimi | openai
DEEPSEEK_API_KEY=sk-xxxx
KIMI_API_KEY=sk-xxxx

# 可选覆盖
DEEPSEEK_MODEL=deepseek-chat
KIMI_MODEL=moonshot-v1-8k
LLM_TIMEOUT=30
LLM_MAX_TOKENS=512
```

---

## 📌 Phase 6 → Phase 7 交接检查

- **完成日期：** ______
- **LLM 对话端到端验证：** ☐ 是 / ☐ 否
- **两家 Provider 均测试通过：** ☐ 是 / ☐ 否
- **备注：** ______
