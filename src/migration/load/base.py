"""Loader interface — keeps the pipeline target-agnostic.

One interface with BigQuery and Postgres implementations, selected at runtime
via TARGET_BACKEND, so the same pipeline runs locally against Postgres and in
the cloud against BigQuery without code changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import Chapter


class BaseLoader(ABC):
    @abstractmethod
    def health_check(self) -> bool:
        """Verify target connectivity before loading data."""
        raise NotImplementedError

    @abstractmethod
    def load(self, chapters: list[Chapter], run_id: str) -> int:
        """Load chapters idempotently; return the number of rows written."""
        raise NotImplementedError
