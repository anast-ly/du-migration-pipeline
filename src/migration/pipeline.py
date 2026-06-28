"""Orchestration: extract -> transform -> load, with a run summary.

Design notes (worth being able to explain in the walk-through):
  * health_check() runs BEFORE extraction, so we fail fast if the target
    is unreachable instead of pulling data for nothing.
  * data errors (one bad record) are logged and skipped inside transform;
    system errors (API down, target unreachable) propagate and fail the run.
  * main() returns a non-zero exit code on failure, which is what lets
    Cloud Run / Cloud Scheduler detect a failed migration.
"""

from __future__ import annotations

import logging
import sys

from .config import settings
from .extract import extract_all
from .load import get_loader
from .transform import transform

logger = logging.getLogger(__name__)


def run() -> dict:
    logger.info(
        "Run starting: target=%s dry_run=%s",
        settings.target_backend,
        settings.dry_run,
    )

    loader = get_loader()
    if not loader.health_check():
        raise RuntimeError("Target health check failed — aborting before extract")

    chapters, stats = transform(extract_all())

    if settings.dry_run:
        logger.info("DRY_RUN: skipping load of %d chapters", len(chapters))
        loaded = 0
    else:
        loaded = loader.load(chapters)

    summary = {**stats.as_dict(), "loaded": loaded}
    logger.info(
        "Run complete: received=%d parse_errors=%d filtered_out=%d "
        "passed=%d loaded=%d",
        summary["total_received"],
        summary["parse_errors"],
        summary["filtered_out"],
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
