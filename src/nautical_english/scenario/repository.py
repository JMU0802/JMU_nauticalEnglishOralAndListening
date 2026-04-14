"""场景库数据访问层"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nautical_english.scenario.models import DialogueTurn, Scenario, ScenarioBase


class ScenarioRepository:
    """提供场景库和对话回合的 CRUD 操作。"""

    def __init__(self, db_url: str | None = None) -> None:
        if db_url is None:
            from nautical_english.config import default_config
            db_path = default_config.db_path.parent / "scenarios.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, echo=False)
        ScenarioBase.metadata.create_all(engine)
        self._Session = sessionmaker(engine)

    # ── 场景 CRUD ─────────────────────────────────────────────────

    def get_all_scenarios(self) -> list[Scenario]:
        with self._Session() as session:
            return session.query(Scenario).order_by(Scenario.difficulty, Scenario.id).all()

    def get_scenarios_by_category(self, category: str) -> list[Scenario]:
        with self._Session() as session:
            return (
                session.query(Scenario)
                .filter(Scenario.category == category)
                .order_by(Scenario.difficulty)
                .all()
            )

    def get_scenario(self, scenario_id: int) -> Scenario | None:
        with self._Session() as session:
            return session.get(Scenario, scenario_id)

    def add_scenario(
        self,
        name_en: str,
        name_zh: str,
        category: str,
        description_en: str,
        description_zh: str,
        system_role_en: str,
        opening_line_en: str,
        difficulty: int = 1,
        max_turns: int = 8,
    ) -> int:
        with self._Session() as session:
            s = Scenario(
                name_en=name_en,
                name_zh=name_zh,
                category=category,
                difficulty=difficulty,
                description_en=description_en,
                description_zh=description_zh,
                system_role_en=system_role_en,
                opening_line_en=opening_line_en,
                max_turns=max_turns,
            )
            session.add(s)
            session.commit()
            return s.id

    def update_scenario(self, scenario_id: int, **kwargs) -> bool:
        with self._Session() as session:
            s = session.get(Scenario, scenario_id)
            if s is None:
                return False
            allowed = {
                "name_en", "name_zh", "category", "difficulty",
                "description_en", "description_zh", "system_role_en",
                "opening_line_en", "max_turns",
            }
            for k, v in kwargs.items():
                if k in allowed:
                    setattr(s, k, v)
            session.commit()
            return True

    def delete_scenario(self, scenario_id: int) -> bool:
        with self._Session() as session:
            s = session.get(Scenario, scenario_id)
            if s:
                session.delete(s)
                session.commit()
                return True
            return False

    def get_categories(self) -> list[str]:
        with self._Session() as session:
            rows = session.query(Scenario.category).distinct().all()
            return sorted({r[0] for r in rows})

    # ── 对话回合 ──────────────────────────────────────────────────

    @staticmethod
    def new_session_id() -> str:
        return str(uuid.uuid4())

    def save_turn(
        self,
        session_id: str,
        student_id: str,
        scenario_id: int,
        turn_index: int,
        role: str,
        content: str,
        *,
        audio_path: str | None = None,
        llm_reply: str | None = None,
        llm_judgement: str | None = None,
        score: float | None = None,
    ) -> int:
        with self._Session() as session:
            turn = DialogueTurn(
                session_id=session_id,
                student_id=student_id,
                scenario_id=scenario_id,
                turn_index=turn_index,
                role=role,
                content=content,
                audio_path=audio_path,
                llm_reply=llm_reply,
                llm_judgement=llm_judgement,
                score=score,
            )
            session.add(turn)
            session.commit()
            return turn.id

    def get_session_turns(self, session_id: str) -> list[DialogueTurn]:
        with self._Session() as session:
            return (
                session.query(DialogueTurn)
                .filter(DialogueTurn.session_id == session_id)
                .order_by(DialogueTurn.turn_index)
                .all()
            )

    def get_student_sessions(self, student_id: str, limit: int = 50) -> list[str]:
        """返回该学员最近的 session_id 列表（去重，时序倒序）。"""
        with self._Session() as session:
            rows = (
                session.query(DialogueTurn.session_id, DialogueTurn.created_at)
                .filter(DialogueTurn.student_id == student_id)
                .order_by(DialogueTurn.created_at.desc())
                .all()
            )
            seen: list[str] = []
            for row in rows:
                if row[0] not in seen:
                    seen.append(row[0])
                if len(seen) >= limit:
                    break
            return seen

    # ── 种子数据 ──────────────────────────────────────────────────

    def seed_if_empty(self) -> None:
        """若场景表为空，写入 10 条初始场景。"""
        with self._Session() as session:
            if session.query(Scenario).count() > 0:
                return
        from nautical_english.scenario.seed_data import SEED_SCENARIOS
        for s in SEED_SCENARIOS:
            self.add_scenario(**s)
