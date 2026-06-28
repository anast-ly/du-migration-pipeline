"""Transformation: validate, coerce, filter to CA/OR/WA.

Business rules live here, not in the API query — so they're unit-testable
without a network and independent of how the source happens to be queried.
Returns the valid chapters plus a stats dict used for the run summary.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Iterable

from .config import settings
from .schema import Chapter, parse_feature

logger = logging.getLogger(__name__)

def _parse_states(raw: str) -> set[str]:
    return {s.strip().upper() for s in raw.split(",") if s.strip()}
    
TARGET_STATES = _parse_states(settings.target_states)

@dataclass
class TransformStats:
    total_received: int = 0
    parse_errors: int = 0
    filtered_out: int = 0
    passed: int = 0
    duplicates: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def transform(features: Iterable[dict]) -> tuple[list[Chapter], TransformStats]:
    stats = TransformStats()
    chapters: list[Chapter] = []
    seen_ids = set()

    for feature in features:
        stats.total_received += 1

        result = parse_feature(feature)
        if not result.ok:
            stats.parse_errors += 1
            attrs = feature.get("attributes") or {}
            source_id = attrs.get("OBJECTID") or attrs.get("ChapterID") or "unknown"

            logger.warning(
                "Skipping record source_id=%s reason=%s", source_id, result.error
                )
            continue

        chapter = result.chapter
        if chapter.state not in TARGET_STATES:
            stats.filtered_out += 1
            continue

        if chapter.chapter_id in seen_ids:
            stats.duplicates += 1
            logger.warning("Duplicate chapter_id skipped: %s", chapter.chapter_id)
            continue

        seen_ids.add(chapter.chapter_id)
        chapters.append(chapter)
        stats.passed += 1

    logger.info(
        "Transform complete: received=%d parse_errors=%d filtered_out=%d "
        "duplicates=%d passed=%d",
        stats.total_received,
        stats.parse_errors,
        stats.filtered_out,
        stats.duplicates,
        stats.passed,
    )
    return chapters, stats
