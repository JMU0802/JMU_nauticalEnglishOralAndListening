"""10 条初始 SMCP 场景种子数据"""

from __future__ import annotations

SEED_SCENARIOS: list[dict] = [
    {
        "name_en": "Pilot Boarding Request",
        "name_zh": "引航员登轮申请",
        "category": "Navigation",
        "difficulty": 1,
        "description_en": (
            "You are the OOW (Officer on Watch) approaching the port. "
            "You need to request a pilot and provide vessel information."
        ),
        "description_zh": "你是当班驾驶员，船舶正在进港。你需要申请引航员并提供船舶信息。",
        "system_role_en": (
            "You are a VTS (Vessel Traffic Service) officer at Xiamen Port. "
            "You receive pilot boarding requests and coordinate arrivals. "
            "Follow SMCP strictly. Be professional and concise."
        ),
        "opening_line_en": (
            "Vessel calling Xiamen VTS, this is Xiamen VTS. "
            "Please state your vessel name, position, and request. Over."
        ),
        "max_turns": 8,
    },
    {
        "name_en": "VTS Position Report",
        "name_zh": "VTS 位置报告",
        "category": "Navigation",
        "difficulty": 1,
        "description_en": (
            "You are approaching a traffic separation scheme. "
            "Report your position, course, and speed to VTS."
        ),
        "description_zh": "你正进入交通分隔区，需向 VTS 报告船位、航向和航速。",
        "system_role_en": (
            "You are a VTS controller managing vessel traffic. "
            "You require regular position reports from vessels in your sector. "
            "Use SMCP standard phrases only."
        ),
        "opening_line_en": (
            "All vessels in sector Alpha, this is Xiamen VTS. "
            "Commence position reports. Over."
        ),
        "max_turns": 6,
    },
    {
        "name_en": "Distress Call — Mayday",
        "name_zh": "遇险呼叫 — Mayday",
        "category": "Distress",
        "difficulty": 3,
        "description_en": (
            "Your vessel is in distress. Transmit a Mayday call including "
            "vessel name, position, nature of distress, number of persons, and any assistance required."
        ),
        "description_zh": "你的船舶遇险，需按 SMCP 规范发出 Mayday 呼叫，包含船名、位置、遇险性质和所需援助。",
        "system_role_en": (
            "You are the Maritime Rescue Coordination Center (MRCC) operator. "
            "You respond to distress calls and coordinate rescue. "
            "Acknowledge the Mayday, confirm details, and dispatch assistance."
        ),
        "opening_line_en": (
            "This is MRCC Xiamen. All stations, all stations, all stations. "
            "I am standing by on Channel 16. Over."
        ),
        "max_turns": 10,
    },
    {
        "name_en": "Man Overboard",
        "name_zh": "有人落水",
        "category": "Distress",
        "difficulty": 2,
        "description_en": (
            "A crew member has fallen overboard. "
            "Report the incident to the MRCC and coordinate rescue operations."
        ),
        "description_zh": "一名船员落水，需向 MRCC 报告并协调救援行动。",
        "system_role_en": (
            "You are an MRCC operator. "
            "You respond to man overboard incidents and coordinate search and rescue. "
            "Follow SMCP urgency communication procedures."
        ),
        "opening_line_en": (
            "This is MRCC Xiamen on Channel 16. "
            "Do you have an urgency message? Over."
        ),
        "max_turns": 8,
    },
    {
        "name_en": "Anchoring Permission Request",
        "name_zh": "锚泊申请",
        "category": "Port Operations",
        "difficulty": 1,
        "description_en": (
            "You need to anchor your vessel in the designated anchorage area. "
            "Request permission from port authority and confirm details."
        ),
        "description_zh": "你需要在指定锚地抛锚，需向港口当局申请许可并确认细节。",
        "system_role_en": (
            "You are a port authority officer managing anchorage areas. "
            "You grant or deny anchoring permissions based on availability. "
            "Use standard SMCP port operations phrases."
        ),
        "opening_line_en": (
            "This is Xiamen Port Authority. "
            "Vessel requesting anchorage, state your vessel name and intended anchorage. Over."
        ),
        "max_turns": 6,
    },
    {
        "name_en": "Cargo Damage Report",
        "name_zh": "货物损坏报告",
        "category": "Cargo",
        "difficulty": 2,
        "description_en": (
            "Cargo damage has been discovered during loading. "
            "Report the damage to the port superintendent and document the incident."
        ),
        "description_zh": "装货时发现货物损坏，需向港口督察员报告并记录事故。",
        "system_role_en": (
            "You are a port superintendent responsible for cargo operations. "
            "You receive damage reports and coordinate documentation. "
            "Use formal maritime English and SMCP procedures."
        ),
        "opening_line_en": (
            "This is Port Superintendent. "
            "I understand you have a cargo incident to report. Please proceed. Over."
        ),
        "max_turns": 8,
    },
    {
        "name_en": "Fire on Board",
        "name_zh": "船上火灾",
        "category": "Emergency",
        "difficulty": 3,
        "description_en": (
            "A fire has broken out in the engine room. "
            "Alert the crew, report to the nearest coast station, and coordinate firefighting."
        ),
        "description_zh": "机舱发生火灾，需向全体船员报警、向最近岸站报告并协调灭火行动。",
        "system_role_en": (
            "You are a coast radio station operator receiving emergency reports. "
            "Respond to the fire emergency with urgency, gather vessel details, "
            "and coordinate with fire services following SMCP emergency procedures."
        ),
        "opening_line_en": (
            "This is Xiamen Radio on Channel 16. "
            "I have received your emergency signal. Please report nature of emergency. Over."
        ),
        "max_turns": 10,
    },
    {
        "name_en": "Weather Report Request",
        "name_zh": "气象报告申请",
        "category": "Navigation",
        "difficulty": 1,
        "description_en": (
            "You need to obtain the latest weather forecast for your passage. "
            "Request a weather report from the coast radio station."
        ),
        "description_zh": "你需要获取最新气象预报以规划航线，向海岸电台申请气象报告。",
        "system_role_en": (
            "You are a coast radio station operator providing weather information. "
            "Respond with wind direction, speed, visibility, and sea state "
            "in standard SMCP weather reporting format."
        ),
        "opening_line_en": (
            "This is Xiamen Radio. "
            "Vessel requesting weather information, state your vessel name and area of concern. Over."
        ),
        "max_turns": 6,
    },
    {
        "name_en": "Tug Assistance Request",
        "name_zh": "请求拖轮协助",
        "category": "Port Operations",
        "difficulty": 2,
        "description_en": (
            "Your vessel requires tug assistance for berthing. "
            "Coordinate with the tug master on approach speed, lines, and berthing plan."
        ),
        "description_zh": "你的船舶靠泊需要拖轮协助，需与拖轮船长协调进港速度、缆绳和靠泊计划。",
        "system_role_en": (
            "You are the tug master coordinating assistance for a berthing vessel. "
            "Confirm tug positioning, approach speed, and line handling using SMCP."
        ),
        "opening_line_en": (
            "This is Tug Xiamen 1 to Master. "
            "Ready to assist. Please state your approach speed and intended berth. Over."
        ),
        "max_turns": 8,
    },
    {
        "name_en": "Medical Assistance — PAN PAN",
        "name_zh": "医疗紧急求助 — PAN PAN",
        "category": "Emergency",
        "difficulty": 2,
        "description_en": (
            "A crew member has a medical emergency. "
            "Transmit a PAN PAN urgency call and request medical advice."
        ),
        "description_zh": "一名船员出现医疗紧急情况，需发出 PAN PAN 紧急呼叫并请求医疗建议。",
        "system_role_en": (
            "You are a MRCC medical officer responding to PAN PAN medical calls. "
            "Ask for patient details, symptoms, and vital signs. "
            "Provide guidance following SMCP urgency communication procedures."
        ),
        "opening_line_en": (
            "This is MRCC Xiamen Medical. "
            "I acknowledge your PAN PAN call. Please state patient's condition. Over."
        ),
        "max_turns": 8,
    },
]
