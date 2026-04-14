"""临时脚本：分析 SQL dump 结构，提取 t_example / t_detail / t_item 样本"""
from __future__ import annotations
import re
from pathlib import Path

SQL_FILE = Path("SMCP_DATA/audioFile/cmcp_spider_db.sql")
sql = SQL_FILE.read_text(encoding="utf-8")

lines = sql.splitlines()

# 提取前 5 行 t_example INSERT
example_lines = [l for l in lines if "INTO `t_example`" in l]
print(f"t_example lines found: {len(example_lines)}")
for l in example_lines[:3]:
    print(" ", l[:250])

# 提取前 3 行 t_item INSERT
item_lines = [l for l in lines if "INTO `t_item`" in l]
print(f"\nt_item lines found: {len(item_lines)}")
# 找出 level=1 的顶级类别
for l in item_lines:
    # 格式: ('uuid', 'title', level, 'level_path', ...)
    m = re.match(r"INSERT INTO `t_item` VALUES \('([^']+)', '([^']+)', (\d+),", l)
    if m and int(m.group(3)) == 1:
        print(f"  [L1] {m.group(1)} | {m.group(2)}")
