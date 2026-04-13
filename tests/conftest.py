"""pytest 全局 fixture"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nautical_english.corpus.models import Base, Category, Phrase


@pytest.fixture
def in_memory_db():
    """提供一个预建表的内存 SQLite 引擎，每个测试独立。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def seeded_session(in_memory_db):
    """提供一个已写入少量种子数据的 Session。"""
    with Session(in_memory_db) as session:
        cat = Category(name_en="Navigation", name_zh="航行")
        session.add(cat)
        session.flush()
        phrases = [
            Phrase(category_id=cat.id, phrase_en="Alter course to starboard",
                   phrase_zh="向右转向", difficulty=1),
            Phrase(category_id=cat.id, phrase_en="Keep clear of me",
                   phrase_zh="请避让我船", difficulty=1),
            Phrase(category_id=cat.id, phrase_en="What are your intentions?",
                   phrase_zh="你的意图是什么？", difficulty=2),
        ]
        session.add_all(phrases)
        session.commit()
        yield session
