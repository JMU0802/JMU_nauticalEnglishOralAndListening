# LightRAG 知识库上传操作说明书
## SMCP 航海英语标准通信短语知识库建设指南

**版本：** v1.0  
**日期：** 2026年4月15日  
**适用对象：** 系统管理员 / 内容维护人员  
**服务地址：** http://localhost:9621

---

## 目录

1. [前置条件检查](#1-前置条件检查)
2. [启动 LightRAG 服务](#2-启动-lightrag-服务)
3. [访问 WebUI 管理界面](#3-访问-webui-管理界面)
4. [上传 SMCP 知识文档](#4-上传-smcp-知识文档)
5. [监控文档处理进度](#5-监控文档处理进度)
6. [知识图谱验证](#6-知识图谱验证)
7. [查询测试](#7-查询测试)
8. [常见问题处理](#8-常见问题处理)
9. [REST API 上传方式（高级）](#9-rest-api-上传方式高级)

---

## 1. 前置条件检查

在上传文档前，请确认以下条件已满足：

### 1.1 环境检查清单

```
✅ LightRAG 依赖已安装（lightrag/.venv 目录存在）
✅ lightrag/.env 文件已配置（API Key、模型参数）
✅ lightrag/lightrag_webui/dist 目录存在（前端已构建）
✅ ZhipuAI API Key 有效且有足够余额
✅ 网络可访问 open.bigmodel.cn
```

### 1.2 确认配置文件

打开 `lightrag/.env`，确认以下关键配置：

```env
# LLM 配置（用于知识图谱实体抽取）
LLM_BINDING_HOST=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4-plus
LLM_BINDING_API_KEY=5f8fe3c322224510bad4dbc37ae2126f.IKlZe0uRvomQnllC

# Embedding 配置（用于向量检索）
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIM=2048
EMBEDDING_BINDING_API_KEY=5f8fe3c322224510bad4dbc37ae2126f.IKlZe0uRvomQnllC
```

> ⚠️ **警告：** `EMBEDDING_MODEL` 和 `EMBEDDING_DIM` 一旦首次导入文档后**不可更改**，
> 否则需要删除 `lightrag/rag_storage/` 目录重新建立知识库，所有已导入文档将丢失。

---

## 2. 启动 LightRAG 服务

### 方法一：使用启动脚本（推荐）

在 Windows PowerShell 中运行：

```powershell
# 进入 lightrag 目录
cd F:\AI_CODING\JMU_nauticalEnglishOralAndListening\lightrag

# 激活虚拟环境并启动服务
.\.venv\Scripts\Activate.ps1
lightrag-server
```

启动成功后终端显示类似：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9621 (Press CTRL+C to quit)
```

### 方法二：后台启动（保留终端）

```powershell
cd F:\AI_CODING\JMU_nauticalEnglishOralAndListening\lightrag
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\lightrag-server.exe"
```

### 验证服务状态

```powershell
# 检查端口是否监听
netstat -an | findstr "9621"

# 或通过 curl 检查
curl http://localhost:9621/health
# 期望返回: {"status":"ok","..."}
```

---

## 3. 访问 WebUI 管理界面

### 3.1 打开浏览器

在 Windows 浏览器（Edge/Chrome）中访问：

```
http://localhost:9621
```

页面加载后显示 LightRAG WebUI 界面，包含以下主要功能区：

```
┌─────────────────────────────────────────────────────────┐
│  🔮 SMCP 航海英语知识库        [搜索...]  [设置]  [?]   │
├─────────────────────────────────────────────────────────┤
│  📄 Documents  |  🕸 Graph  |  💬 Chat  |  📊 Stats    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│          主要内容区域                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 界面导航说明

| 菜单 | 功能 |
|------|------|
| **Documents** | 文档管理、上传、删除、状态查看 |
| **Graph** | 知识图谱可视化（实体关系网络） |
| **Chat/Query** | 直接查询知识库 |
| **Stats** | 文档数量、实体数、关系数统计 |

---

## 4. 上传 SMCP 知识文档

### 4.1 准备上传文件

确认以下文件存在：

```
SMCP_DATA/
├── SMCP.md                     # ✅ Markdown 格式，优先上传（处理最快）
└── docs/
    ├── smcp.pdf                # ✅ SMCP 标准短语 PDF
    ├── A.918(22).pdf           # ✅ IMO A.918(22) 决议 PDF
    └── 3317.-Maritime-English-for-the-Merchant-Marine-Academy-Grecia.pdf  # ✅ 航海英语教材
```

### 4.2 上传步骤

#### 步骤一：进入 Documents 页

点击顶部菜单 **📄 Documents**，页面显示文档列表（初始为空）。

```
┌─────────────────────────────────────────────────────────┐
│  Documents                              [+ Upload]       │
├─────────────────────────────────────────────────────────┤
│  (empty) 暂无文档                                        │
└─────────────────────────────────────────────────────────┘
```

#### 步骤二：点击 Upload 按钮

点击右上角 **[+ Upload]** 按钮，出现上传对话框：

```
┌─────────────────────────────────────────────────────────┐
│  Upload Documents                              [×]       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  拖拽文件到此处，或点击选择文件                    │   │
│  │  支持格式：.txt .md .pdf .docx .html             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  [取消]                              [Upload Files]      │
└─────────────────────────────────────────────────────────┘
```

#### 步骤三：按顺序上传文档

> 📌 **推荐上传顺序：** 处理速度快的文档先上传，便于快速验证系统工作正常

**第1批（优先）：**
- 选择文件：`SMCP_DATA/SMCP.md`
- 点击 **[Upload Files]**
- 等待状态变为 "Processing..."

**第2批：**
- 选择文件：`SMCP_DATA/docs/smcp.pdf`
- 点击 **[Upload Files]**

**第3批：**
- 选择文件：`SMCP_DATA/docs/A.918(22).pdf`
- 点击 **[Upload Files]**

**第4批（可选）：**
- 选择文件：`SMCP_DATA/docs/3317.-Maritime-English-for-the-Merchant-Marine-Academy-Grecia.pdf`
- 点击 **[Upload Files]**

### 4.3 处理时间预估

| 文档 | 大小 | 预估处理时间 |
|------|------|------------|
| `SMCP.md` | ~50KB | 2-5 分钟 |
| `smcp.pdf` | ~500KB | 5-15 分钟 |
| `A.918(22).pdf` | ~1MB | 10-20 分钟 |
| 航海英语教材 PDF | ~5MB | 20-60 分钟 |

> ⚠️ **注意：** 处理时间取决于 ZhipuAI API 速率限制。系统已配置 `MAX_ASYNC=2`，
> 可以同时提交多个文档，但实际并发处理受 API 配额限制。

---

## 5. 监控文档处理进度

### 5.1 WebUI 状态监控

Documents 页面会实时更新每个文档的处理状态：

```
┌─────────────────────────────────────────────────────────────────┐
│  Documents                                        [+ Upload]     │
├────────────┬──────────────┬──────────┬──────────────────────────┤
│ 文件名      │ 上传时间      │ 大小     │ 状态                      │
├────────────┼──────────────┼──────────┼──────────────────────────┤
│ SMCP.md    │ 14:30:01    │ 48 KB   │ ✅ Completed (2m 15s)     │
│ smcp.pdf   │ 14:32:00    │ 512 KB  │ 🔄 Processing... 45%      │
│ A.918.pdf  │ 14:33:00    │ 1.2 MB  │ ⏳ Pending                │
└────────────┴──────────────┴──────────┴──────────────────────────┘
```

状态说明：
- `⏳ Pending` — 排队等待处理
- `🔄 Processing...` — 正在进行实体抽取（显示百分比）
- `✅ Completed` — 处理完成，已加入知识图谱
- `❌ Failed` — 处理失败（见[常见问题](#8-常见问题处理)）

### 5.2 通过 API 查询处理状态

```powershell
# 查询所有文档状态
$response = Invoke-RestMethod -Uri "http://localhost:9621/documents/paginated" -Method Get
$response.data | Format-Table file_name, status, created_at
```

### 5.3 终端日志监控

在 LightRAG 启动的终端窗口，可以看到详细处理日志：

```
INFO: Processing document: SMCP.md
INFO: Extracting entities from chunk 1/5...
INFO: Found 23 entities, 41 relations in chunk 1
INFO: Extracting entities from chunk 2/5...
...
INFO: SMCP.md processed successfully: 89 entities, 156 relations
```

---

## 6. 知识图谱验证

### 6.1 查看知识图谱可视化

所有文档处理完成后，点击顶部菜单 **🕸 Graph**：

```
┌─────────────────────────────────────────────────────────────────┐
│  Knowledge Graph                    [Layout ▼] [Filter] [Export]│
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│    [MAYDAY]──────────[Distress_Procedure]                        │
│       │                      │                                    │
│    [PAN PAN]          [VHF_Channel_16]──[Calling_Procedure]      │
│       │                      │                                    │
│    [SECURITE]         [Vessel_Traffic_Service]                   │
│                              │                                    │
│    [SMCP_Phrase]─────[Standard_Call_Format]──[Response_Format]  │
│                                                                   │
│  节点数: 234  |  关系数: 512                                      │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准：** 节点数 ≥ 50（理想状态 ≥ 200）

### 6.2 节点交互

- **点击节点** — 查看实体详情和相关描述
- **拖拽** — 调整布局
- **滚轮缩放** — 放大/缩小图谱
- **搜索框** — 搜索特定实体（如输入 "MAYDAY"）

---

## 7. 查询测试

### 7.1 WebUI 查询界面

点击 **💬 Chat** 或 **Query** 标签，测试知识库质量：

```
┌─────────────────────────────────────────────────────────────────┐
│  Query Knowledge Base                  Mode: [Mix ▼]             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  How do I call Xiamen VTS on VHF channel 16?                    │
│                                                              [↵] │
├─────────────────────────────────────────────────────────────────┤
│  Answer:                                                          │
│  According to SMCP standards, the initial call to a VTS should  │
│  follow the format:                                              │
│  "[VTS name], this is [vessel name], [vessel call sign], over."  │
│  ...                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 推荐测试查询

按以下列表逐一测试，验证知识库质量：

| # | 测试查询 | 期望包含的关键词 |
|---|---------|---------------|
| 1 | What is the standard format for calling a port authority? | "this is", "vessel name", "call sign", "over" |
| 2 | How to send a distress signal using SMCP? | "MAYDAY MAYDAY MAYDAY", "channel 16" |
| 3 | What phrases are used for reporting vessel position? | "bearing", "position", "north/south", latitude/longitude |
| 4 | Explain the PAN PAN urgency signal | "PAN PAN PAN", "urgency", "medical" |
| 5 | What is the SMCP response to a vessel request? | "roger", "wilco", "standby" |

### 7.3 查询模式说明

| 模式 | 适用场景 | 速度 |
|------|---------|------|
| `naive` | 简单向量检索，类似传统 RAG | 快 |
| `local` | 本地实体关系检索 | 中 |
| `global` | 全局主题检索 | 慢 |
| `mix` | 混合检索（推荐） | 中 |
| `hybrid` | 向量+图谱混合 | 中 |

> 💡 **建议：** 在 SMCP 训练系统中使用 `mix` 模式，平衡质量和速度。

---

## 8. 常见问题处理

### ❌ 问题：文档处理失败（Status: Failed）

**排查步骤：**

1. 查看终端日志中的错误信息
2. 常见原因：LLM API 超时（SMCP PDF 较大，实体抽取耗时长）
3. 解决：在 `.env` 中增加超时时间：

```env
LLM_TIMEOUT=180
```

4. 重新上传失败的文档（LightRAG 支持重试）

---

### ❌ 问题：PDF 无法解析

**排查步骤：**

1. 检查 PDF 是否加密：使用 Adobe Acrobat 尝试打开
2. 如果加密，在 `.env` 中设置密码：

```env
PDF_DECRYPT_PASSWORD=your_password
```

3. 备选方案：将 PDF 转为纯文本 `.txt` 再上传

```powershell
# 使用 Python 提取 PDF 文本
python -c "
from pypdf import PdfReader
reader = PdfReader('SMCP_DATA/docs/smcp.pdf')
text = '\n'.join(page.extract_text() for page in reader.pages)
with open('lightrag/inputs/smcp_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print('Done:', len(text), 'chars')
"
```

---

### ❌ 问题：API 速率限制错误

**现象：** 日志中出现 `429 Too Many Requests` 或 `rate limit exceeded`

**解决：**

修改 `lightrag/.env`，降低并发：

```env
MAX_ASYNC=1
MAX_PARALLEL_INSERT=1
```

重启服务后重新上传。

---

### ❌ 问题：WebUI 无法访问

**排查：**
```powershell
# 检查端口
netstat -an | findstr "9621"

# 检查进程
Get-Process -Name "lightrag*" -ErrorAction SilentlyContinue

# 检查 dist 目录
Test-Path "F:\AI_CODING\JMU_nauticalEnglishOralAndListening\lightrag\lightrag_webui\dist"
```

如果 `dist` 目录不存在，需要重新构建前端（见安装说明）。

---

### ❌ 问题：知识库查询返回内容不相关

**可能原因：**
- 文档还未处理完成
- Embedding 维度配置错误

**验证：**
```powershell
curl "http://localhost:9621/documents/paginated"
# 检查所有文档状态都是 "completed"
```

---

## 9. REST API 上传方式（高级）

适合批量上传或脚本自动化场景。

### 9.1 上传单个文件

```powershell
# PowerShell 方式
$form = @{
    'file' = Get-Item -Path 'SMCP_DATA\SMCP.md'
}
Invoke-RestMethod `
    -Uri "http://localhost:9621/documents/upload" `
    -Method Post `
    -Form $form
```

```bash
# curl 方式（需要 curl.exe on Windows）
curl -X POST "http://localhost:9621/documents/upload" \
     -F "file=@SMCP_DATA/SMCP.md"
```

### 9.2 批量上传脚本

```powershell
# batch_upload.ps1 — 批量上传 SMCP 知识库文档
$lightragUrl = "http://localhost:9621"
$docDir = "F:\AI_CODING\JMU_nauticalEnglishOralAndListening\SMCP_DATA"

$files = @(
    "$docDir\SMCP.md",
    "$docDir\docs\smcp.pdf",
    "$docDir\docs\A.918(22).pdf"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "上传: $file"
        $form = @{ 'file' = Get-Item -Path $file }
        $result = Invoke-RestMethod -Uri "$lightragUrl/documents/upload" -Method Post -Form $form
        Write-Host "  状态: $($result.status)" 
    } else {
        Write-Warning "文件不存在: $file"
    }
}

Write-Host "批量上传完成。访问 $lightragUrl 查看处理进度。"
```

### 9.3 查询 API

```powershell
# 文本查询（不走 WebUI，直接 REST API）
$body = @{
    query = "What is the standard VTS call procedure?"
    mode = "mix"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:9621/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.response
```

---

## 附录：SMCP 主项目集成验证

知识库建立后，在主项目 `.env` 中添加以下配置，以启用 RAG 增强对话：

```env
# 在 F:\AI_CODING\JMU_nauticalEnglishOralAndListening\.env 中追加
LIGHTRAG_HOST=http://localhost:9621
LIGHTRAG_ENABLED=true
LIGHTRAG_QUERY_MODE=mix
LIGHTRAG_TIMEOUT=15
```

然后重启主程序，对话教练将自动检测 LightRAG 服务并使用 RAG 增强。

---

*文档版本：1.0 | 维护人：系统管理员 | 最后更新：2026年4月15日*
