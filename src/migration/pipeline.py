"""Orchestration: extract -> transform -> load, with a run summary.

Design notes (worth being able to explain in the walk-through):
  * for a real run the target health check runs before load (a DRY_RUN
    skips the loader entirely, so extract + transform need no credentials).
  * data errors (one bad record) are logged and skipped inside transform;
    system errors (API down, target unreachable) propagate and fail the run.
  * main() returns a non-zero exit code on failure, which is what lets
    Cloud Run / Cloud Scheduler detect a failed migration.
"""

from __future__ import annotations

import logging
import sys
from uuid import uuid4

from .config import settings
from .extract import extract_all
from .load import get_loader
from .transform import transform

logger = logging.getLogger(__name__)


def run() -> dict:
    run_id = str(uuid4())

    logger.info(
        "Run starting: run_id=%s target=%s dry_run=%s",
        run_id,
        settings.target_backend,
        settings.dry_run,
    )

    chapters, stats = transform(extract_all())

    if settings.dry_run:
        logger.info(
            "DRY_RUN: run_id=%s skipping load of %d chapters",
            run_id,
            len(chapters),
        )
        loaded = 0
    else:
        loader = get_loader()
        if not loader.health_check():
            raise RuntimeError("Target health check failed, aborting run")

        loaded = loader.load(chapters, run_id=run_id)

    summary = {**stats.as_dict(), "loaded": loaded, "run_id": run_id}

    logger.info(
        "Run complete: run_id=%s received=%d parse_errors=%d filtered_out=%d "
        "duplicates=%d passed=%d loaded=%d",
        run_id,
        summary["total_received"],
        summary["parse_errors"],
        summary["filtered_out"],
        summary["duplicates"],
        summary["passed"],
        summary["loaded"],
    )

    return summary


def main() -> int:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        run()
        return 0
    except Exception as exc:  # noqa: BLE001 - top-level guard for exit code
        logger.exception("Migration failed: %s", exc)
        return 1
