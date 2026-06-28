"""Loader factory: pick the implementation from TARGET_BACKEND."""

from __future__ import annotations

from ..config import settings
from .base import BaseLoader
from .bigquery import BigQueryLoader
from .postgres import PostgresLoader

__all__ = ["BaseLoader", "BigQueryLoader", "PostgresLoader", "get_loader"]


def get_loader() -> BaseLoader:
    backend = settings.target_backend.lower()
    if backend == "bigquery":
        return BigQueryLoader()
    if backend == "postgres":
        return PostgresLoader()
    raise ValueError(
        f"Unknown TARGET_BACKEND={backend!r} (expected 'bigquery' or 'postgres')"
    )
