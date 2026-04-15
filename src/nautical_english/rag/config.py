"""LightRAG 连接配置"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class RAGConfig:
    """LightRAG Server 连接参数。

    从环境变量（带 LIGHTRAG_ 前缀）读取，支持 .env 文件。
    所有参数均有合理默认值，LightRAG 未启动时自动降级。
    """

    host: str = field(
        default_factory=lambda: os.environ.get("LIGHTRAG_HOST", "http://localhost:9621")
    )
    timeout: int = field(
        default_factory=lambda: int(os.environ.get("LIGHTRAG_TIMEOUT", "15"))
    )
    enabled: bool = field(
        default_factory=lambda: os.environ.get("LIGHTRAG_ENABLED", "true").lower() == "true"
    )
    query_mode: str = field(
        default_factory=lambda: os.environ.get("LIGHTRAG_QUERY_MODE", "mix")
    )
    top_k: int = field(
        default_factory=lambda: int(os.environ.get("LIGHTRAG_TOP_K", "5"))
    )
