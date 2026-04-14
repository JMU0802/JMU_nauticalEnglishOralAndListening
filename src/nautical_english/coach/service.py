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

import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

from nautical_english.llm.provider import BaseLLMProvider, LLMMessage
from nautical_english.coach.prompts import build_system_prompt, parse_llm_output
from nautical_english.scenario.repository import ScenarioRepository


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
    ) -> None:
        self._repo = scenario_repo
        self._provider = provider
        self._on_turn_complete = on_turn_complete
        self._on_error = on_error
        self._on_stream_chunk = on_stream_chunk

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

        # Append to message history
        self._messages.append({"role": "user", "content": text})

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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _llm_call(self, student_text: str, student_turn_idx: int) -> None:
        from nautical_english.llm.config import get_max_tokens

        full_content = ""
        try:
            for chunk in self._provider.stream_chat(
                self._messages,
                max_tokens=get_max_tokens(),
                temperature=0.7,
            ):
                full_content += chunk
                if self._on_stream_chunk:
                    self._on_stream_chunk(full_content)  # pass accumulated so far
        except Exception as exc:  # noqa: BLE001
            self._state = CoachState.READY
            if self._on_error:
                self._on_error(str(exc))
            return

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
