"""SQLAlchemy ORM 数据模型 — 语料库、训练记录"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    """SMCP 场景类别，如 Navigation、Distress 等。"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    phrases: Mapped[list["Phrase"]] = relationship(
        "Phrase", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name_en={self.name_en!r}>"


class Phrase(Base):
    """SMCP 标准航海英语短语。"""

    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    phrase_en: Mapped[str] = mapped_column(Text, nullable=False)
    phrase_zh: Mapped[str] = mapped_column(Text, nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # 1=基础  2=中级  3=高级
    audio_path: Mapped[str | None] = mapped_column(String(500))

    category: Mapped["Category"] = relationship("Category", back_populates="phrases")
    records: Mapped[list["TrainingRecord"]] = relationship(
        "TrainingRecord", back_populates="phrase"
    )

    def __repr__(self) -> str:
        return f"<Phrase id={self.id} phrase_en={self.phrase_en!r}>"


class TrainingRecord(Base):
    """学员单次练习记录。"""

    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(100), nullable=False)
    phrase_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("phrases.id"), nullable=False
    )
    recognized_text: Mapped[str] = mapped_column(Text, nullable=False)
    wer_score: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    phrase: Mapped["Phrase"] = relationship("Phrase", back_populates="records")

    def __repr__(self) -> str:
        return (
            f"<TrainingRecord id={self.id} student={self.student_id!r} "
            f"score={self.overall_score}>"
        )
