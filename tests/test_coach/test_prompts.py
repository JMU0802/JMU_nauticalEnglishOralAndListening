"""Unit tests for coach.prompts module."""

from __future__ import annotations

from nautical_english.coach.prompts import build_system_prompt, parse_llm_output


def test_build_system_prompt_contains_fields():
    prompt = build_system_prompt(
        scenario_name="Pilot Boarding",
        role_description="You are a VTS officer.",
        opening_line="State your vessel name. Over.",
        difficulty=2,
    )
    assert "Pilot Boarding" in prompt
    assert "VTS officer" in prompt
    assert "State your vessel name" in prompt
    assert "2/3" in prompt


def test_parse_llm_output_standard():
    raw = (
        "[REPLY]\nXiamen VTS, roger. Vessel approved. Over.\n"
        "[JUDGE]\n你的回答包含了正确的SMCP词组。"
    )
    result = parse_llm_output(raw)
    assert "roger" in result.reply
    assert "SMCP词组" in result.judge


def test_parse_llm_output_no_judge():
    raw = "[REPLY]\nStandby. Over."
    result = parse_llm_output(raw)
    assert "Standby" in result.reply
    assert result.judge == ""


def test_parse_llm_output_no_markers():
    raw = "Roger. Wilco. Out."
    result = parse_llm_output(raw)
    assert "Roger" in result.reply


def test_parse_llm_output_case_insensitive():
    raw = "[reply]\nHello, over.\n[judge]\n不错的尝试。"
    result = parse_llm_output(raw)
    assert "Hello" in result.reply
    assert "不错" in result.judge
