"""程序入口"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# 将 src 目录加入 sys.path（开发模式运行时）
_SRC = Path(__file__).parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# 离线模式优化：模型已缓存在本地时，在任何 HuggingFace 库 import 前设置离线标志
# 这样 sentence_transformers / transformers 不会发起缓存验证网络请求（节省 ~15s）
# ---------------------------------------------------------------------------
def _set_hf_offline_if_cached(model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
    slug = "models--" + model_name.replace("/", "--")
    # 检查项目内 models/sbert 目录（优先）
    local_sbert = _SRC.parent / "models" / "sbert" / slug / "snapshots"
    # 检查用户 HuggingFace 全局缓存
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / slug / "snapshots"
    cached = (
        (local_sbert.is_dir() and any(local_sbert.iterdir())) or
        (hf_cache.is_dir() and any(hf_cache.iterdir()))
    )
    if cached:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

_set_hf_offline_if_cached()

# 启用详细计时日志（方便诊断卡顿）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

from PyQt6.QtWidgets import QApplication

from nautical_english.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Maritime English Trainer")
    app.setOrganizationName("JMU")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
