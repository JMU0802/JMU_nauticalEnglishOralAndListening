"""场景库与对话回合 ORM 数据模型"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ScenarioBase(DeclarativeBase):
    pass


class Scenario(ScenarioBase):
    """一个可供学员练习的 SMCP 场景。"""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Navigation")
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description_en: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description_zh: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # LLM 扮演的角色说明（注入系统提示）
    system_role_en: Mapped[str] = mapped_column(Text, nullable=False)
    # LLM 开场白（第一轮由 LLM 说）
    opening_line_en: Mapped[str] = mapped_column(Text, nullable=False)
    max_turns: Mapped[int] = mapped_column(Integer, default=8, nullable=False)

    turns: Mapped[list["DialogueTurn"]] = relationship(
        "DialogueTurn", back_populates="scenario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} name_en={self.name_en!r}>"


class DialogueTurn(ScenarioBase):
    """单次对话会话中的一个回合（coach 或 student）。"""

    __tablename__ = "dialogue_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scenario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scenarios.id"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "coach" | "student"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[str | None] = mapped_column(String(500))
    # LLM 点评文本（只有 role=student 的回合才有）
    llm_reply: Mapped[str | None] = mapped_column(Text)
    llm_judgement: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="turns")

    def __repr__(self) -> str:
        return f"<DialogueTurn session={self.session_id!r} turn={self.turn_index} role={self.role!r}>"
