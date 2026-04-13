"""SMCP 标准海事通信英语种子数据

来源：IMO Standard Marine Communication Phrases (SMCP) 2002 版
覆盖 5 大场景类别，共 60+ 标准短语
"""

from __future__ import annotations

# 结构：(category_en, category_zh, [(phrase_en, phrase_zh, difficulty), ...])
SEED_DATA: list[tuple[str, str, list[tuple[str, str, int]]]] = [
    # ──────────────────────────────────────────────────────────────
    # 1. 航行与机动 Navigation & Maneuvering
    # ──────────────────────────────────────────────────────────────
    (
        "Navigation & Maneuvering",
        "航行与机动",
        [
            ("Alter course to starboard.", "向右转向。", 1),
            ("Alter course to port.", "向左转向。", 1),
            ("Maintain your course and speed.", "保持你的航向和航速。", 1),
            ("Stop your vessel immediately.", "立即停船。", 1),
            ("Reduce speed.", "减速。", 1),
            ("Increase speed.", "增速。", 1),
            ("Come to anchor.", "抛锚。", 2),
            ("You are standing into danger.", "你正驶入危险区域。", 2),
            ("You are in a dangerous position.", "你处于危险位置。", 2),
            ("Proceed with caution.", "谨慎驶进。", 2),
            ("I am altering my course to starboard.", "我正在向右转向。", 1),
            ("I am altering my course to port.", "我正在向左转向。", 1),
            ("I am operating astern propulsion.", "我在用倒车推进。", 3),
            ("Keep well clear of me.", "请远离我船。", 1),
            ("I require a pilot.", "我需要引航员。", 2),
        ],
    ),
    # ──────────────────────────────────────────────────────────────
    # 2. 遇险与紧急 Distress & Urgency
    # ──────────────────────────────────────────────────────────────
    (
        "Distress & Urgency",
        "遇险与紧急",
        [
            ("Mayday. Mayday. Mayday.", "求救。求救。求救。", 1),
            ("I am in distress and require immediate assistance.", "我遇险，需要立即援助。", 1),
            ("I require immediate assistance.", "我需要立即援助。", 1),
            ("I am on fire.", "我船着火。", 1),
            ("I am sinking.", "我船正在下沉。", 1),
            ("I have a man overboard.", "有人落水。", 1),
            ("I require medical assistance.", "我需要医疗援助。", 2),
            ("I am abandoning my vessel.", "我正在弃船。", 2),
            ("I require a tug.", "我需要拖船。", 2),
            ("Abandon ship!", "弃船！", 1),
            ("Stand by to render assistance.", "准备提供援助。", 2),
            ("I will stand by to render assistance.", "我将待命提供援助。", 2),
        ],
    ),
    # ──────────────────────────────────────────────────────────────
    # 3. 避碰 Collision Avoidance (COLREGS)
    # ──────────────────────────────────────────────────────────────
    (
        "Collision Avoidance",
        "避碰",
        [
            ("Keep clear of me.", "请避让我船。", 1),
            ("What are your intentions?", "你的意图是什么？", 1),
            ("I am the stand-on vessel.", "我是直航船。", 2),
            ("I am the give-way vessel.", "我是让路船。", 2),
            ("You are the stand-on vessel.", "你是直航船。", 2),
            ("You are the give-way vessel.", "你是让路船。", 2),
            ("Risk of collision exists.", "存在碰撞风险。", 2),
            ("Collision is imminent.", "碰撞迫在眉睫。", 2),
            ("I am altering course to avoid collision.", "我正转向以避免碰撞。", 3),
            ("I am reducing speed to avoid collision.", "我正减速以避免碰撞。", 3),
            ("Take avoiding action.", "采取避让行动。", 1),
            ("My engines are full astern.", "我的主机已全速倒车。", 3),
        ],
    ),
    # ──────────────────────────────────────────────────────────────
    # 4. 锚泊与系泊 Anchoring & Mooring
    # ──────────────────────────────────────────────────────────────
    (
        "Anchoring & Mooring",
        "锚泊与系泊",
        [
            ("I am at anchor.", "我正在锚泊。", 1),
            ("I am weighing anchor.", "我正在起锚。", 1),
            ("I have dragged my anchor.", "我的锚走锚了。", 2),
            ("The anchorage is clear.", "锚地畅通。", 2),
            ("I require a mooring.", "我需要一个系泊点。", 2),
            ("Make fast the forward line.", "系紧首缆。", 3),
            ("Make fast the stern line.", "系紧尾缆。", 3),
            ("Let go all lines.", "松开所有缆绳。", 2),
        ],
    ),
    # ──────────────────────────────────────────────────────────────
    # 5. 甚高频无线电通信 VHF Communication
    # ──────────────────────────────────────────────────────────────
    (
        "VHF Communication",
        "甚高频通信",
        [
            ("This is vessel [name] on channel sixteen.", "这是[船名]，使用第16频道。", 1),
            ("Over.", "完毕，请回答。", 1),
            ("Out.", "通话结束。", 1),
            ("Roger.", "收到。", 1),
            ("Say again.", "请重复。", 1),
            ("Understood.", "明白。", 1),
            ("Stand by.", "请稍候。", 1),
            ("I read you loud and clear.", "我收听清晰。", 2),
            ("I cannot read you. Please repeat.", "我听不清，请重复。", 2),
            ("Switch to channel [number].", "改用[频道号]频道。", 2),
            ("What is your position?", "你的位置在哪里？", 1),
            ("My position is [latitude] [longitude].", "我的位置是[纬度][经度]。", 2),
        ],
    ),
]
