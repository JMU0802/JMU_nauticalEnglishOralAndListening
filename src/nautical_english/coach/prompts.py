"""SMCP coaching prompt templates.

The LLM is instructed to respond with two clearly-delimited sections:

    [REPLY]
    <natural next dialogue turn as the radio counterpart>

    [JUDGE]
    <brief SMCP correctness assessment of the student's last utterance>

Call :func:`build_system_prompt` once at session start and pass the result
as the ``"system"`` message.  Call :func:`parse_llm_output` to split the
LLM's raw reply into its two parts.
"""

from __future__ import annotations

import re
from typing import NamedTuple


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
You are an AI SMCP (Standard Marine Communication Phrases) language coach.
Your role in this conversation: {role_description}

SCENARIO: {scenario_name}
DIFFICULTY: {difficulty}/3

=== YOUR TASK ===
1. Stay fully in character as the radio counterpart described above.
2. After EVERY student message, reply with EXACTLY this structure:

[REPLY]
<your in-character radio response in nautical English>

[JUDGE]
<1-3 sentence SMCP assessment of the student's previous utterance.
 Note: correct phrases used, errors, missing SMCP elements, suggested correction.
 If the student's message was perfect, say "Excellent SMCP usage.">

=== GUIDELINES ===
- Use authentic SMCP phrases (e.g. "I say again", "Roger", "Wilco", "Over", "Out").
- Keep [REPLY] concise (≤ 60 words) and realistic for radio communication.
- [JUDGE] must always be in Chinese so the student can understand clearly.
- Be encouraging but accurate. Point out every SMCP deviation.
- If the student goes off-topic, gently redirect to the scenario.
- If max turns are almost reached, start to close the conversation naturally.

Opening line (say this first, before any student input):
{opening_line}
"""


def build_system_prompt(
    *,
    scenario_name: str,
    role_description: str,
    opening_line: str,
    difficulty: int = 1,
) -> str:
    """Return the system prompt string for a dialogue session."""
    return _SYSTEM_TEMPLATE.format(
        scenario_name=scenario_name,
        role_description=role_description,
        opening_line=opening_line,
        difficulty=max(1, min(3, difficulty)),
    )


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------

_REPLY_RE = re.compile(r"\[REPLY\](.*?)(?=\[JUDGE\]|$)", re.DOTALL | re.IGNORECASE)
_JUDGE_RE = re.compile(r"\[JUDGE\](.*?)$", re.DOTALL | re.IGNORECASE)


class ParsedLLMOutput(NamedTuple):
    reply: str   # in-character radio response
    judge: str   # SMCP assessment in Chinese


def parse_llm_output(raw: str) -> ParsedLLMOutput:
    """Extract [REPLY] and [JUDGE] sections from the LLM's raw text.

    Falls back gracefully when the LLM omits the markers.
    """
    reply_match = _REPLY_RE.search(raw)
    judge_match = _JUDGE_RE.search(raw)

    reply = reply_match.group(1).strip() if reply_match else raw.strip()
    judge = judge_match.group(1).strip() if judge_match else ""

    return ParsedLLMOutput(reply=reply, judge=judge)
