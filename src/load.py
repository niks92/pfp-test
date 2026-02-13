"""Load stage — upsert chapter records into Postgres."""

import logging

import psycopg2
from psycopg2.extras import execute_values

from src.config import DBConfig
from src.transform import Chapter

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS university_chapters (
    chapter_id   VARCHAR(20) PRIMARY KEY,
    chapter_name VARCHAR(255) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(2)   NOT NULL,
    longitude    DOUBLE PRECISION NOT NULL,
    latitude     DOUBLE PRECISION NOT NULL,
    updated_at   TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO university_chapters
    (chapter_id, chapter_name, city, state, longitude, latitude)
VALUES %s
ON CONFLICT (chapter_id) DO UPDATE SET
    chapter_name = EXCLUDED.chapter_name,
    city         = EXCLUDED.city,
    state        = EXCLUDED.state,
    longitude    = EXCLUDED.longitude,
    latitude     = EXCLUDED.latitude,
    updated_at   = NOW()
"""


def ensure_table(db_config: DBConfig) -> None:
    """Create the university_chapters table if it does not exist."""
    with psycopg2.connect(db_config.connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    logger.info("Ensured university_chapters table exists")


def load_chapters(db_config: DBConfig, chapters: list[Chapter]) -> int:
    """Upsert chapters into Postgres. Returns the number of rows affected."""
    if not chapters:
        logger.warning("No chapters to load — skipping")
        return 0

    rows = [
        (c.chapter_id, c.chapter_name, c.city, c.state, c.longitude, c.latitude)
        for c in chapters
    ]

    with psycopg2.connect(db_config.connection_string) as conn:
        with conn.cursor() as cur:
            execute_values(cur, UPSERT_SQL, rows)
        conn.commit()

    logger.info("Loaded %d chapters into Postgres", len(rows))
    return len(rows)
