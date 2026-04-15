"""CoachService — orchestrates a single SMCP dialogue session.

State machine::

    IDLE ──► READY ──► WAITING_LLM ──► READY
                  └──────────────────► DONE

Usage::

    svc = CoachService(scenario_repo, llm_provider)
    svc.start_session(scenario_id=1, student_id="s001")
    # The coach sends the opening line automatically via on_turn_complete callback.

    svc.student_speak("Xiamen VTS this is MV Ocean Star, over.")
    # → triggers async LLM call → on_turn_complete(llm_reply, judgement, score)

    svc.end_session()  # persist summary
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

from nautical_english.llm.provider import BaseLLMProvider, LLMMessage
from nautical_english.coach.prompts import build_system_prompt, inject_rag_context, parse_llm_output
from nautical_english.scenario.repository import ScenarioRepository
from nautical_english.rag.client import RAGClient

log = logging.getLogger("coach")


# ---------------------------------------------------------------------------
# State + callbacks
# ---------------------------------------------------------------------------

class CoachState(Enum):
    IDLE = auto()
    READY = auto()          # waiting for student input
    WAITING_LLM = auto()    # LLM call in flight
    DONE = auto()


@dataclass
class TurnResult:
    session_id: str
    turn_index: int
    student_text: str
    llm_reply: str
    judgement: str          # Chinese SMCP assessment
    score: float            # 0–100 heuristic


# ---------------------------------------------------------------------------
# CoachService
# ---------------------------------------------------------------------------

class CoachService:
    """High-level dialogue controller.

    Parameters
    ----------
    scenario_repo:
        :class:`~nautical_english.scenario.repository.ScenarioRepository`
    provider:
        An LLM provider instance
    on_turn_complete:
        Called on the main thread (via ``result_callback``) after each LLM reply.
    on_error:
        Called with an error message string when the LLM fails.
    """

    MAX_SCORE = 100.0
    _SMCP_KEYWORDS = {
        "over", "out", "roger", "wilco", "mayday", "pan pan",
        "securite", "i say again", "do you read", "received",
        "affirmative", "negative", "standby",
    }

    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        provider: BaseLLMProvider,
        on_turn_complete: Optional[Callable[[TurnResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_stream_chunk: Optional[Callable[[str], None]] = None,
        rag_client: Optional[RAGClient] = None,
    ) -> None:
        self._repo = scenario_repo
        self._provider = provider
        self._on_turn_complete = on_turn_complete
        self._on_error = on_error
        self._on_stream_chunk = on_stream_chunk
        self._rag_client = rag_client

        self._state = CoachState.IDLE
        self._session_id: str = ""
        self._student_id: str = ""
        self._scenario_id: int = 0
        self._messages: list[LLMMessage] = []
        self._turn_index: int = 0
        self._max_turns: int = 8

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CoachState:
        return self._state

    @property
    def session_id(self) -> str:
        return self._session_id

    def start_session(self, scenario_id: int, student_id: str) -> str:
        """Initialise a new dialogue session.

        Returns the opening line the coach should display immediately.
        """
        scenario = self._repo.get_scenario(scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found")

        self._session_id = self._repo.new_session_id()
        self._student_id = student_id
        self._scenario_id = scenario_id
        self._turn_index = 0
        self._max_turns = scenario.max_turns
        self._state = CoachState.READY

        system_prompt = build_system_prompt(
            scenario_name=scenario.name_en,
            role_description=scenario.system_role_en,
            opening_line=scenario.opening_line_en,
            difficulty=scenario.difficulty,
        )
        self._messages = [{"role": "system", "content": system_prompt}]

        # Persist coach opening turn
        self._repo.save_turn(
            session_id=self._session_id,
            student_id=self._student_id,
            scenario_id=self._scenario_id,
            turn_index=self._turn_index,
            role="coach",
            content=scenario.opening_line_en,
        )
        self._turn_index += 1

        return scenario.opening_line_en

    def student_speak(self, text: str, audio_path: str | None = None) -> None:
        """Process the student's utterance asynchronously.

        Saves the student turn and fires an LLM call in a daemon thread.
        ``on_turn_complete`` is invoked when the reply arrives.
        """
        if self._state != CoachState.READY:
            return
        self._state = CoachState.WAITING_LLM

        # Save student turn
        student_turn_idx = self._turn_index
        self._repo.save_turn(
            session_id=self._session_id,
            student_id=self._student_id,
            scenario_id=self._scenario_id,
            turn_index=student_turn_idx,
            role="student",
            content=text,
            audio_path=audio_path,
        )
        self._turn_index += 1

        # Append to message history (keep system prompt + last 8 messages = 4 turns)
        # RAG 增强：非阻塞查询，失败时退化为原始消息
        augmented_text = text
        if self._rag_client is not None:
            try:
                rag_ctx = self._rag_client.query(text)
                augmented_text = inject_rag_context(text, rag_ctx)
                if rag_ctx:
                    log.debug("RAG context injected (%d chars)", len(rag_ctx))
            except Exception as exc:  # noqa: BLE001
                log.debug("RAG query skipped: %s", exc)
        self._messages.append({"role": "user", "content": augmented_text})
        if len(self._messages) > 9:  # 1 system + 8 dialogue
            self._messages = self._messages[:1] + self._messages[-8:]

        # Fire async LLM call
        t = threading.Thread(
            target=self._llm_call,
            args=(text, student_turn_idx),
            daemon=True,
        )
        t.start()

    def end_session(self) -> None:
        """Mark the session as complete."""
        self._state = CoachState.DONE

    def evaluate_session(
        self,
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Generate a comprehensive SMCP evaluation for the session asynchronously.

        Calls *on_complete* with the evaluation text (from background thread).
        """
        t = threading.Thread(
            target=self._evaluation_call,
            args=(on_complete, on_error),
            daemon=True,
        )
        t.start()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evaluation_call(
        self,
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        turns = self._repo.get_session_turns(self._session_id)
        student_turns = [t for t in turns if t.role == "student"]

        if not student_turns:
            on_complete("暂无学生发言记录，无法生成评估。")
            return

        # Build numbered list of student utterances with per-turn judgement
        lines: list[str] = []
        judge_map = {t.turn_index - 1: t.llm_judgement for t in turns
                     if t.role == "coach" and t.llm_judgement}
        for i, st in enumerate(student_turns):
            judge = judge_map.get(st.turn_index + 1, "")
            lines.append(f"第{i+1}句：{st.content}")
            if judge:
                lines.append(f"  教练评语：{judge}")

        turns_text = "\n".join(lines)

        messages: list[LLMMessage] = [
            {
                "role": "system",
                "content": (
                    "You are a senior SMCP (Standard Marine Communication Phrases) examiner. "
                    "Evaluate the student's radio communication performance and respond ENTIRELY in Chinese. "
                    "Be specific, structured, and constructive."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"请对以下学生在SMCP对话练习中的全部发言进行综合评估：\n\n"
                    f"{turns_text}\n\n"
                    "请按以下结构作答（每项都要具体）：\n"
                    "【综合评价】整体SMCP规范用语掌握程度（2-3句）\n"
                    "【主要优点】列出2-3个具体做得好的地方\n"
                    "【主要问题】列出2-3个需要改进的具体问题，并给出正确说法\n"
                    "【建议复习】列出3-5个需要重点复习的SMCP标准短语"
                ),
            },
        ]

        try:
            full_content = ""
            for chunk in self._provider.stream_chat(
                messages,
                max_tokens=500,
                temperature=0.5,
            ):
                full_content += chunk
            on_complete(full_content)
        except Exception as exc:  # noqa: BLE001
            on_error(str(exc))

    def _llm_call(self, student_text: str, student_turn_idx: int) -> None:
        from nautical_english.llm.config import get_max_tokens

        t_start = time.perf_counter()
        log.info("[TIMING] _llm_call start  provider=%s  model=%s  msgs=%d",
                 self._provider.name, self._provider.model, len(self._messages))

        full_content = ""
        first_chunk = True
        try:
            for chunk in self._provider.stream_chat(
                self._messages,
                max_tokens=get_max_tokens(),
                temperature=0.7,
            ):
                if first_chunk:
                    log.info("[TIMING] First token in %.2fs", time.perf_counter() - t_start)
                    first_chunk = False
                full_content += chunk
                if self._on_stream_chunk:
                    self._on_stream_chunk(full_content)  # pass accumulated so far
        except Exception as exc:  # noqa: BLE001
            log.error("[TIMING] LLM error after %.2fs: %s", time.perf_counter() - t_start, exc)
            self._state = CoachState.READY
            if self._on_error:
                self._on_error(str(exc))
            return

        log.info("[TIMING] LLM complete in %.2fs  total_chars=%d",
                 time.perf_counter() - t_start, len(full_content))

        parsed = parse_llm_output(full_content)
        score = self._score_student_turn(student_text)

        # Append assistant turn to history
        self._messages.append({"role": "assistant", "content": full_content})

        # Persist coach reply
        coach_turn_idx = self._turn_index
        self._repo.save_turn(
            session_id=self._session_id,
            student_id=self._student_id,
            scenario_id=self._scenario_id,
            turn_index=coach_turn_idx,
            role="coach",
            content=parsed.reply,
            llm_reply=parsed.reply,
            llm_judgement=parsed.judge,
            score=score,
        )
        self._turn_index += 1

        result = TurnResult(
            session_id=self._session_id,
            turn_index=coach_turn_idx,
            student_text=student_text,
            llm_reply=parsed.reply,
            judgement=parsed.judge,
            score=score,
        )

        # Transition state
        done = self._turn_index >= self._max_turns * 2
        self._state = CoachState.DONE if done else CoachState.READY

        if self._on_turn_complete:
            self._on_turn_complete(result)

    def _score_student_turn(self, text: str) -> float:
        """Heuristic SMCP score [0-100] based on keyword presence."""
        lower = text.lower()
        hits = sum(1 for kw in self._SMCP_KEYWORDS if kw in lower)
        # Base score: 50 + 10 per keyword, capped at 100
        return min(self.MAX_SCORE, 50.0 + hits * 10.0)
