"""BigQuery loader — primary cloud target.

Idempotent by design: WRITE_TRUNCATE replaces the table contents on every
run, so re-running the migration never produces duplicates (the migration
is a full, repeatable snapshot of the source). The dataset and table are
created if absent so a first run works against an empty project.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from google.cloud import bigquery

from ..config import settings
from ..schema import Chapter
from .base import BaseLoader

logger = logging.getLogger(__name__)

SCHEMA = [
    bigquery.SchemaField("chapter_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("chapter_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("state", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("migrated_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("migration_run_id", "STRING", mode="REQUIRED"),
]


class BigQueryLoader(BaseLoader):
    def __init__(self) -> None:
        self.client = bigquery.Client(project=settings.gcp_project_id)
        self.dataset_id = f"{settings.gcp_project_id}.{settings.bq_dataset}"
        self.table_id = f"{self.dataset_id}.{settings.bq_table}"

    def health_check(self) -> bool:
        try:
            self.client.query("SELECT 1").result()
            logger.info("BigQuery health check passed")
            return True
        except Exception as exc:  # noqa: BLE001 - surfaced as a failed health check
            logger.error("BigQuery health check failed: %s", exc)
            return False

    def _ensure_dataset(self) -> None:
        dataset = bigquery.Dataset(self.dataset_id)
        dataset.location = settings.bq_location
        self.client.create_dataset(dataset, exists_ok=True)
        logger.info("Dataset ready: %s", self.dataset_id)

    def _ensure_table(self) -> None:
        table = bigquery.Table(self.table_id, schema=SCHEMA)
        self.client.create_table(table, exists_ok=True)
        logger.info("Table ready: %s", self.table_id)

    def load(self, chapters: list[Chapter], run_id: str) -> int:
        self._ensure_dataset()
        self._ensure_table()

        now = datetime.now(timezone.utc).isoformat()
        rows = [
            {
                "chapter_id": c.chapter_id,
                "chapter_name": c.chapter_name,
                "city": c.city,
                "state": c.state,
                "longitude": c.coordinates.longitude,
                "latitude": c.coordinates.latitude,
                "migrated_at": now,
                "migration_run_id": run_id,
            }
            for c in chapters
        ]

        if not rows:
            logger.warning("No rows to load into BigQuery")
            return 0

        job_config = bigquery.LoadJobConfig(
            schema=SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        self.client.load_table_from_json(
            rows, self.table_id, job_config=job_config
        ).result()

        logger.info("Loaded %d rows into %s", len(rows), self.table_id)
        return len(rows)
