"""Schema-aware ingestion + migration-safe parsing.

`Chapter` is the explicit target schema. `parse_feature` is the single,
auditable boundary where raw ArcGIS features are coerced into that schema.
A feature that can't be parsed safely returns a ParseResult with an error
reason rather than raising — so one bad record never aborts a migration run.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, field_validator


class Coordinates(BaseModel):
    longitude: float
    latitude: float

    @field_validator("longitude")
    @classmethod
    def _valid_lon(cls, v: float) -> float:
        if not -180.0 <= v <= 180.0:
            raise ValueError(f"longitude out of range: {v}")
        return v

    @field_validator("latitude")
    @classmethod
    def _valid_lat(cls, v: float) -> float:
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"latitude out of range: {v}")
        return v


class Chapter(BaseModel):
    chapter_id: str
    chapter_name: str
    city: str
    state: str
    coordinates: Coordinates

    @field_validator("chapter_id", "chapter_name", "city", "state")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("required string is empty after stripping")
        return v

    @field_validator("state")
    @classmethod
    def _upper_state(cls, v: str) -> str:
        return v.upper()


@dataclass
class ParseResult:
    """Outcome of parsing one raw feature."""

    chapter: Chapter | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.chapter is not None


# Mapping from assessment field -> real ArcGIS attribute name.
FIELD_MAP = {
    "chapter_id": "ChapterID",
    "chapter_name": "University_Chapter",
    "city": "City",
    "state": "State",
}


def _coerce_str(value) -> str | None:
    """Type coercion with migration-safe null handling."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_feature(feature: dict) -> ParseResult:
    """Parse one raw ArcGIS feature into a Chapter.

    Returns ParseResult(chapter=None, error=...) on any missing/invalid
    field instead of raising, so the caller can log + skip and continue.
    """
    try:
        attrs = feature.get("attributes") or {}
        geometry = feature.get("geometry") or {}

        chapter_id = _coerce_str(attrs.get(FIELD_MAP["chapter_id"]))
        chapter_name = _coerce_str(attrs.get(FIELD_MAP["chapter_name"]))
        city = _coerce_str(attrs.get(FIELD_MAP["city"]))
        state = _coerce_str(attrs.get(FIELD_MAP["state"]))

        lon = geometry.get("x")
        lat = geometry.get("y")

        missing = [
            name
            for name, val in {
                "chapter_id": chapter_id,
                "chapter_name": chapter_name,
                "city": city,
                "state": state,
                "longitude": lon,
                "latitude": lat,
            }.items()
            if val is None
        ]
        if missing:
            return ParseResult(None, f"missing fields: {', '.join(missing)}")

        chapter = Chapter(
            chapter_id=chapter_id,
            chapter_name=chapter_name,
            city=city,
            state=state,
            coordinates=Coordinates(longitude=float(lon), latitude=float(lat)),
        )
        return ParseResult(chapter)

    except (ValueError, TypeError) as exc:
        return ParseResult(None, f"validation error: {exc}")
