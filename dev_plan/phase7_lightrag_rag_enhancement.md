# Phase 7 开发计划 — RAG 增强版 SMCP 口语训练与评估系统

**版本：** v1.0  
**日期：** 2026年4月15日  
**负责人：** 系统架构师  
**前置条件：** Phase 6（LLM 场景对话教练）验收通过；LightRAG Server 部署就绪；SMCP 知识库文档已导入。  
**文档状态：** ✅ 已批准，进入实施阶段  

---

## 1. 背景与动机

### 1.1 问题陈述

当前 Phase 6 系统依赖在线 LLM(GLM-4-Plus) 直接生成 SMCP 对话内容，存在以下关键问题：

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| LLM 对 SMCP 专业知识掌握不稳定 | 生成非标准短语，误导学员 | 🔴 高 |
| 无法引用 IMO A.918(22) 原文 | 缺乏权威依据 | 🔴 高 |
| 每次请求消耗大量 token（无记忆） | 运营成本高 | 🟡 中 |
| 评估缺乏专业知识来源 | 评估质量不稳定 | 🔴 高 |

### 1.2 解决方案：LightRAG 知识增强

引入 **LightRAG**（基于知识图谱的 RAG 框架）作为专业知识库服务，将以下权威文档建立成结构化知识图谱：
- IMO SMCP 标准（A.918(22) 决议）
- Maritime English for Merchant Marine Academy（航海英语教材）
- SMCP 完整短语集（smcp.pdf）

**增强效果：**  
LLM 对话响应 = LightRAG 检索出的 SMCP 标准知识 + LLM 语言生成能力  
= 专业性 + 流畅性 的最优组合

---

## 2. 系统架构

### 2.1 整体架构（增强后）

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SMCP Training Application                        │
│  ScenarioSelector → DialogueView → DialogueSummary                  │
└──────────┬──────────────────┬────────────────────┬──────────────────┘
           │                  │                    │
    ASR (Whisper)    ┌────────▼────────┐    TTSSynthesizer
                     │  CoachService   │
                     │  (相比v1增加RAG) │
                     └────────┬────────┘
                              │
              ┌───────────────┼──────────────────┐
              │               │                  │
    ┌─────────▼──────┐  ┌─────▼──────┐  ┌───────▼────────┐
    │ LLMLProvider   │  │ RAGClient  │  │ ScenarioRepo   │
    │ (GLM/ZhipuAI) │  │ (HTTP API) │  │ (SQLite)       │
    └────────────────┘  └─────┬──────┘  └────────────────┘
                              │
                     ┌────────▼────────────┐
                     │  LightRAG Server    │  ← 独立进程
                     │  Port: 9621        │
                     │  WebUI + REST API  │
                     └────────┬────────────┘
                              │
                     ┌────────▼────────────┐
                     │  知识图谱存储        │
                     │  - SMCP 标准短语     │
                     │  - IMO A.918(22)    │
                     │  - Maritime English │
                     │  JSON/NetworkX     │
                     └────────────────────┘
```

### 2.2 RAG 调用流程

```
学员输入 (ASR/文字)
    │
    ▼
CoachService.student_speak()
    │
    ├─[1] RAGClient.query(student_text, mode="mix")
    │         └─ LightRAG Server → 检索相关 SMCP 知识
    │
    ├─[2] 构建增强 Prompt:
    │         system = 标准 SMCP Coach 角色
    │         context = RAG 检索结果（相关标准短语 + 程序）
    │         user = 学员输入
    │
    ├─[3] LLM.stream_chat(augmented_messages)
    │         └─ GLM 基于 RAG 上下文生成回复
    │
    └─[4] 返回 TurnResult（reply + judgement + score）
```

### 2.3 组件职责

| 组件 | 职责 | 实现位置 |
|------|------|----------|
| `RAGClient` | HTTP 调用 LightRAG REST API | `src/nautical_english/rag/client.py` |
| `RAGConfig` | LightRAG 连接参数管理 | `src/nautical_english/rag/config.py` |
| `CoachService` (增强) | 集成 RAG 上下文到 prompt | `src/nautical_english/coach/service.py` |
| `prompts.py` (增强) | 带 RAG 上下文的 prompt 模板 | `src/nautical_english/coach/prompts.py` |
| LightRAG Server | 知识图谱 + 向量检索服务 | `lightrag/` 目录，独立进程 |

---

## 3. 知识库规划

### 3.1 知识库文档清单

| 文档 | 来源 | 重要性 | 处理方式 |
|------|------|--------|----------|
| `smcp.pdf` | SMCP_DATA/docs/ | 🔴 核心 | 全量导入 |
| `A.918(22).pdf` | SMCP_DATA/docs/ | 🔴 核心 | 全量导入 |
| `3317.-Maritime-English-for-the-Merchant-Marine-Academy-Grecia.pdf` | SMCP_DATA/docs/ | 🟡 补充 | 关键章节导入 |
| `SMCP.md` | SMCP_DATA/ | 🟢 快速索引 | 优先导入 |

### 3.2 知识图谱实体规划

LightRAG 将从文档中自动提取并建立以下实体网络：

```
SMCP_Phrase ──────── Procedure ──────── Situation
    │                    │                   │
    ▼                    ▼                   ▼
Signal/Call         Safety_Level        Vessel_Type
    │                    │                   │
    ▼                    ▼                   ▼
VHF_Channel         IMO_Reference       Communication_Role
```

---

## 4. 详细任务分解（WBS）

### Sprint 7.1: LightRAG 部署与验证（第 1-2 天）

#### Task 7.1.1: 安装 LightRAG 依赖
- [ ] 在 `lightrag/` 目录创建 Python 虚拟环境：`python -m venv .venv`
- [ ] 安装依赖：`.venv\Scripts\pip install -e ".[api]"`
- [ ] 验证安装：`lightrag-server --version` 或 `.venv\Scripts\lightrag-server --version`

#### Task 7.1.2: 构建前端 WebUI
- [ ] 安装 bun：`npm install -g bun` 或 `irm bun.sh/install.ps1 | iex`
- [ ] 进入前端目录：`cd lightrag/lightrag_webui`
- [ ] 安装依赖：`bun install --frozen-lockfile` （或 `npm install`）
- [ ] 构建产物：`bun run build` （或 `npm run build`）
- [ ] 验证构建：`dist/` 目录存在且有 `index.html`

#### Task 7.1.3: 配置 .env 文件
- [ ] 确认 `lightrag/.env` 配置（已创建）
- [ ] 重点检查：`LLM_BINDING_API_KEY`、`EMBEDDING_MODEL`、`EMBEDDING_DIM`
- [ ] 创建 `inputs/` 和 `rag_storage/` 目录
- [ ] 运行安全检查（可选）

#### Task 7.1.4: 启动服务验证
- [ ] 启动服务：`cd lightrag && .venv\Scripts\lightrag-server`
- [ ] 访问 WebUI：http://localhost:9621
- [ ] 测试 API 健康检查：`curl http://localhost:9621/health`
- [ ] 创建启动脚本 `lightrag/start_server.ps1`

**验收标准：** WebUI 可访问，/health 返回 200

---

### Sprint 7.2: SMCP 知识库导入（第 3-4 天）

#### Task 7.2.1: 文档预处理
- [ ] 确认 `SMCP_DATA/docs/` 中的三个 PDF 文件可正常打开
- [ ] 将 `SMCP_DATA/SMCP.md` 拷贝为 `lightrag/inputs/smcp_phrases.md`
- [ ] 将三个 PDF 拷贝到 `lightrag/inputs/`

#### Task 7.2.2: 通过 WebUI 导入文档
- [ ] 访问 LightRAG WebUI → Documents 页
- [ ] 上传 `smcp_phrases.md`（最优先，处理最快）
- [ ] 上传 `smcp.pdf`
- [ ] 上传 `A.918(22).pdf`
- [ ] 监控处理进度（需要 5-15 分钟/文档，受 LLM API 速率限制）

#### Task 7.2.3: 知识图谱验证
- [ ] 在 WebUI → Graph 视图查看实体关系图
- [ ] 在 WebUI → Query 执行测试查询：
  - `"What is the SMCP phrase for establishing communication with VTS?"`
  - `"Explain the distress signal procedure in SMCP"`
- [ ] 确认返回内容引用标准短语

**验收标准：** 查询可返回 IMO SMCP 原文短语，知识图谱包含 ≥50 个实体节点

---

### Sprint 7.3: RAGClient 开发（第 5-6 天）

#### Task 7.3.1: 创建 RAG 子包
- [ ] 创建 `src/nautical_english/rag/__init__.py`
- [ ] 创建 `src/nautical_english/rag/config.py`（LightRAG 连接配置）
- [ ] 创建 `src/nautical_english/rag/client.py`（HTTP 客户端）

**`config.py` 关键内容：**
```python
from pydantic import BaseSettings

class RAGConfig(BaseSettings):
    host: str = "http://localhost:9621"
    timeout: int = 30
    enabled: bool = True
    query_mode: str = "mix"  # naive | local | global | mix | hybrid
    top_k: int = 5

    class Config:
        env_prefix = "LIGHTRAG_"
```

**`client.py` 关键内容：**
```python
import httpx

class RAGClient:
    def __init__(self, config: RAGConfig): ...
    
    def query(self, question: str, mode: str = "mix") -> str:
        """同步查询 LightRAG，返回相关知识文本"""
        ...
    
    def is_healthy(self) -> bool:
        """检查 LightRAG Server 是否在线"""
        ...
```

#### Task 7.3.2: 单元测试 RAGClient
- [ ] 创建 `tests/test_rag_client.py`
- [ ] 测试：健康检查（mock http）
- [ ] 测试：查询返回格式正确
- [ ] 测试：LightRAG 离线时降级处理（返回空字符串，不抛异常）

---

### Sprint 7.4: CoachService + Prompt 增强（第 7-8 天）

#### Task 7.4.1: 增强 Prompt 模板

修改 `src/nautical_english/coach/prompts.py`，新增支持 RAG 上下文的版本：

```python
def build_system_prompt_with_rag(
    scenario_name: str,
    role_description: str,
    opening_line: str,
    difficulty: str,
    rag_context: str = "",  # 新增参数
) -> str:
    base = build_system_prompt(scenario_name, role_description, opening_line, difficulty)
    if not rag_context:
        return base
    return base + f"""

## SMCP Reference Knowledge
The following standard phrases and procedures are retrieved from IMO SMCP knowledge base.
Use these as authoritative reference when generating your responses and evaluations:

{rag_context}

Always prefer these official SMCP phrases over improvised language.
"""
```

#### Task 7.4.2: 增强 CoachService

修改 `src/nautical_english/coach/service.py`：

```python
class CoachService:
    def __init__(
        self,
        ...,
        rag_client: Optional[RAGClient] = None,  # 新增可选参数
    ):
        self._rag = rag_client
    
    def _build_augmented_messages(self, student_text: str) -> list[LLMMessage]:
        """query RAG then inject context into system message"""
        rag_context = ""
        if self._rag and self._rag.is_healthy():
            try:
                rag_context = self._rag.query(
                    f"SMCP phrases and procedures for: {student_text}",
                    mode="mix"
                )
            except Exception:
                pass  # 静默降级：无 RAG 时使用原有 prompt
        
        # 重建系统 prompt（含 RAG 上下文）
        augmented = self._messages.copy()
        if rag_context:
            augmented[0] = {
                "role": "system",
                "content": build_system_prompt_with_rag(..., rag_context=rag_context)
            }
        return augmented
```

**设计原则（降级安全）：**  
- LightRAG Server 离线 → 自动降级到无 RAG 模式，不影响对话功能
- RAG 查询超时 → 跳过 RAG，使用原有 prompt
- RAG 返回空 → 正常使用原有 prompt

#### Task 7.4.3: 集成测试

- [ ] `tests/integration/test_coach_with_rag.py`
- [ ] 测试：RAG 在线时 prompt 包含上下文
- [ ] 测试：RAG 离线时对话正常运行（降级测试）
- [ ] 测试：完整 2 轮对话流程（mock LightRAG + mock LLM）

---

### Sprint 7.5: App 配置集成（第 9 天）

#### Task 7.5.1: 应用启动集成

修改 `src/main.py`，在应用启动时初始化 RAGClient：

```python
from nautical_english.rag.client import RAGClient
from nautical_english.rag.config import RAGConfig

def _create_rag_client() -> Optional[RAGClient]:
    """尝试连接 LightRAG，若未启动则返回 None（降级模式）"""
    cfg = RAGConfig()
    if not cfg.enabled:
        return None
    client = RAGClient(cfg)
    if client.is_healthy():
        log.info("LightRAG Server 已连接 (%s)", cfg.host)
        return client
    log.warning("LightRAG Server 不可用，以无 RAG 模式运行")
    return None
```

#### Task 7.5.2: 配置 .env

在主项目 `.env` 中新增：
```
# LightRAG 集成配置
LIGHTRAG_HOST=http://localhost:9621
LIGHTRAG_ENABLED=true
LIGHTRAG_QUERY_MODE=mix
LIGHTRAG_TOP_K=5
LIGHTRAG_TIMEOUT=15
```

---

### Sprint 7.6: 启动脚本与文档（第 10 天）

#### Task 7.6.1: 创建 LightRAG 启动脚本

`lightrag/start_server.ps1`：
```powershell
# SMCP 知识库服务启动脚本
Write-Host "启动 LightRAG SMCP 知识库服务..."
Set-Location $PSScriptRoot
.\.venv\Scripts\lightrag-server
```

#### Task 7.6.2: 知识库上传操作说明书（独立文档）

详见 `docs/lightrag_upload_guide.md`

---

## 5. 质量保证

### 5.1 测试矩阵

| 测试类型 | 文件 | 覆盖场景 |
|----------|------|----------|
| 单元测试 | `tests/test_rag_client.py` | RAGClient 正常/异常/降级 |
| 单元测试 | `tests/test_prompts.py` | RAG 上下文注入 |
| 集成测试 | `tests/integration/test_coach_rag.py` | 端到端对话含 RAG |
| 手动测试 | WebUI 查询测试 | 知识库查询质量 |

### 5.2 验收标准清单

- [ ] LightRAG Server 启动时间 < 30 秒
- [ ] SMCP 知识库查询响应 < 5 秒
- [ ] Coach 对话第一回合响应 < 10 秒（含 RAG）
- [ ] LightRAG 离线时，训练功能正常运行（降级测试通过）
- [ ] SMCP 标准短语查询准确率 ≥80%（人工评估 10 个测试问题）
- [ ] 知识图谱节点数 ≥ 100

---

## 6. 风险管理

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| ZhipuAI API 速率限制导致文档处理超时 | 🟡 中 | 🟡 中 | 减小 MAX_ASYNC=2, MAX_PARALLEL_INSERT=1 |
| PDF 解析失败（加密/特殊格式） | 🟡 中 | 🟡 中 | 先用文本版导入，PDF 作为补充 |
| LLM 提取实体质量不佳 | 🟡 中 | 🔴 高 | 使用 glm-4-plus 而非 flash 版本 |
| RAG 查询延迟影响对话体验 | 🟡 中 | 🟡 中 | 异步 RAG 查询 + 超时降级 |
| 知识图谱构建成本 | 🟡 中 | 🟡 中 | 每文档约 1000-3000 token，总计约 50K token |

---

## 7. 进度跟踪

| Sprint | 周期 | 状态 | 里程碑 |
|--------|------|------|--------|
| 7.1 | Day 1-2 | 🔄 进行中 | LightRAG Server 启动 ✓ |
| 7.2 | Day 3-4 | ⏸ 待开始 | SMCP 知识库导入 |
| 7.3 | Day 5-6 | ⏸ 待开始 | RAGClient 开发 |
| 7.4 | Day 7-8 | ⏸ 待开始 | Coach 增强 |
| 7.5 | Day 9 | ⏸ 待开始 | App 集成 |
| 7.6 | Day 10 | ⏸ 待开始 | 文档 + 交付 |

---

## 8. 与现有 Phase 1-6 的接口契约

### 8.1 向后兼容承诺
- `CoachService` 接口签名不变（`rag_client` 为可选参数）
- 无 RAG 时行为与 Phase 6 完全相同
- 所有现有 Phase 1-6 测试必须保持通过

### 8.2 新增接口

```
GET  http://localhost:9621/health          # LightRAG 健康检查
POST http://localhost:9621/query          # 查询知识库
POST http://localhost:9621/documents/upload # 上传新文档（管理使用）
GET  http://localhost:9621/              # WebUI 首页
```

---

*文档版本：1.0 | 状态：已批准 | 下次评审：Phase 7.2 完成后*
