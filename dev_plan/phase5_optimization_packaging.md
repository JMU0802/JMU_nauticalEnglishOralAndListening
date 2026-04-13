# Phase 5 开发计划 — 优化、测试与 Windows 打包

**周期：** 第 10-12 周（Sprint 10, 11 & 12）  
**前置条件：** Phase 4 全部验收通过，完整 UI 可正常运行一次训练。  
**目标：** 性能优化（模型预加载 + 缓存）、达到 ≥70% 测试覆盖率、PyInstaller 打包为 Windows 独立安装包。  
**完成标准：** 可在无 Python 环境的 Windows PC 上安装并运行；整体评分响应时间 ≤10 秒（不含首次 Whisper 加载）。

---

## 📦 本阶段交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| 性能优化 | `src/nautical_english/` 各模块 | 懒加载、缓存、并发预热 |
| 全量单元测试补全 | `tests/` | 覆盖率 ≥70% |
| 主 spec 文件 | `scripts/nautical_trainer.spec` | PyInstaller 构建配置 |
| Windows 安装包 | `dist/NauticalTrainer_Setup.exe` | Inno Setup 或 NSIS |
| 用户手册 | `docs/user_manual.md` | 安装 + 使用说明（中文） |
| 开发者文档 | `docs/developer_guide.md` | 模块说明、扩展指南 |

---

## 🛠️ Task 5.1 — 性能基准测试

在优化之前先建立基准。

### Step 1：创建性能测试脚本

新建 `scripts/benchmark.py`：

```python
"""性能基准测试脚本

测量端到端各阶段耗时，为优化提供数据依据。

用法：
    python scripts/benchmark.py
"""
import sys
import time
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nautical_english.config import AppConfig
from nautical_english.asr.recognizer import WhisperRecognizer
from nautical_english.tts.synthesizer import TTSSynthesizer
from nautical_english.nlp.matcher import SentenceMatcher
from nautical_english.corpus.repository import CorpusRepository


def measure(label: str, func, *args, **kwargs):
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"  {label:<35s} {elapsed:6.2f}s")
    return result


cfg = AppConfig()
print("=" * 52)
print("  性能基准测试")
print("=" * 52)

repo = CorpusRepository()
phrases = [p.phrase_en for p in repo.get_all_phrases()]

# 1. 模型加载
recognizer = measure("Whisper 模型加载", WhisperRecognizer, cfg.whisper_model_size)
matcher = measure("SBERT 模型加载 + 编码", SentenceMatcher, phrases)
synth = measure("TTS 模型加载", TTSSynthesizer)

# 2. 推理延迟
dummy_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.05
measure("Whisper 转录 (3s 音频)", recognizer.transcribe, dummy_audio, 16000)
measure("SBERT 匹配", matcher.find_best_match, "alter course to starboard")
measure("TTS 合成", synth.synthesize, "Alter course to starboard",
        Path("corpus/db/tmp/benchmark_out.wav"))

print("=" * 52)
print("基准测试完成。将以上数据保存到 docs/ 作为优化前基线。")
```

### Step 2：运行并记录基准数据

```bash
python scripts/benchmark.py > docs/performance_baseline.txt
cat docs/performance_baseline.txt
```

### Step 3：提交

```bash
git add scripts/benchmark.py docs/performance_baseline.txt
git commit -m "perf: add benchmark script and record baseline"
```

---

## 🛠️ Task 5.2 — 模型预加载与缓存优化

### Step 1：应用启动时并行预热

更新 `src/main.py` 中的模型加载逻辑，使用 QThread 在后台预热：

```python
class ModelLoadThread(QThread):
    """应用启动时在 splash screen 期间异步加载重型模型"""
    loaded = pyqtSignal(object, object, object)  # recognizer, matcher, synth
    error = pyqtSignal(str)

    def __init__(self, cfg: AppConfig, phrases_en: list[str]):
        super().__init__()
        self._cfg = cfg
        self._phrases = phrases_en

    def run(self):
        try:
            from nautical_english.asr.recognizer import WhisperRecognizer
            from nautical_english.nlp.matcher import SentenceMatcher
            from nautical_english.tts.synthesizer import TTSSynthesizer
            r = WhisperRecognizer(self._cfg.whisper_model_size)
            m = SentenceMatcher(self._phrases)
            t = TTSSynthesizer()
            self.loaded.emit(r, m, t)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
```

### Step 2：SentenceMatcher 缓存查询结果

在 `src/nautical_english/nlp/matcher.py` 中添加简单的 LRU 缓存：

```python
from functools import lru_cache

class SentenceMatcher:
    # ...已有代码...

    @lru_cache(maxsize=256)
    def find_best_match(self, query: str) -> MatchResult:
        # lru_cache 要求 query 是 hashable（str 天然满足）
        return self._find_best_match_impl(query)

    def _find_best_match_impl(self, query: str) -> MatchResult:
        # 将原 find_best_match 的实现移到这里
        ...
```

> ⚠️ 注意：如果 `find_best_match` 返回 `MatchResult` 对象，需确认它是 hashable/frozen dataclass，
> 否则 `lru_cache` 无法工作。推荐直接缓存 `query → result` 用 `dict` 代替：

```python
class SentenceMatcher:
    def __init__(self, phrases):
        # ...原初始化代码...
        self._cache: dict[str, MatchResult] = {}

    def find_best_match(self, query: str) -> MatchResult:
        if query in self._cache:
            return self._cache[query]
        result = self._find_best_match_impl(query)
        self._cache[query] = result
        return result
```

### Step 3：TTS 音频文件缓存

在 `TTSSynthesizer.synthesize()` 中添加文件级缓存，相同文本不重复生成：

```python
import hashlib

class TTSSynthesizer:
    def __init__(self, cache_dir: Path | None = None):
        # ...原代码...
        self._cache_dir = cache_dir or Path("corpus/db/tts_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, out_path: Path | None = None) -> Path:
        # 基于文本 hash 的缓存键
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        cached = self._cache_dir / f"{text_hash}.wav"
        if cached.exists():
            return cached
        target = out_path or cached
        target.parent.mkdir(parents=True, exist_ok=True)
        self._tts.tts_to_file(text=text, file_path=str(target))
        return target
```

### Step 4：验证优化效果

```bash
python scripts/benchmark.py > docs/performance_optimized.txt
python -c "
import re
def get_times(f):
    return {m[1]: float(m[2]) for m in re.finditer(r'(.*?)\s+(\d+\.\d+)s', open(f).read())}
baseline = get_times('docs/performance_baseline.txt')
optimized = get_times('docs/performance_optimized.txt')
for k in baseline:
    if k in optimized:
        diff = optimized[k] - baseline[k]
        pct = diff / baseline[k] * 100
        print(f'{k[:40]:40s}: {pct:+.1f}%')
"
```

---

## 🛠️ Task 5.3 — 测试覆盖率补全

### Step 1：当前覆盖率检查

```bash
pytest tests/ --cov=nautical_english --cov-report=term-missing --cov-report=html:htmlcov -v
```

查看 `htmlcov/index.html` 找出未覆盖的关键代码路径。

### Step 2：补充缺失测试

根据覆盖率报告，优先补充以下常见遗漏项：

#### `tests/test_asr/test_recognizer.py` 补充

```python
def test_transcribe_with_empty_segment_list(mock_recognizer):
    """Whisper 返回空段列表时不抛出"""
    with patch("faster_whisper.WhisperModel") as MockModel:
        m = MockModel.return_value
        m.transcribe.return_value = ([], MagicMock(language="en"))
        r = WhisperRecognizer.__new__(WhisperRecognizer)
        r._model = m
        result = r.transcribe(np.zeros(16000, dtype=np.float32), 16000)
        assert result == ""

def test_transcribe_strips_whitespace(mock_recognizer):
    seg = MagicMock()
    seg.text = "  Alter course  "
    with patch("faster_whisper.WhisperModel") as MockModel:
        m = MockModel.return_value
        m.transcribe.return_value = ([seg], MagicMock(language="en"))
        r = WhisperRecognizer.__new__(WhisperRecognizer)
        r._model = m
        result = r.transcribe(np.zeros(16000, dtype=np.float32), 16000)
        assert result == "alter course"
```

#### `tests/test_nlp/test_matcher.py` 补充

```python
def test_find_best_match_empty_query():
    matcher = SentenceMatcher(["Alter course to starboard", "Stand by engine"])
    result = matcher.find_best_match("")
    # 空 query 应返回结果，不抛异常
    assert result is not None

def test_find_best_match_caches_result():
    matcher = SentenceMatcher(["Alter course to starboard"])
    r1 = matcher.find_best_match("alter course")
    r2 = matcher.find_best_match("alter course")
    assert r1 is r2  # 同一对象（缓存命中）
```

### Step 3：覆盖率目标验证

```bash
pytest tests/ --cov=nautical_english --cov-fail-under=70 -q
```

**预期：** `Required test coverage of 70% reached.`

### Step 4：提交

```bash
git add tests/
git commit -m "test: add missing tests to reach 70% coverage"
```

---

## 🛠️ Task 5.4 — PyInstaller 打包

### Step 1：运行打包脚本（生成 spec）

```bash
python scripts/build_installer.py --spec-only
```

### Step 2：检查并编辑 spec 文件

打开 `scripts/nautical_trainer.spec`，确认以下关键配置：

```python
# nautical_trainer.spec 关键配置
a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("src/nautical_english/ui/resources/styles.qss", "nautical_english/ui/resources"),
        ("corpus/db/corpus.db", "corpus/db"),           # 内嵌语料库
        ("SMCP_DATA/audioFile", "SMCP_DATA/audioFile"), # 内嵌标准音频
        # 注意：不内嵌 AI 模型（太大），改用运行时加载路径
    ],
    hiddenimports=[
        "nautical_english",
        "nautical_english.asr",
        "nautical_english.tts",
        "nautical_english.nlp",
        "nautical_english.corpus",
        "nautical_english.feedback",
        "nautical_english.training",
        "nautical_english.ui",
        "sounddevice",
        "faster_whisper",
        "sentence_transformers",
        "sqlalchemy.dialects.sqlite",
    ],
    ...
)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name="NauticalTrainer",
    debug=False,
    upx=True,
    console=False,        # 不显示黑框
    icon="docs/icon.ico", # 应用图标（可选）
)
```

### Step 3：执行完整打包

```bash
pyinstaller scripts/nautical_trainer.spec --clean --noconfirm
```

若出现 `ModuleNotFoundError` 相关错误，将缺失模块加入 `hiddenimports`。

### Step 4：测试打包结果（无 Python 环境 VM 中测试）

```bash
# 临时 PATH 干净环境测试（排除当前 Python）
$originalPath = $env:PATH
$env:PATH = "C:\Windows\System32"
.\dist\NauticalTrainer\NauticalTrainer.exe
$env:PATH = $originalPath
```

或者将 `dist/NauticalTrainer/` 文件夹复制到另一台没有 Python 的 Windows 机器测试。

### Step 5：创建 Inno Setup 脚本（可选）

新建 `scripts/installer.iss`（需安装 Inno Setup 6）：

```iss
[Setup]
AppName=Maritime English Trainer
AppVersion=0.1.0
AppPublisher=JMU
DefaultDirName={autopf}\NauticalTrainer
DefaultGroupName=NauticalTrainer
OutputDir=dist
OutputBaseFilename=NauticalTrainer_Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\NauticalTrainer\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Maritime English Trainer"; Filename: "{app}\NauticalTrainer.exe"
Name: "{commondesktop}\Maritime English Trainer"; Filename: "{app}\NauticalTrainer.exe"

[Run]
Filename: "{app}\NauticalTrainer.exe"; Description: "Launch Maritime English Trainer"; Flags: nowait postinstall
```

编译安装包：

```bash
# 需要 Inno Setup 6 可执行文件在 PATH 中
iscc scripts/installer.iss
```

### Step 6：提交

```bash
git add scripts/ dist/ -f  # 注意：通常不提交 dist/ 到 Git，除非有 CI/CD 需要
git commit -m "build: add PyInstaller spec and installer script"
```

---

## 🛠️ Task 5.5 — 用户手册与文档

### Step 1：创建用户手册

新建 `docs/user_manual.md`：

````markdown
# 航海英语听说训练系统 — 用户手册

## 系统要求
- Windows 10/11 (64位)
- 4GB 内存（推荐 8GB）
- 2GB 可用磁盘空间
- 麦克风（录音功能必须）

## 安装步骤
1. 运行 `NauticalTrainer_Setup.exe`
2. 按照向导提示安装
3. 首次运行需下载 AI 模型（约 1-2GB），请保持网络连接

## 学生端使用
1. 打开程序后点击 **Practice** 选项卡
2. 在左上角下拉菜单中选择训练类别
3. 阅读屏幕显示的英文短语和中文参考
4. 点击红色圆形按钮开始 5 秒录音
5. 说完后查看评分结果和标准参考

## 管理员端使用
1. 点击 **Admin** 选项卡
2. 使用搜索框过滤短语
3. 点击 **+ 新增短语** 添加自定义短语
4. 选中行后点击 **✎ 编辑** 或 **✕ 删除**

## 故障排除
| 症状 | 解决方案 |
|------|----------|
| 未检测到麦克风 | 检查 Windows 声音设置中的录音设备 |
| 评分一直为 0 | 说话音量过低，或麦克风被其他程序占用 |
| 应用无响应（处理中） | 首次识别需要 10-30 秒加载模型，请耐心等待 |
````

### Step 2：最终集成测试检查清单

运行以下完整验收测试：

```bash
# 1. 单元测试
pytest tests/ --cov=nautical_english --cov-fail-under=70 -v

# 2. 主窗口启动
python src/main.py &
sleep 5
# 手动验证窗口出现，无报错

# 3. 演示脚本
python scripts/demo_session.py

# 4. 打包产物
dist\NauticalTrainer\NauticalTrainer.exe
```

---

## ✅ Phase 5 最终验收标准

- [ ] `python scripts/benchmark.py` 输出显示转录端到端 ≤10 秒
- [ ] `pytest --cov-fail-under=70` 通过
- [ ] `dist/NauticalTrainer/NauticalTrainer.exe` 在干净 Windows 环境下可正常启动
- [ ] 测试安装包 `NauticalTrainer_Setup.exe` 安装成功（如选做）
- [ ] `docs/user_manual.md` 已创建且内容完整
- [ ] 所有 git commit 覆盖所有功能（`git log --oneline` 可看到完整历史）

---

## 📊 全项目最终性能目标

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 转录延迟（3秒音频） | ≤5 秒 | `benchmark.py` |
| 端到端响应时间 | ≤10 秒 | 手动秒表 |
| 测试覆盖率 | ≥70% | `pytest --cov` |
| 安装包大小 | ≤500 MB | `dist/` 文件夹大小 |
| 首次启动时间 | ≤30 秒 | 手动计时 |

---

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `PyInstaller` 打包后缺少 DLL | Windows 运行时库 | 确认 Visual C++ Redistributable 已部署；UPX 压缩有时破坏 DLL，尝试 `--upx-exclude=vcruntime*.dll` |
| 打包后 SQLite 数据库消失 | `datas` 路径配置错误 | 检查 spec 文件中 `corpus/db/corpus.db` 的源路径是否相对于 spec 文件位置 |
| 打包后 QSS 样式丢失 | 资源文件未包含 | 确认 `styles.qss` 在 `datas` 列表中，并用 `sys._MEIPASS` 在代码中构建路径 |
| `faster_whisper` 在打包后崩溃 | CTranslate2 C++ 扩展 | 添加 `--collect-all faster_whisper` 到 PyInstaller 命令 |

---

## 📌 项目完成检查

- **最终版本号：** v0.1.0
- **打包完成日期：** ______
- **测试通过率：** ______%
- **安装包路径：** `dist/NauticalTrainer_Setup.exe`
- **已测试的 Windows 版本：** ______
- **备注：** ______

---

## 🎯 后续迭代建议（v0.2.0+）

1. **多学生账户系统** — 登录 + 个人历史记录隔离
2. **在线更新语料库** — 从服务器下载最新 SMCP 短语
3. **自适应训练** — 根据历史错误率自动调整难度
4. **教师批改模式** — 人工标注不合格录音，增强训练集
5. **更好的 TTS** — 替换为 VITS/Bark 等更自然的英语发音模型
6. **发音音素评分** — 集成 Kaldi/ESPnet 的音素级别评估
