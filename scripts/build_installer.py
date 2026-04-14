"""Windows 安装包构建脚本（PyInstaller）。

用法：
    python scripts/build_installer.py
    python scripts/build_installer.py --spec-only
"""

from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).parent.parent
SPEC_FILE = ROOT / "scripts" / "nautical_trainer.spec"
ENTRY = ROOT / "src" / "main.py"


SPEC_CONTENT = """\
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'{entry}'],
    pathex=[r'{src}'],
    binaries=[],
    datas={datas},
    hiddenimports=[
        'nautical_english',
        'nautical_english.asr',
        'nautical_english.tts',
        'nautical_english.nlp',
        'nautical_english.corpus',
        'nautical_english.feedback',
        'nautical_english.training',
        'nautical_english.ui',
        'sounddevice',
        'soundfile',
        'faster_whisper',
        'sentence_transformers',
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
"""


def _build_datas() -> str:
    pairs: list[tuple[str, str]] = []
    candidates = [
        (ROOT / "src" / "nautical_english" / "ui" / "resources", "nautical_english/ui/resources"),
        (ROOT / "corpus" / "db", "corpus/db"),
        (ROOT / "SMCP_DATA" / "audioFile", "SMCP_DATA/audioFile"),
        (ROOT / "assets", "assets"),
    ]
    for src, dst in candidates:
        if src.exists():
            pairs.append((str(src), dst))
    return repr(pairs)


def _render_spec() -> str:
    return SPEC_CONTENT.format(
        entry=str(ENTRY),
        src=str(ROOT / "src"),
        datas=_build_datas(),
        icon=str(ROOT / "assets" / "icons" / "app.ico"),
    )


def main() -> None:
    parser = ArgumentParser(description="Build PyInstaller package for Nautical Trainer")
    parser.add_argument("--spec-only", action="store_true", help="Only generate spec file")
    args = parser.parse_args()

    # 写入 spec 文件
    SPEC_FILE.write_text(_render_spec(), encoding="utf-8")
    print(f"[build] Spec file written: {SPEC_FILE}")

    if args.spec_only:
        print("[build] Spec-only mode, skip PyInstaller build.")
        return

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
