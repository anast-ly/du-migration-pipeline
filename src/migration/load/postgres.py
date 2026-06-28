"""Postgres loader — local target (docker-compose) and Cloud SQL.

Idempotent via INSERT ... ON CONFLICT (chapter_id) DO UPDATE, so re-running
upserts rather than duplicating. chapter_id is the natural key from the
source system, which makes this the migration-safe write strategy.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import execute_values

from ..config import settings
from ..schema import Chapter
from .base import BaseLoader

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS university_chapters (
    chapter_id   VARCHAR(50)      PRIMARY KEY,
    chapter_name VARCHAR(255)     NOT NULL,
    city         VARCHAR(255)     NOT NULL,
    state        VARCHAR(2)       NOT NULL,
    longitude    DOUBLE PRECISION NOT NULL,
    latitude     DOUBLE PRECISION NOT NULL,
    migrated_at  TIMESTAMPTZ      NOT NULL
);
"""

UPSERT_SQL = """
INSERT INTO university_chapters
    (chapter_id, chapter_name, city, state, longitude, latitude, migrated_at)
VALUES %s
ON CONFLICT (chapter_id) DO UPDATE SET
    chapter_name = EXCLUDED.chapter_name,
    city         = EXCLUDED.city,
    state        = EXCLUDED.state,
    longitude    = EXCLUDED.longitude,
    latitude     = EXCLUDED.latitude,
    migrated_at  = EXCLUDED.migrated_at;
"""


class PostgresLoader(BaseLoader):
    def __init__(self) -> None:
        self.conn_params = {
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "dbname": settings.postgres_db,
            "user": settings.postgres_user,
            "password": settings.postgres_password,
        }

    def _connect(self):
        return psycopg2.connect(**self.conn_params)

    def health_check(self) -> bool:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
            logger.info("Postgres health check passed")
            return True
        except Exception as exc:  # noqa: BLE001 - surfaced as a failed health check
            logger.error("Postgres health check failed: %s", exc)
            return False

    def load(self, chapters: list[Chapter]) -> int:
        if not chapters:
            logger.warning("No rows to load into Postgres")
            return 0

        now = datetime.now(timezone.utc)
        rows = [
            (
                c.chapter_id,
                c.chapter_name,
                c.city,
                c.state,
                c.coordinates.longitude,
                c.coordinates.latitude,
                now,
            )
            for c in chapters
        ]

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            execute_values(cur, UPSERT_SQL, rows)
            conn.commit()

        logger.info("Upserted %d rows into university_chapters", len(rows))
        return len(rows)
