"""Windows 安装包构建脚本（PyInstaller）

用法：
    python scripts/build_installer.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SPEC_FILE = ROOT / "nautical_trainer.spec"
ENTRY = ROOT / "src" / "main.py"


SPEC_CONTENT = """\
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'{entry}'],
    pathex=[r'{src}'],
    binaries=[],
    datas=[
        (r'{corpus_db}', 'corpus/db'),
        (r'{assets}', 'assets'),
        (r'{qss}', 'nautical_english/ui/resources'),
    ],
    hiddenimports=[
        'sounddevice',
        'soundfile',
        'sqlalchemy.dialects.sqlite',
    ],
    hookspath=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='maritime_english_trainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=r'{icon}',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='maritime_english_trainer',
)
""".format(
    entry=str(ENTRY),
    src=str(ROOT / "src"),
    corpus_db=str(ROOT / "corpus" / "db"),
    assets=str(ROOT / "assets"),
    qss=str(ROOT / "src" / "nautical_english" / "ui" / "resources"),
    icon=str(ROOT / "assets" / "icons" / "app.ico"),
)


def main() -> None:
    # 写入 spec 文件
    SPEC_FILE.write_text(SPEC_CONTENT, encoding="utf-8")
    print(f"[build] Spec file written: {SPEC_FILE}")

    # 调用 PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(SPEC_FILE)]
    print(f"[build] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        print("✅ Build successful. Output in dist/")
    else:
        print("❌ Build failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
