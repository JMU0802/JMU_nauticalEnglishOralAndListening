# Phase 4 开发计划 — PyQt6 用户界面实现

**周期：** 第 7-9 周（Sprint 7, 8 & 9）  
**前置条件：** Phase 3 全部验收通过，端到端命令行演示脚本可完整运行。  
**目标：** 构建完整双语 UI（学生端英文 + 管理员端中文），集成 Phase 1-3 所有后端模块。  
**完成标准：** 主窗口可通过 `python src/main.py` 打开；学生端可完整完成一次训练；管理员端可查看和添加短语。

---

## 📦 本阶段交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| 练习视图（学生端主界面） | `src/nautical_english/ui/student/practice_view.py` | 录音按钮 + 波形 + 短语展示 |
| 结果视图 | `src/nautical_english/ui/student/result_view.py` | 评分卡片 + HTML 差异着色 |
| 进度视图 | `src/nautical_english/ui/student/progress_view.py` | 折线图/柱状图历史评分 |
| 语料库管理（管理员端） | `src/nautical_english/ui/admin/corpus_manager.py` | CRUD 表格视图 |
| 进度仪表盘（管理员端） | `src/nautical_english/ui/admin/progress_dashboard.py` | 全班统计概览 |
| 主窗口最终版 | `src/nautical_english/ui/main_window.py` | 依赖注入 + QThread 异步 |
| 音频波形组件 | `src/nautical_english/ui/components/waveform_widget.py` | QWidget 自定义绘制 |
| 计分卡组件 | `src/nautical_english/ui/components/score_card.py` | 可复用评分展示控件 |

---

## 🛠️ Task 4.1 — 主窗口框架与主题验证

### Step 1：验证窗口可以打开

```bash
python src/main.py
```

**预期：** 主窗口出现，标题为 "Maritime English Trainer"，Ocean Blue 暗色主题加载正常。

### Step 2：检查 QSS 主题覆盖范围

打开 `src/nautical_english/ui/resources/styles.qss`，确认包含以下关键 ID 样式：

```qss
#recordBtn  { ... }   /* 录音按钮红色圆形 */
#scoreLabel { ... }   /* 大号评分数字 */
#gradeLabel { ... }   /* 等级文字 */
#phraseLabel { ... }  /* 当前短语展示 */
```

若缺失，补充到 `styles.qss` 中：

```qss
#recordBtn {
    background-color: #E74C3C;
    border-radius: 36px;
    min-width: 72px;
    min-height: 72px;
    font-size: 14px;
    color: white;
}
#recordBtn:checked {
    background-color: #C0392B;
}
#scoreLabel {
    font-size: 48px;
    font-weight: bold;
    color: #2ECC71;
}
#gradeLabel {
    font-size: 20px;
    color: #3498DB;
}
#phraseLabel {
    font-size: 22px;
    color: #ECF0F1;
    padding: 12px;
}
```

### Step 3：验证依赖注入模式

确认 `main.py` 按以下顺序初始化并注入依赖：

```python
# src/main.py 参考结构
from nautical_english.training.session import TrainingSession
from nautical_english.ui.main_window import MainWindow

def build_session(cfg):
    # 此处创建所有依赖
    return TrainingSession(...)

app = QApplication(sys.argv)
cfg = AppConfig()
session = build_session(cfg)
window = MainWindow(session=session, repository=repo)
window.show()
app.exec()
```

### Step 4：提交

```bash
git add src/nautical_english/ui/
git commit -m "feat(ui): verify QSS theme and main window launch"
```

---

## 🛠️ Task 4.2 — 音频波形组件

新建 `src/nautical_english/ui/components/waveform_widget.py`：

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
import numpy as np


class WaveformWidget(QWidget):
    """实时音频波形显示组件"""

    HEIGHT = 80
    BAR_WIDTH = 3
    BAR_GAP = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)
        self.setMinimumWidth(200)
        self._samples: list[float] = []

    def update_waveform(self, audio_chunk: np.ndarray) -> None:
        """接收 float32 音频块，更新波形"""
        chunk = audio_chunk.copy()
        n_bars = max(1, self.width() // (self.BAR_WIDTH + self.BAR_GAP))
        # 将 chunk 分成 n_bars 段，取每段 RMS
        segments = np.array_split(chunk, n_bars)
        self._samples = [float(np.sqrt(np.mean(s ** 2))) for s in segments]
        self.update()

    def clear(self) -> None:
        self._samples = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor("#1A2332")
        painter.fillRect(self.rect(), bg_color)

        if not self._samples:
            return

        pen = QPen(QColor("#3498DB"), self.BAR_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        bar_total = self.BAR_WIDTH + self.BAR_GAP
        mid_y = self.height() // 2
        max_h = mid_y - 4

        for i, rms in enumerate(self._samples):
            x = i * bar_total + self.BAR_WIDTH // 2
            h = int(min(rms * 4 * max_h, max_h))
            painter.drawLine(x, mid_y - h, x, mid_y + h)
```

验证：

```python
# 在 Python interactive 中快速验证绘制
import sys
from PyQt6.QtWidgets import QApplication
sys.path.insert(0, "src")
app = QApplication(sys.argv)
from nautical_english.ui.components.waveform_widget import WaveformWidget
import numpy as np
w = WaveformWidget()
w.update_waveform(np.random.randn(4000).astype(np.float32) * 0.1)
w.show()
app.exec()
```

---

## 🛠️ Task 4.3 — 练习视图（学生端核心）

完整实现 `src/nautical_english/ui/student/practice_view.py`：

**布局结构：**
```
┌──────────────────────────────────────────┐
│  Category Selector  [▾ Navigation]        │
├──────────────────────────────────────────┤
│  Current Phrase                           │
│  "Alter course to starboard"             │ ← #phraseLabel
│  参考中文：向右转向                        │
├──────────────────────────────────────────┤
│  [  Waveform Display (WaveformWidget)  ] │
├──────────────────────────────────────────┤
│       [ ● START RECORDING ]              │ ← #recordBtn
│   Status: Ready  / Recording...  / Done  │
├──────────────────────────────────────────┤
│  [  Previous  ]       [  Next  ]         │
└──────────────────────────────────────────┘
```

**关键信号槽设计：**

```python
class PracticeView(QWidget):
    # 发出信号
    recording_completed = pyqtSignal(np.ndarray)  # 录音完成，传递音频数据
    phrase_changed = pyqtSignal(int)               # 短语切换，传递短语 ID

    def __init__(self, phrases: list[Phrase], parent=None):
        super().__init__(parent)
        self._phrases = phrases
        self._current_index = 0
        self._audio_capture = AudioCapture()
        self._recording_thread = None
        self._setup_ui()
        self._connect_signals()

    def _on_record_clicked(self, checked: bool):
        if checked:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        """启动 QThread 进行录音"""
        self._waveform.clear()
        self._status_label.setText("Recording...")
        self._recording_thread = RecordingThread(self._audio_capture)
        self._recording_thread.chunk_ready.connect(self._waveform.update_waveform)
        self._recording_thread.finished_signal.connect(self._on_recording_done)
        self._recording_thread.start()

    def _on_recording_done(self, audio: np.ndarray):
        self._record_btn.setChecked(False)
        self._status_label.setText("Processing...")
        self.recording_completed.emit(audio)
```

### QThread 录音线程

新建 `src/nautical_english/ui/components/recording_thread.py`：

```python
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import sounddevice as sd


class RecordingThread(QThread):
    """非阻塞录音线程，逐块发送波形数据"""

    chunk_ready = pyqtSignal(np.ndarray)     # 每帧音频块
    finished_signal = pyqtSignal(np.ndarray) # 录音完成，完整音频

    SAMPLE_RATE = 16000
    CHUNK_FRAMES = 1600  # 100ms/块

    def __init__(self, duration: float = 5.0, parent=None):
        super().__init__(parent)
        self._duration = duration
        self._running = True

    def run(self):
        frames = []
        total_frames = int(self._duration * self.SAMPLE_RATE)

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=self.CHUNK_FRAMES,
        ) as stream:
            while self._running and sum(len(f) for f in frames) < total_frames:
                chunk, _ = stream.read(self.CHUNK_FRAMES)
                frames.append(chunk[:, 0])
                self.chunk_ready.emit(chunk[:, 0])

        audio = np.concatenate(frames)[:total_frames]
        self.finished_signal.emit(audio)

    def stop(self):
        self._running = False
```

### QThread ASR/TTS 处理线程

新建 `src/nautical_english/ui/components/session_thread.py`：

```python
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
from nautical_english.training.session import TrainingSession, SessionResult


class SessionThread(QThread):
    """后台运行 TrainingSession.run()，避免阻塞 UI"""

    session_done = pyqtSignal(object)   # SessionResult
    session_error = pyqtSignal(str)     # 错误信息

    def __init__(self, session: TrainingSession, audio: np.ndarray,
                 student_id: str, output_dir, parent=None):
        super().__init__(parent)
        self._session = session
        self._audio = audio
        self._student_id = student_id
        self._output_dir = output_dir

    def run(self):
        try:
            result = self._session.run(
                audio=self._audio,
                student_id=self._student_id,
                output_dir=self._output_dir,
            )
            self.session_done.emit(result)
        except Exception as e:  # noqa: BLE001
            self.session_error.emit(str(e))
```

---

## 🛠️ Task 4.4 — 结果视图

完整实现 `src/nautical_english/ui/student/result_view.py`：

**布局结构：**
```
┌──────────────────────────────────────────┐
│             87.0 / 100                   │ ← #scoreLabel
│               Good                       │ ← #gradeLabel
├──────────────────────────────────────────┤
│  You said:    "alter course to port"     │
│  Standard:    "Alter course to starboard"│
│  Diff:  ...to <红 port> (<绿 starboard>) │
│  中文参考：向右转向                        │
├──────────────────────────────────────────┤
│  WER: 0.25     Similarity: 0.95          │
├──────────────────────────────────────────┤
│  [  ▶  Play Standard Pronunciation  ]    │
│  [   Try Again   ]  [    Next →    ]     │
└──────────────────────────────────────────┘
```

**关键实现：**

```python
class ResultView(QWidget):
    retry_clicked = pyqtSignal()
    next_clicked = pyqtSignal()

    def display_result(self, result: SessionResult) -> None:
        self._score_label.setText(f"{result.overall_score:.1f} / 100")
        self._grade_label.setText(result.feedback.grade)
        self._diff_browser.setHtml(
            f"<div style='font-size:14pt;'>{result.feedback.diff_html}</div>"
        )
        self._zh_label.setText(result.feedback.standard_phrase_zh)
        self._wer_label.setText(f"WER: {result.score.wer:.2%}")
        self._sim_label.setText(f"Similarity: {result.score.similarity:.2%}")

    def _play_pronunciation(self):
        """播放 TTS/SMCP 音频"""
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PyQt6.QtCore import QUrl
        if not hasattr(self, "_player"):
            self._player = QMediaPlayer()
            self._audio_out = QAudioOutput()
            self._player.setAudioOutput(self._audio_out)
        self._player.setSource(QUrl.fromLocalFile(str(self._tts_path)))
        self._player.play()
```

---

## 🛠️ Task 4.5 — 进度视图

完整实现 `src/nautical_english/ui/student/progress_view.py`：

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt


class ProgressChart(QWidget):
    """轻量级折线图——历史评分趋势"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._scores: list[float] = []

    def load_scores(self, scores: list[float]) -> None:
        self._scores = scores
        self.update()

    def paintEvent(self, event):
        if not self._scores:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1A2332"))

        w, h = self.width(), self.height()
        margin = 30
        n = len(self._scores)
        if n < 2:
            return

        # 绘制网格线
        painter.setPen(QColor("#2C3E50"))
        for y_val in [0, 25, 50, 75, 100]:
            py = h - margin - int((y_val / 100) * (h - 2 * margin))
            painter.drawLine(margin, py, w - margin, py)

        # 绘制折线
        painter.setPen(QColor("#3498DB"))
        step = (w - 2 * margin) / (n - 1)
        pts = []
        for i, s in enumerate(self._scores):
            px = int(margin + i * step)
            py = h - margin - int((s / 100) * (h - 2 * margin))
            pts.append((px, py))

        for i in range(len(pts) - 1):
            painter.drawLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

        # 数据点
        painter.setBrush(QColor("#2ECC71"))
        painter.setPen(Qt.PenStyle.NoPen)
        for px, py in pts:
            painter.drawEllipse(px - 4, py - 4, 8, 8)
```

---

## 🛠️ Task 4.6 — 管理员端：语料库管理

完整实现 `src/nautical_english/ui/admin/corpus_manager.py`：

**布局结构：**
```
┌─────────────────────────────────────────────────────────────┐
│  搜索: [_______________]  [+ 新增短语]  [✎ 编辑]  [✕ 删除] │
├──────┬──────────────────────┬──────────┬──────────┬──────────┤
│ ID   │ 英文短语              │ 中文翻译  │ 分类     │ 难度    │
├──────┼──────────────────────┼──────────┼──────────┼──────────┤
│ 1    │ Alter course to ...  │ 向右转向  │ 导航     │ ★★☆    │
└──────┴──────────────────────┴──────────┴──────────┴──────────┘
```

**关键实现：**

```python
class CorpusManager(QWidget):
    def __init__(self, repository: CorpusRepository, parent=None):
        super().__init__(parent)
        self._repo = repository
        self._setup_ui()
        self._load_data()

    def _load_data(self):
        phrases = self._repo.get_all_phrases()
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["ID", "English Phrase", "Chinese", "Category", "Difficulty"])
        for p in phrases:
            row = [
                QStandardItem(str(p.id)),
                QStandardItem(p.phrase_en),
                QStandardItem(p.phrase_zh),
                QStandardItem(p.category.name_zh if p.category else ""),
                QStandardItem("★" * p.difficulty + "☆" * (3 - p.difficulty)),
            ]
            self._model.appendRow(row)

    def _add_phrase(self):
        """弹出对话框添加新短语"""
        dialog = PhraseEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._repo.add_phrase(**data)
            self._load_data()
```

---

## 🛠️ Task 4.7 — 主窗口最终集成

更新 `src/nautical_english/ui/main_window.py`，完成完整的依赖注入和信号路由：

```python
class MainWindow(QMainWindow):
    def __init__(self, session: TrainingSession, repository: CorpusRepository,
                 student_id: str = "default_student"):
        super().__init__()
        self._session = session
        self._repo = repository
        self._student_id = student_id

        self._init_views()
        self._connect_signals()
        self._load_stylesheet()
        self.setWindowTitle("Maritime English Trainer v0.1.0")
        self.resize(900, 700)

    def _connect_signals(self):
        """连接学生端信号到处理器"""
        self._practice_view.recording_completed.connect(self._handle_audio)

    def _handle_audio(self, audio: np.ndarray):
        """启动后台 SessionThread 处理"""
        from nautical_english.ui.components.session_thread import SessionThread
        from pathlib import Path
        self._session_thread = SessionThread(
            self._session, audio, self._student_id,
            output_dir=Path("corpus/db/tmp"),
        )
        self._session_thread.session_done.connect(self._on_session_done)
        self._session_thread.session_error.connect(self._on_session_error)
        self._session_thread.start()

    def _on_session_done(self, result):
        self._result_view.display_result(result)
        self._tab_widget.setCurrentIndex(1)  # 切换到结果页
```

---

## ✅ Phase 4 验收标准

- [ ] `python src/main.py` 打开主窗口，无报错
- [ ] 学生可完整走完一次：选短语 → 录音 → 看评分 → 听标准发音
- [ ] 结果 HTML 差异显示正确颜色（错误=红，正确=绿）
- [ ] 进度视图显示历史评分折线图
- [ ] 管理员可新增/删除短语，列表即时更新
- [ ] 录音期间 UI 不卡冻（QThread 生效）
- [ ] `pytest tests/ -v` 全部通过（含 UI 无需实际窗口的测试）

---

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `QMediaPlayer` 无声音 | PyQt6 需要额外的 multimedia 包 | `pip install PyQt6-Qt6 PyQt6-sip` 并确认系统编解码器 |
| 录音线程崩溃 | sounddevice 和 QThread 的信号冲突 | 在 `RecordingThread.run()` 中用 `try/except` 捕获并 emit error 信号 |
| 主窗口 QSS 不生效 | 路径问题 | 用 `Path(__file__).parent / "resources" / "styles.qss"` |
| QTableView 不显示数据 | Model 未设置到 View | 确认 `self._table.setModel(self._model)` 在 `_setup_ui` 中调用 |

---

## 📌 Phase 4 → Phase 5 交接检查

- **完成日期：** ______
- **学生端完整流程测试通过：** ☐ 是 / ☐ 否
- **管理员端 CRUD 测试通过：** ☐ 是 / ☐ 否
- **UI 线程安全（QThread）：** ☐ 已验证 / ☐ 未验证
- **备注：** ______
