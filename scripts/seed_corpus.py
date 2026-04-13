"""初始化 SMCP 语料库数据库

用法：
    python scripts/seed_corpus.py [--db path/to/corpus.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from nautical_english.corpus.models import Base, Category, Phrase
from nautical_english.corpus.seed_data import SEED_DATA
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        existing = session.query(Category).count()
        if existing > 0:
            print(f"[seed] Database already contains {existing} categories. Skipping.")
            return

        total_phrases = 0
        for cat_en, cat_zh, phrases in SEED_DATA:
            cat = Category(name_en=cat_en, name_zh=cat_zh)
            session.add(cat)
            session.flush()
            for phrase_en, phrase_zh, difficulty in phrases:
                p = Phrase(
                    category_id=cat.id,
                    phrase_en=phrase_en,
                    phrase_zh=phrase_zh,
                    difficulty=difficulty,
                )
                session.add(p)
                total_phrases += 1

        session.commit()
        print(f"[seed] Inserted {len(SEED_DATA)} categories, {total_phrases} phrases.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SMCP corpus into SQLite.")
    parser.add_argument(
        "--db",
        default=str(ROOT / "corpus" / "db" / "corpus.db"),
        help="Path to the SQLite database file",
    )
    args = parser.parse_args()
    seed(Path(args.db))
    print("✅ Corpus seeded successfully.")


if __name__ == "__main__":
    main()
