"""Extraction from the Ducks Unlimited ArcGIS FeatureServer.

The API paginates: each response carries `exceededTransferLimit: true` while
more records remain. We page with resultOffset/resultRecordCount until it's
absent. Transient HTTP failures are retried with exponential backoff; a
persistent failure raises (a *system* error that should fail the run).
"""

from __future__ import annotations

import logging
from typing import Generator

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import settings

logger = logging.getLogger(__name__)

BASE_PARAMS = {
    "where": "1=1",
    "outFields": "ChapterID,University_Chapter,City,State",
    "outSR": "4326",
    "returnGeometry": "true",
    "f": "json",
}


@retry(
    retry=retry_if_exception_type(requests.RequestException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _fetch_page(offset: int, page_size: int) -> dict:
    params = {**BASE_PARAMS, "resultOffset": offset, "resultRecordCount": page_size}
    resp = requests.get(settings.du_api_url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_all() -> Generator[dict, None, None]:
    """Yield every raw feature from the API, handling pagination."""
    offset = 0
    page_size = settings.du_api_page_size
    total = 0

    logger.info("Extraction starting (page_size=%d)", page_size)

    while True:
        data = _fetch_page(offset, page_size)

        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"ArcGIS API returned an error: {data['error']}")

        features = data.get("features", [])
        if not features:
            break

        yield from features
        total += len(features)
        logger.debug(
            "offset=%d fetched=%d running_total=%d", offset, len(features), total
        )

        if not data.get("exceededTransferLimit", False):
            break

        offset += page_size

    logger.info("Extraction complete: %d raw features", total)
