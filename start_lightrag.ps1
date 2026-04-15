# SMCP LightRAG 知识库服务启动脚本
# 使用方法：在项目根目录运行：.\start_lightrag.ps1
# 前提：已完成 lightrag/ 目录的安装（参考 docs/lightrag_upload_guide.md）
#   1. git clone https://github.com/HKUDS/LightRAG.git lightrag
#   2. cd lightrag && uv pip install -e ".[api]"（或 pip install -e ".[api]"）
#   3. 复制 lightrag/.env.example 为 lightrag/.env 并填入 API Key

param(
    [int]$Port = 9621,
    [int]$EmbedPort = 9622
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LightragDir = Join-Path $ProjectRoot "lightrag"
Set-Location $LightragDir

Write-Host "=== SMCP LightRAG 知识库服务启动 ===" -ForegroundColor Cyan

# Step 1: 启动本地 embedding 服务器（后台）
Write-Host "[1/2] 启动本地 Embedding 服务 (端口 $EmbedPort)..." -ForegroundColor Yellow
$EmbedScript = Join-Path $ProjectRoot "local_embedding_server.py"
$PythonExe = Join-Path $LightragDir ".venv\Scripts\python.exe"

Start-Process -FilePath $PythonExe -ArgumentList $EmbedScript -WindowStyle Minimized
Start-Sleep -Seconds 4

try {
    $health = Invoke-RestMethod -Uri "http://localhost:$EmbedPort/health" -TimeoutSec 5
    Write-Host "    Embedding 服务就绪: $($health.model) (dim=$($health.dim))" -ForegroundColor Green
} catch {
    Write-Warning "Embedding 服务未响应，LightRAG 将无法处理新文档"
}

# Step 2: 启动 LightRAG 服务器（前台）
Write-Host "[2/2] 启动 LightRAG Server (端口 $Port)..." -ForegroundColor Yellow
Write-Host "    WebUI: http://localhost:$Port/webui" -ForegroundColor Cyan
Write-Host "    API:   http://localhost:$Port/docs" -ForegroundColor Cyan
Write-Host ""

$ServerExe = Join-Path $LightragDir ".venv\Scripts\lightrag-server.exe"
& $ServerExe --host 0.0.0.0 --port $Port
