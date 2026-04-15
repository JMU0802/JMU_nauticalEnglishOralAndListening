"""LightRAG HTTP 客户端 — 为 CoachService 提供 SMCP 知识检索"""
from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request
import json
from typing import Optional

from nautical_english.rag.config import RAGConfig

log = logging.getLogger("nautical_english.rag")


class RAGClient:
    """轻量级同步 HTTP 客户端，调用 LightRAG Server REST API。

    设计原则（降级安全）：
    - LightRAG Server 离线 → ``query`` 返回空字符串，不抛异常
    - ``is_healthy`` 失败 → 返回 False，CoachService 跳过 RAG 增强
    - 所有异常在内部捕获并记录，从不向上传播
    """

    def __init__(self, config: Optional[RAGConfig] = None) -> None:
        self._cfg = config or RAGConfig()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """检查 LightRAG Server 是否在线并返回 200。"""
        if not self._cfg.enabled:
            return False
        try:
            url = f"{self._cfg.host.rstrip('/')}/health"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as exc:
            log.debug("LightRAG health check failed: %s", exc)
            return False

    def query(
        self,
        question: str,
        mode: Optional[str] = None,
    ) -> str:
        """查询知识库，返回相关 SMCP 标准知识文本。

        Parameters
        ----------
        question:
            自然语言查询，通常是学员发言的上下文描述。
        mode:
            检索模式：naive | local | global | mix | hybrid。
            默认使用 ``RAGConfig.query_mode``（mix）。

        Returns
        -------
        str
            相关知识文本。LightRAG 不可用时返回空字符串。
        """
        if not self._cfg.enabled:
            return ""
        try:
            url = f"{self._cfg.host.rstrip('/')}/query"
            payload = json.dumps({
                "query": question,
                "mode": mode or self._cfg.query_mode,
                "top_k": self._cfg.top_k,
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._cfg.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # LightRAG API 返回格式：{"response": "..."}
                return str(data.get("response", "")).strip()
        except urllib.error.HTTPError as exc:
            log.warning("LightRAG query HTTP %s: %s", exc.code, exc.reason)
            return ""
        except Exception as exc:
            log.debug("LightRAG query failed (will use no-RAG mode): %s", exc)
            return ""

    def upload_text(self, content: str, description: str = "") -> bool:
        """通过 API 上传文本内容到知识库（管理用途）。

        Returns True if accepted, False otherwise.
        """
        if not self._cfg.enabled:
            return False
        try:
            url = f"{self._cfg.host.rstrip('/')}/documents/text"
            payload = json.dumps({
                "text": content,
                "description": description,
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status in (200, 201, 202)
        except Exception as exc:
            log.error("LightRAG upload failed: %s", exc)
            return False
