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

    def get_all_records(self, limit: int = 500) -> list[TrainingRecord]:
        """返回所有学生的训练记录（管理端仪表盘使用）。"""
        with self._Session() as session:
            return (
                session.query(TrainingRecord)
                .order_by(TrainingRecord.created_at.desc())
                .limit(limit)
                .all()
            )

    def get_all_student_ids(self) -> list[str]:
        """返回有过训练记录的所有学生 ID。"""
        with self._Session() as session:
            rows = (
                session.query(TrainingRecord.student_id)
                .distinct()
                .all()
            )
            return [r[0] for r in rows]

    def get_phrase_stats(self) -> list[dict]:
        """返回每条短语的练习次数和平均分。

        Returns
        -------
        list of dict with keys: phrase_id, phrase_en, count, avg_score
        """
        with self._Session() as session:
            results = (
                session.query(
                    TrainingRecord.phrase_id,
                    Phrase.phrase_en,
                )
                .join(Phrase, TrainingRecord.phrase_id == Phrase.id)
                .all()
            )
            # 汇总统计
            from collections import defaultdict
            agg: dict[int, dict] = defaultdict(lambda: {"phrase_en": "", "scores": []})
            for phrase_id, phrase_en in results:
                agg[phrase_id]["phrase_en"] = phrase_en
            # 重新查带分数的
            rows = (
                session.query(
                    TrainingRecord.phrase_id,
                    Phrase.phrase_en,
                    TrainingRecord.overall_score,
                )
                .join(Phrase, TrainingRecord.phrase_id == Phrase.id)
                .all()
            )
            agg2: dict[int, dict] = defaultdict(lambda: {"phrase_en": "", "scores": []})
            for phrase_id, phrase_en, score in rows:
                agg2[phrase_id]["phrase_en"] = phrase_en
                agg2[phrase_id]["scores"].append(score)

            stats = []
            for pid, data in sorted(agg2.items()):
                scores = data["scores"]
                stats.append({
                    "phrase_id":  pid,
                    "phrase_en":  data["phrase_en"],
                    "count":      len(scores),
                    "avg_score":  sum(scores) / len(scores) if scores else 0.0,
                })
            return stats

    def update_phrase(
        self,
        phrase_id: int,
        *,
        phrase_en: str | None = None,
        phrase_zh: str | None = None,
        category_id: int | None = None,
        difficulty: int | None = None,
        phonetic: str | None = None,
    ) -> bool:
        """更新短语字段，返回 True 表示成功，False 表示短语不存在。"""
        with self._Session() as session:
            p = session.get(Phrase, phrase_id)
            if p is None:
                return False
            if phrase_en is not None:
                p.phrase_en = phrase_en
            if phrase_zh is not None:
                p.phrase_zh = phrase_zh
            if category_id is not None:
                p.category_id = category_id
            if difficulty is not None:
                p.difficulty = difficulty
            if phonetic is not None:
                p.phonetic = phonetic
            session.commit()
            return True

    def add_category(self, name_en: str, name_zh: str, description: str = "") -> int:
        """新增类别，返回新类别 id。"""
        with self._Session() as session:
            cat = Category(name_en=name_en, name_zh=name_zh, description=description)
            session.add(cat)
            session.commit()
            return cat.id

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
