"""句子语义匹配模块 — 基于 Sentence-BERT 的余弦相似度匹配"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MatchResult:
    """匹配结果。"""

    phrase: str           # 最佳匹配短语
    score: float          # 余弦相似度 ∈ [0, 1]
    index: int            # 在候选列表中的下标


_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SentenceMatcher:
    """将学员语音文本与 SMCP 标准短语库进行语义相似度匹配。

    Parameters
    ----------
    phrases:
        标准短语列表（来自数据库）。
    model_name:
        sentence-transformers 模型名称。
    """

    def __init__(
        self,
        phrases: list[str],
        model_name: str = _DEFAULT_MODEL,
        cache_folder: str | None = None,
        device: str = "auto",
    ) -> None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        import torch  # noqa: PLC0415

        if device == "auto":
            resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            resolved_device = device

        # 优先使用项目内本地模型，完全跳过 HuggingFace 网络请求（加快启动 15-20 秒）
        # 路径: models/sbert/<hub_slug>/snapshots/<commit>/
        resolved_model: str = model_name
        _local_hub = Path(__file__).resolve().parents[3] / "models" / "sbert"
        _slug = "models--" + model_name.replace("/", "--")
        _snap_dir = _local_hub / _slug / "snapshots"
        if _snap_dir.is_dir():
            _snaps = sorted(_snap_dir.iterdir())
            if _snaps and (_snaps[-1] / "config.json").exists():
                resolved_model = str(_snaps[-1])
        
        self._model = SentenceTransformer(
            resolved_model,
            cache_folder=cache_folder,
            device=resolved_device,
        )
        self._phrases = phrases
        # 预计算语料库向量（normalize 后可直接用点积代替余弦）
        self._embeddings: np.ndarray = self._model.encode(
            phrases, normalize_embeddings=True, show_progress_bar=False
        )
        self._cache: dict[str, MatchResult] = {}

    def find_best_match(self, query: str) -> MatchResult:
        """在候选短语中找到与 ``query`` 最接近的标准句。"""
        normalized = query.strip().lower()
        cached = self._cache.get(normalized)
        if cached is not None:
            return cached

        q_emb = self._model.encode([normalized], normalize_embeddings=True, show_progress_bar=False)
        scores = (self._embeddings @ q_emb.T).flatten()
        idx = int(np.argmax(scores))
        result = MatchResult(
            phrase=self._phrases[idx],
            score=float(scores[idx]),
            index=idx,
        )
        self._cache[normalized] = result
        return result

    def update_phrases(self, phrases: list[str]) -> None:
        """更新候选短语库并重新编码（语料变更时调用）。"""
        self._phrases = phrases
        self._embeddings = self._model.encode(
            phrases, normalize_embeddings=True, show_progress_bar=False
        )
        self._cache.clear()
