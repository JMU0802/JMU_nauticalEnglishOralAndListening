"""应用控制器 — 管理 AI 模型生命周期，桥接 UI 与业务逻辑"""

from __future__ import annotations

import random
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from nautical_english.config import AppConfig
from nautical_english.corpus.models import Category, Phrase
from nautical_english.corpus.repository import CorpusRepository
from nautical_english.scenario.repository import ScenarioRepository
from nautical_english.ui.worker import ModelLoader, SessionWorker


class AppController(QObject):
    """协调模型加载、语料数据访问、会话运行的中心控制器。

    信号
    ----
    models_loading(str)   : 模型加载中，携带进度消息
    models_ready()        : 模型加载完成，可以开始练习
    models_error(str)     : 模型加载失败
    session_done(object)  : 会话完成，携带 SessionResult
    session_error(str)    : 会话运行失败
    """

    models_loading  = pyqtSignal(str)
    models_ready    = pyqtSignal()
    models_error    = pyqtSignal(str)
    session_done    = pyqtSignal(object)
    session_error   = pyqtSignal(str)

    def __init__(self, cfg: AppConfig | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cfg = cfg or AppConfig()
        self._repo = CorpusRepository()
        self._scenario_repo = ScenarioRepository()
        self._scenario_repo.seed_if_empty()

        # 加载后填充
        self._recognizer   = None
        self._matcher      = None
        self._scorer       = None
        self._feedback_gen = None
        self._synthesizer  = None
        self._ready        = False

        # 语料缓存
        self._all_phrases: list[Phrase] = []
        self._categories:  list[Category] = []
        self._current_phrase: Phrase | None = None
        self._current_filter_cat_id: int | None = None  # None = 全部

        self._loader: ModelLoader | None = None
        self._worker: SessionWorker | None = None

        # 临时音频输出目录
        self._output_dir = Path(tempfile.gettempdir()) / "naut_eng"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ── 属性 ─────────────────────────────────────────────────────

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def categories(self) -> list[Category]:
        return self._categories

    @property
    def current_phrase(self) -> Phrase | None:
        return self._current_phrase

    @property
    def repo(self) -> CorpusRepository:
        return self._repo

    @property
    def scenario_repo(self) -> ScenarioRepository:
        return self._scenario_repo

    # ── 初始化 ───────────────────────────────────────────────────

    def load_corpus(self) -> None:
        """同步加载语料库数据（轻量，可在主线程运行）。"""
        self._all_phrases = self._repo.get_all_phrases()
        self._categories  = self._repo.get_all_categories()

    def start_loading_models(self) -> None:
        """异步加载 AI 模型（SBERT + Whisper）。"""
        if not self._all_phrases:
            self.load_corpus()
        texts = [p.phrase_en for p in self._all_phrases]
        self._loader = ModelLoader(self._cfg, texts, self)
        self._loader.progress.connect(self.models_loading)
        self._loader.finished.connect(self._on_models_ready)
        self._loader.error.connect(self.models_error)
        self._loader.start()

    def _on_models_ready(self, recognizer, matcher, scorer, feedback_gen, synthesizer) -> None:
        self._recognizer   = recognizer
        self._matcher      = matcher
        self._scorer       = scorer
        self._feedback_gen = feedback_gen
        self._synthesizer  = synthesizer
        self._ready        = True
        self.models_ready.emit()

    # ── 短语选择 ─────────────────────────────────────────────────

    def set_category_filter(self, category_id: int | None) -> None:
        """设置类别筛选，None 表示全部。"""
        self._current_filter_cat_id = category_id

    def next_phrase(self) -> Phrase | None:
        """随机抽取下一个短语（根据当前筛选）。"""
        pool = self._filtered_pool()
        if not pool:
            return None
        # 避免连续出现同一道题
        if len(pool) > 1 and self._current_phrase:
            pool = [p for p in pool if p.id != self._current_phrase.id]
        self._current_phrase = random.choice(pool)
        return self._current_phrase

    def _filtered_pool(self) -> list[Phrase]:
        if self._current_filter_cat_id is None:
            return self._all_phrases
        return [p for p in self._all_phrases
                if p.category_id == self._current_filter_cat_id]

    def phrase_count(self, category_id: int | None = None) -> int:
        if category_id is None:
            return len(self._all_phrases)
        return sum(1 for p in self._all_phrases if p.category_id == category_id)

    # ── 会话运行 ─────────────────────────────────────────────────

    def run_session(self, audio, student_id: str) -> None:
        """在后台线程中运行完整评估 pipeline。"""
        if not self._ready:
            self.session_error.emit("Models not loaded yet.")
            return
        if self._current_phrase is None:
            self.session_error.emit("No phrase selected.")
            return

        self._worker = SessionWorker(
            audio=audio,
            phrase_id=self._current_phrase.id,
            recognizer=self._recognizer,
            matcher=self._matcher,
            scorer=self._scorer,
            feedback_gen=self._feedback_gen,
            synthesizer=self._synthesizer,
            repo=self._repo,
            student_id=student_id,
            output_dir=self._output_dir,
            parent=self,
        )
        self._worker.finished.connect(self.session_done)
        self._worker.error.connect(self.session_error)
        self._worker.start()

    # ── 进度查询 ─────────────────────────────────────────────────

    def get_recent_records(self, student_id: str, limit: int = 20) -> list:
        try:
            recs = self._repo.get_student_records(student_id)
            return recs[-limit:]
        except Exception:  # noqa: BLE001
            return []
