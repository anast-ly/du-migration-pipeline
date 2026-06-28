"""Unit tests for schema-aware parsing, coercion and null handling."""

from src.migration.schema import parse_feature


def _feature(**attrs_and_geom):
    geom = attrs_and_geom.pop("geometry", {"x": -120.0, "y": 38.0})
    attrs = {
        "ChapterID": "CA-0001",
        "University_Chapter": "Test Chapter",
        "City": "Testville",
        "State": "CA",
        **attrs_and_geom,
    }
    return {"attributes": attrs, "geometry": geom}


def test_valid_feature_parses():
    result = parse_feature(_feature())
    assert result.ok
    assert result.chapter.chapter_id == "CA-0001"
    assert result.chapter.state == "CA"


def test_state_is_uppercased():
    result = parse_feature(_feature(State="ca"))
    assert result.ok
    assert result.chapter.state == "CA"


def test_whitespace_is_stripped():
    result = parse_feature(_feature(University_Chapter="  Chico State DU  "))
    assert result.ok
    assert result.chapter.chapter_name == "Chico State DU"


def test_null_required_field_is_rejected():
    result = parse_feature(_feature(University_Chapter=None))
    assert not result.ok
    assert "missing" in result.error


def test_empty_string_field_is_rejected():
    result = parse_feature(_feature(City="   "))
    assert not result.ok


def test_missing_geometry_is_rejected():
    result = parse_feature(_feature(geometry={}))
    assert not result.ok
    assert "longitude" in result.error or "latitude" in result.error


def test_out_of_range_coordinate_is_rejected():
    result = parse_feature(_feature(geometry={"x": -999.0, "y": 38.0}))
    assert not result.ok
    assert "validation error" in result.error


def test_numeric_id_is_coerced_to_string():
    result = parse_feature(_feature(ChapterID=12345))
    assert result.ok
    assert result.chapter.chapter_id == "12345"
