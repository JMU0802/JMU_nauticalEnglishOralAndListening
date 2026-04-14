"""导入完整 SMCP 语料库（带音频路径）到 corpus.db

数据来源：SMCP_DATA/audioFile/cmcp_spider_db.sql
音频目录：SMCP_DATA/audioFile/downloads/<uuid>.mp3（共 5133 条）

功能：
  1. 解析 SQL dump，提取 t_item / t_detail / t_example 三张表
  2. 以 SMCP A1/A2/B1/B2/B3/B4 六个顶级类别重建 categories 表
  3. 导入 5133 条 t_example 记录（仅含本地 MP3 的条目）
  4. phrase_en = example.context, audio_path = 相对路径

用法：
    python scripts/import_smcp_audio.py [--db path] [--sql path] [--audio-dir path]
    python scripts/import_smcp_audio.py --dry-run   # 只解析，不写库
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from nautical_english.corpus.models import Base, Category, Phrase, TrainingRecord
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ── 顶级类别映射（level=1）──────────────────────────────────────────────────
TOP_LEVEL_NAMES: dict[str, str] = {
    "A1 - External communication phrases": "A1 - 对外通信",
    "A2 - On-board communication phrases": "A2 - 船内通信",
    "B1 - Operative ship handling": "B1 - 船舶驾驶操作",
    "B2 - Safety on board": "B2 - 船上安全",
    "B3 - Cargo and cargo handling": "B3 - 货物与装卸",
    "B4 - Passenger care": "B4 - 旅客照料",
}

# 将 B1 改名让 key 匹配 SQL 中实际标题（SQL 里用的是含连字符格式）
# 实际上从上面的输出看到是: "B1 - Operative ship handling" ← 加这个以防无匹配
_TOP_FALLBACK: dict[str, str] = {v.split("-")[0].strip(): v
                                  for v in TOP_LEVEL_NAMES}


# ── SQL 解析工具 ─────────────────────────────────────────────────────────────

def _parse_values(line: str) -> list[str | None]:
    """从 INSERT INTO ... VALUES (...) 中提取字段列表。

    支持：带引号字符串 'xxx'、NULL、整数/浮点数。
    """
    m = re.search(r"VALUES\s*\((.+)\);$", line.rstrip())
    if not m:
        return []
    raw = m.group(1)
    fields: list[str | None] = []
    in_str = False
    buf: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if in_str:
            if ch == "\\" and i + 1 < len(raw):
                nc = raw[i + 1]
                escape_map = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "'": "'"}
                buf.append(escape_map.get(nc, nc))
                i += 2
                continue
            if ch == "'":
                # 处理 SQL 转义的单引号 ''
                if i + 1 < len(raw) and raw[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_str = False
                fields.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        else:
            if ch == "'":
                buf = []   # 丢弃任何前导空格/逗号残留
                in_str = True
            elif ch == "," :
                # 如果 buf 有未加引号内容（数字等），存入
                token = "".join(buf).strip()
                if token:
                    fields.append(token)
                    buf = []
            elif raw[i: i + 4] == "NULL":
                fields.append(None)
                i += 4
                continue
            else:
                buf.append(ch)
        i += 1
    # 最后剩余的非字符串 token
    token = "".join(buf).strip()
    if token:
        fields.append(token)
    return fields


def parse_sql(sql_path: Path) -> tuple[dict, dict, dict]:
    """解析 SQL 文件，返回 (items, details, examples) 三个字典。

    items  : {id: {title, level, level_path, parent_id}}
    details: {id: {item_id, title, cmcp, syntax}}
    examples: {id: {detail_id, context, file_path}}
    """
    items: dict[str, dict] = {}
    details: dict[str, dict] = {}
    examples: dict[str, dict] = {}

    with sql_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if "INTO `t_item`" in line:
                f = _parse_values(line)
                if len(f) >= 4:
                    items[f[0]] = {
                        "title": f[1] or "",
                        "level": int(f[2]) if f[2] is not None else 0,
                        "level_path": f[3] or "",
                        "parent_id": f[4] if len(f) > 4 else None,
                    }
            elif "INTO `t_detail`" in line:
                f = _parse_values(line)
                if len(f) >= 4:
                    details[f[0]] = {
                        "item_id": f[1],
                        "title": f[2] or "",
                        "cmcp": f[3] or "",
                        "syntax": f[4] if len(f) > 4 else None,
                    }
            elif "INTO `t_example`" in line:
                f = _parse_values(line)
                if len(f) >= 3:
                    examples[f[0]] = {
                        "detail_id": f[1],
                        "context": (f[2] or "").strip(),
                        "file_path": f[3] if len(f) > 3 else None,
                    }
    return items, details, examples


def build_item_tree(items: dict) -> dict[str, str | None]:
    """构建 item_id → top_level_title 的映射。

    策略：在 level_path 字段（分号分隔的祖先 ID 链）中查找 level=1 的节点。
    """
    # level=1 的顶级节点 id → title
    top_ids: dict[str, str] = {
        iid: info["title"] for iid, info in items.items() if info["level"] == 1
    }

    def find_top(item_id: str) -> str | None:
        info = items.get(item_id)
        if not info:
            return None
        if info["level"] == 1:
            return info["title"]
        path = info.get("level_path", "")
        ancestors = [p.strip() for p in path.split(";") if p.strip()]
        for anc_id in ancestors:
            if anc_id in top_ids:
                return top_ids[anc_id]
        return None

    item_to_top: dict[str, str | None] = {
        iid: find_top(iid) for iid in items
    }
    return item_to_top


# ── 数据库操作 ────────────────────────────────────────────────────────────────

def import_data(
    db_path: Path,
    sql_path: Path,
    audio_dir: Path,
    dry_run: bool = False,
) -> None:
    print(f"[import] 解析 SQL: {sql_path} ...")
    items, details, examples = parse_sql(sql_path)
    print(f"[import] t_item={len(items)}, t_detail={len(details)}, t_example={len(examples)}")

    item_to_top = build_item_tree(items)

    # 仅保留有 MP3 文件的 examples
    available: list[dict] = []
    missing_audio = 0
    for ex_id, ex in examples.items():
        mp3 = audio_dir / f"{ex_id}.mp3"
        if mp3.exists():
            det = details.get(ex["detail_id"], {})
            item_id = det.get("item_id", "")
            top_title = item_to_top.get(item_id)
            available.append({
                "uuid": ex_id,
                "context": ex["context"],
                "cmcp": det.get("cmcp", ""),
                "top_category": top_title or "Unknown",
                "audio_path": str(mp3.relative_to(ROOT)).replace("\\", "/"),
            })
        else:
            missing_audio += 1

    print(f"[import] 有 MP3: {len(available)}, 缺失 MP3: {missing_audio}")

    # 统计各顶级类别
    from collections import Counter
    cat_counts = Counter(r["top_category"] for r in available)
    for cat, cnt in sorted(cat_counts.items()):
        zh = TOP_LEVEL_NAMES.get(cat, "—")
        print(f"  {cat!r} ({zh}): {cnt}")

    if dry_run:
        print("[dry-run] 仅解析，不写入数据库。")
        return

    # 构建 DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # 删除已有 training_records、phrases、categories
        session.execute(text("DELETE FROM training_records"))
        session.execute(text("DELETE FROM phrases"))
        session.execute(text("DELETE FROM categories"))
        session.commit()
        print("[import] 已清空旧数据。")

        # 插入 6 个顶级类别
        cat_name_to_obj: dict[str, Category] = {}
        for en_title, zh_title in TOP_LEVEL_NAMES.items():
            cat = Category(name_en=en_title, name_zh=zh_title)
            session.add(cat)
            session.flush()
            cat_name_to_obj[en_title] = cat

        # 增加一个 Unknown fallback
        fallback_cat = Category(name_en="Unknown", name_zh="其他")
        session.add(fallback_cat)
        session.flush()
        cat_name_to_obj["Unknown"] = fallback_cat

        # 批量插入 phrases
        phrase_objs: list[Phrase] = []
        for r in available:
            cat_obj = cat_name_to_obj.get(r["top_category"], fallback_cat)
            phrase_objs.append(
                Phrase(
                    category_id=cat_obj.id,
                    phrase_en=r["context"],
                    phrase_zh="",          # 无中文翻译，留空
                    difficulty=1,
                    audio_path=r["audio_path"],
                )
            )
        session.bulk_save_objects(phrase_objs)
        session.commit()
        print(f"[import] 已导入 {len(phrase_objs)} 条短语（带音频）。✅")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="导入 SMCP 音频语料库")
    parser.add_argument("--db", default=str(ROOT / "corpus" / "db" / "corpus.db"))
    parser.add_argument(
        "--sql",
        default=str(ROOT / "SMCP_DATA" / "audioFile" / "cmcp_spider_db.sql"),
    )
    parser.add_argument(
        "--audio-dir",
        default=str(ROOT / "SMCP_DATA" / "audioFile" / "downloads"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    import_data(
        db_path=Path(args.db),
        sql_path=Path(args.sql),
        audio_dir=Path(args.audio_dir),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
