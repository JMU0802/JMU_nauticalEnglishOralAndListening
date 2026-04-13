"""程序入口"""

from __future__ import annotations

import sys
from pathlib import Path

# 将 src 目录加入 sys.path（开发模式运行时）
_SRC = Path(__file__).parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

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
