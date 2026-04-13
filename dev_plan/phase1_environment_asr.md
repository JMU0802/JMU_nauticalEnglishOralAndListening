# Phase 1 开发计划 — 开发环境 + ASR + 基础窗口

**周期：** 第 1-2 周（Sprint 1 & 2）  
**目标：** 搭建可运行的开发环境，实现麦克风录音与 Whisper 语音识别，打开最小 PyQt6 窗口。  
**完成标准：** 能对着麦克风说一句英语，终端打印出识别文本，PyQt6 窗口正常打开。

---

## 📦 本阶段交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| 项目依赖配置 | `pyproject.toml` / `requirements.txt` | 所有依赖锁定 |
| 全局配置模块 | `src/nautical_english/config.py` | 路径、参数集中管理 |
| 音频录制模块 | `src/nautical_english/asr/audio_capture.py` | sounddevice 录音 |
| ASR 识别模块 | `src/nautical_english/asr/recognizer.py` | faster-whisper 封装 |
| 模型下载脚本 | `scripts/download_models.py` | 一键下载 Whisper 模型 |
| 最小主窗口 | `src/nautical_english/ui/main_window.py` | PyQt6 主窗口骨架 |
| 程序入口 | `src/main.py` | `python main.py` 可启动 |
| 单元测试 | `tests/test_asr/` | ASR 相关测试 |

---

## 🛠️ Task 1.1 — 开发环境配置

> **前提：** 已安装 Python 3.11+、Git、CUDA（可选）

### Step 1：创建并激活虚拟环境

```bash
cd f:\AI_CODING\JMU_nauticalEnglishOralAndListening

# 创建虚拟环境
python -m venv .venv

# Windows 激活
.venv\Scripts\activate
```

### Step 2：安装核心依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ 若有 NVIDIA GPU，额外安装：
> ```bash
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```
nvidia-smi
Mon Apr 13 18:16:01 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.01                 Driver Version: 592.01         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5060 ...  WDDM  |   00000000:02:00.0  On |                  N/A |
| N/A   48C    P4             19W /   49W |    3267MiB /   8151MiB |     12%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A           16652    C+G   ...Chrome\Application\chrome.exe      N/A      |
|    0   N/A  N/A           16936    C+G   ...ms\Microsoft VS Code\Code.exe      N/A      |
|    0   N/A  N/A           18720    C+G   ...8wekyb3d8bbwe\M365Copilot.exe      N/A      |
|    0   N/A  N/A           18748    C+G   ...ntrolPanel\SystemSettings.exe      N/A      |
|    0   N/A  N/A           20108    C+G   ...ainframe\DesktopAssistant.exe      N/A      |
|    0   N/A  N/A           20224    C+G   ...cw5n1h2txyewy\WidgetBoard.exe      N/A      |
|    0   N/A  N/A           27452    C+G   ...2p2nqsd0c76g0\app\ChatGPT.exe      N/A      |
|    0   N/A  N/A           29356    C+G   ...8bbwe\PhoneExperienceHost.exe      N/A      |
|    0   N/A  N/A           30528    C+G   ...ncent\QQBrowser\QQBrowser.exe      N/A      |
|    0   N/A  N/A           31864    C+G   ...crosoft OneDrive\OneDrive.exe      N/A      |
|    0   N/A  N/A           36252    C+G   ...0.3856.109\msedgewebview2.exe      N/A      |
|    0   N/A  N/A           36868    C+G   ...les\Tencent\Weixin\Weixin.exe      N/A      |
|    0   N/A  N/A           38684    C+G   ...SnippingTool\SnippingTool.exe      N/A      |
|    0   N/A  N/A           39032    C+G   ..._cw5n1h2txyewy\SearchHost.exe      N/A      |
|    0   N/A  N/A           40012    C+G   ...4__w2gh52qy24etm\Nahimic3.exe      N/A      |
|    0   N/A  N/A           44696    C+G   ...Chrome\Application\chrome.exe      N/A      |
|    0   N/A  N/A           49700    C+G   ...ms\Microsoft VS Code\Code.exe      N/A      |
|    0   N/A  N/A           50080    C+G   ...2p2nqsd0c76g0\app\ChatGPT.exe      N/A      |
|    0   N/A  N/A           50432    C+G   C:\Windows\explorer.exe               N/A      |
|    0   N/A  N/A           52148    C+G   ...em32\ApplicationFrameHost.exe      N/A      |
|    0   N/A  N/A           57328    C+G   ...2txyewy\CrossDeviceResume.exe      N/A      |
|    0   N/A  N/A           58496    C+G   ...0.3856.109\msedgewebview2.exe      N/A      |
|    0   N/A  N/A           60812    C+G   ...acted\runtime\WeChatAppEx.exe      N/A      |
|    0   N/A  N/A           62396    C+G   ...0.3856.109\msedgewebview2.exe      N/A      |
|    0   N/A  N/A           63696    C+G   ...ogram Files\ToDesk\ToDesk.exe      N/A      |
|    0   N/A  N/A           63888    C+G   ...ows\System32\NahimicSvc64.exe      N/A      |
|    0   N/A  N/A           66716    C+G   ...y\StartMenuExperienceHost.exe      N/A      |
|    0   N/A  N/A           67276    C+G   ...xyewy\ShellExperienceHost.exe      N/A      |
|    0   N/A  N/A           68220    C+G   ...0.3856.109\msedgewebview2.exe      N/A      |
|    0   N/A  N/A           68836    C+G   ...5n1h2txyewy\TextInputHost.exe      N/A      |
|    0   N/A  N/A           69268    C+G   ...indows\System32\ShellHost.exe      N/A      |
+-----------------------------------------------------------------------------------------+
### Step 3：安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### Step 4：验证关键包导入正常

```bash
python -c "import faster_whisper; import PyQt6; import sounddevice; print('All OK')"
```

**预期输出：** `All OK`

### Step 5：初始化 Git 仓库并首次提交

```bash
git init
git add .
git commit -m "chore: init project structure and dependencies"
```

---

## 🛠️ Task 1.2 — 全局配置模块

> 文件已存在：`src/nautical_english/config.py`  
> 本任务验证其正确性。

### Step 1：编写配置测试

新建文件 `tests/test_config.py`：

```python
from nautical_english.config import AppConfig

def test_whisper_model_size_valid():
    cfg = AppConfig()
    assert cfg.whisper_model_size in ("tiny", "small", "medium", "large", "large-v3")

def test_db_path_is_absolute():
    cfg = AppConfig()
    assert cfg.db_path.is_absolute()

def test_score_weights_sum_to_one():
    cfg = AppConfig()
    assert abs(cfg.score_alpha + cfg.score_beta - 1.0) < 1e-6

def test_sample_rate_is_16k():
    cfg = AppConfig()
    assert cfg.sample_rate == 16_000
```

### Step 2：运行测试

```bash
cd f:\AI_CODING\JMU_nauticalEnglishOralAndListening
pytest tests/test_config.py -v
```

**预期：** 4 tests passed

### Step 3：提交

```bash
git add tests/test_config.py
git commit -m "test: add AppConfig unit tests"
```

---

## 🛠️ Task 1.3 — 音频录制模块

> 文件已存在：`src/nautical_english/asr/audio_capture.py`

### Step 1：补充测试文件

编辑 `tests/test_asr/test_audio_capture.py`（若为空则新建）：

```python
from unittest.mock import patch, MagicMock
import numpy as np
from nautical_english.asr.audio_capture import AudioCapture

def test_audio_capture_init():
    cap = AudioCapture(sample_rate=16000)
    assert cap.sample_rate == 16000
    assert cap.channels == 1

def test_get_available_devices_returns_list():
    with patch("nautical_english.asr.audio_capture.sd.query_devices") as mock_qd:
        mock_qd.return_value = [
            {"name": "Mic A", "max_input_channels": 1},
            {"name": "Mic B", "max_input_channels": 2},
            {"name": "Speaker", "max_input_channels": 0},  # 输出设备，应被过滤
        ]
        cap = AudioCapture()
        devices = cap.get_available_devices()
        assert len(devices) == 2  # Speaker 被过滤掉

def test_save_without_record_raises():
    import pytest
    cap = AudioCapture()
    with pytest.raises(ValueError, match="No recording"):
        from pathlib import Path
        cap.save(Path("test.wav"))

def test_load_returns_ndarray(tmp_path):
    import soundfile as sf
    wav_path = tmp_path / "test.wav"
    data = np.zeros(16000, dtype=np.float32)
    sf.write(str(wav_path), data, 16000)
    loaded = AudioCapture.load(wav_path)
    assert isinstance(loaded, np.ndarray)
    assert len(loaded) == 16000
```

### Step 2：运行测试

```bash
pytest tests/test_asr/test_audio_capture.py -v
```

**预期：** 4 tests passed

### Step 3：手动录音验证（可选）

```python
# 在 Python 交互环境中测试
from nautical_english.asr.audio_capture import AudioCapture
from pathlib import Path

cap = AudioCapture()
print("录音 3 秒...")
audio = cap.record(3.0)
cap.save(Path("test_record.wav"))
print(f"录制完成，形状: {audio.shape}")
```

### Step 4：提交

```bash
git add tests/test_asr/
git commit -m "test: add AudioCapture unit tests"
```

---

## 🛠️ Task 1.4 — 下载 Whisper 模型

> ⚠️ 模型较大（large-v3 约 3GB），需要网络连接，**仅需下载一次**。

### Step 1：运行下载脚本

```bash
# 下载 large-v3（效果最好，推荐）
python scripts/download_models.py --model large-v3

# 若磁盘/内存有限，改用 medium（约 1.5GB）
# python scripts/download_models.py --model medium
```

**预期输出：**
```
[Whisper] Downloading 'large-v3' to ...\models\whisper ...
[Whisper] Done.
[SBERT] Downloading 'paraphrase-multilingual-MiniLM-L12-v2' ...
[SBERT] Done.
✅ All models downloaded successfully.
```

### Step 2：验证模型文件存在

```bash
Get-ChildItem models\whisper -Recurse | Select-Object Name
```

---

## 🛠️ Task 1.5 — ASR 识别模块测试

> 文件已存在：`src/nautical_english/asr/recognizer.py`  
> 使用 Mock 测试，**不需要实际加载模型**。

### Step 1：完善测试文件

`tests/test_asr/test_recognizer.py` 已存在，直接运行：

```bash
pytest tests/test_asr/test_recognizer.py -v
```

**预期：** 3 tests passed

### Step 2：集成冒烟测试（需要模型已下载）

```python
# smoke_test_asr.py（临时脚本，测完删除）
from pathlib import Path
from nautical_english.asr.recognizer import WhisperRecognizer
from nautical_english.asr.audio_capture import AudioCapture
from nautical_english.config import AppConfig

cfg = AppConfig()
rec = WhisperRecognizer(
    model_size=cfg.whisper_model_size,
    model_dir=cfg.whisper_model_dir,
)
cap = AudioCapture()

print("开始录音 5 秒，请说英语...")
audio = cap.record(5.0)
text = rec.transcribe(audio)
print(f"识别结果: {text}")
```

**预期：** 能打印出识别的英文文本

### Step 3：提交

```bash
git add tests/test_asr/
git commit -m "test: verify WhisperRecognizer with mock"
```

---

## 🛠️ Task 1.6 — 最小 PyQt6 主窗口

> 文件已存在：`src/nautical_english/ui/main_window.py` 和 `src/main.py`

### Step 1：启动验证

```bash
cd src
python main.py
```

**预期：** 弹出标题为 "Maritime English Trainer — JMU 集美大学" 的深色主题窗口，包含两个标签页。

### Step 2：提交

```bash
git add src/
git commit -m "feat(ui): verify MainWindow launches with ocean blue theme"
```

---

## ✅ Phase 1 验收标准

在提交 Phase 1 完成前，逐项确认：

- [ ] `pytest tests/ -v` 全部通过（无需 AI 模型的测试套件）
- [ ] `python src/main.py` 能打开 PyQt6 窗口
- [ ] Whisper 模型已下载到 `models/whisper/`
- [ ] SBERT 模型已下载
- [ ] 录音 → ASR 冒烟测试通过（手动验证）
- [ ] Git 有至少 3 次规范提交记录

---

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `sounddevice` 无法找到麦克风 | 驱动问题或系统权限 | 运行 `python -c "import sounddevice; print(sounddevice.query_devices())"` 查看设备列表 |
| `PyQt6` 导入报错 | 版本不兼容 | 确保 `pip install PyQt6>=6.7.0` |
| Whisper 模型下载慢 | 网络问题 | 使用 `--model small` 先验证流程，后换 large |
| CUDA 不可用 | 驱动/CUDA 版本 | 在 `config.py` 中将 `whisper_device` 改为 `"cpu"` |

---

## 📌 Phase 1 → Phase 2 交接检查

完成后在此记录：

- **完成日期：** ______
- **实际耗时：** ______
- **Whisper 模型规格：** `______`（tiny/small/medium/large-v3）
- **遇到的主要问题：** ______
- **备注：** ______
