"""Loader interface — the seam that makes the pipeline target-agnostic.

The assessment names both BigQuery (task 1) and Postgres (task 3) as the
migration target. Rather than choosing, we define one interface and two
implementations, selected at runtime via TARGET_BACKEND. This is the
'separation of concerns' the brief asks for, and lets a teammate run the
exact same pipeline locally against Postgres and in the cloud against BigQuery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import Chapter


class BaseLoader(ABC):
    @abstractmethod
    def health_check(self) -> bool:
        """Verify connectivity to the target before any data is pulled."""
        raise NotImplementedError

    @abstractmethod
    def load(self, chapters: list[Chapter], run_id: str) -> int:
        """Load chapters idempotently; return the number of rows written."""
        raise NotImplementedError
