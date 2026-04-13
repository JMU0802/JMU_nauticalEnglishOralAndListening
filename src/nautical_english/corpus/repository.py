"""数据访问层 — 对 SQLAlchemy Session 的封装"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from nautical_english.corpus.models import Base, Category, Phrase, TrainingRecord


class CorpusRepository:
    """提供语料库和训练记录的 CRUD 操作。

    Parameters
    ----------
    db_url:
        SQLAlchemy 连接字符串，默认使用 ``corpus/db/corpus.db``。
    seed:
        若为 ``True``，在内存数据库场景下自动写入测试种子数据。
    """

    def __init__(
        self,
        db_url: str | None = None,
        seed: bool = False,
    ) -> None:
        if db_url is None:
            from nautical_english.config import default_config  # noqa: PLC0415

            db_path: Path = default_config.db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(engine)
        self._Session = sessionmaker(engine)

        if seed:
            self._seed_minimal()

    # ── 类别操作 ─────────────────────────────────────────────────

    def get_all_categories(self) -> list[Category]:
        with self._Session() as session:
            return session.query(Category).all()

    # ── 短语操作 ─────────────────────────────────────────────────

    def get_all_phrases(self) -> list[Phrase]:
        with self._Session() as session:
            return session.query(Phrase).all()

    def get_phrases_by_difficulty(self, difficulty: int) -> list[Phrase]:
        with self._Session() as session:
            return (
                session.query(Phrase)
                .filter(Phrase.difficulty == difficulty)
                .all()
            )

    def get_phrases_by_category(self, category_id: int) -> list[Phrase]:
        with self._Session() as session:
            return (
                session.query(Phrase)
                .filter(Phrase.category_id == category_id)
                .all()
            )

    def add_phrase(
        self,
        category_id: int,
        phrase_en: str,
        phrase_zh: str,
        difficulty: int = 1,
        phonetic: str | None = None,
    ) -> int:
        with self._Session() as session:
            p = Phrase(
                category_id=category_id,
                phrase_en=phrase_en,
                phrase_zh=phrase_zh,
                difficulty=difficulty,
                phonetic=phonetic,
            )
            session.add(p)
            session.commit()
            return p.id

    def delete_phrase(self, phrase_id: int) -> None:
        with self._Session() as session:
            p = session.get(Phrase, phrase_id)
            if p:
                session.delete(p)
                session.commit()

    # ── 训练记录操作 ─────────────────────────────────────────────

    def save_training_record(
        self,
        student_id: str,
        phrase_id: int,
        recognized_text: str,
        wer_score: float,
        similarity_score: float,
        overall_score: float,
    ) -> int:
        with self._Session() as session:
            record = TrainingRecord(
                student_id=student_id,
                phrase_id=phrase_id,
                recognized_text=recognized_text,
                wer_score=wer_score,
                similarity_score=similarity_score,
                overall_score=overall_score,
            )
            session.add(record)
            session.commit()
            return record.id

    def get_student_records(self, student_id: str) -> list[TrainingRecord]:
        with self._Session() as session:
            return (
                session.query(TrainingRecord)
                .filter(TrainingRecord.student_id == student_id)
                .order_by(TrainingRecord.created_at)
                .all()
            )

    # ── 内部方法 ─────────────────────────────────────────────────

    def _seed_minimal(self) -> None:
        """写入最小测试种子数据（仅用于单元测试的内存数据库）。"""
        with self._Session() as session:
            if session.query(Category).count() > 0:
                return  # 已有数据，跳过
            cat = Category(name_en="Navigation", name_zh="航行")
            session.add(cat)
            session.flush()
            phrases = [
                Phrase(
                    category_id=cat.id,
                    phrase_en="Alter course to starboard",
                    phrase_zh="向右转向",
                    difficulty=1,
                ),
                Phrase(
                    category_id=cat.id,
                    phrase_en="Keep clear of me",
                    phrase_zh="请避让我船",
                    difficulty=1,
                ),
                Phrase(
                    category_id=cat.id,
                    phrase_en="What are your intentions?",
                    phrase_zh="你的意图是什么？",
                    difficulty=2,
                ),
            ]
            session.add_all(phrases)
            session.commit()
