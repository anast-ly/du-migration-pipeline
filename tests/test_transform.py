"""Unit tests for the transform stage: filtering + stats accounting."""

import json
from pathlib import Path

from src.migration.transform import transform

FIXTURE = Path(__file__).parent / "fixtures" / "sample_api_response.json"


def _features():
    return json.loads(FIXTURE.read_text())["features"]


def test_filters_to_target_states():
    chapters, _ = transform(_features())
    states = {c.state for c in chapters}
    assert states <= {"CA", "OR", "WA"}
    assert "FL" not in states


def test_keeps_valid_ca_or_wa_records():
    chapters, _ = transform(_features())
    ids = {c.chapter_id for c in chapters}
    # CA-0042 (Chico), OR-0007, WA-0019 are valid CA/OR/WA records.
    assert {"CA-0042", "OR-0007", "WA-0019"} <= ids


def test_stats_account_for_every_record():
    _, stats = transform(_features())
    s = stats.as_dict()
    assert s["total_received"] == 6
    # FL is filtered out (not a target state).
    assert s["filtered_out"] >= 1
    # CA-9999 (null name) and OR-0500 (no geometry) are parse errors.
    assert s["parse_errors"] == 2
    assert s["passed"] == 3
    assert (
        s["passed"] + s["parse_errors"] + s["filtered_out"]
        == s["total_received"]
    )


def test_bad_records_do_not_abort_run():
    # The generator includes a null-name and a no-geometry record;
    # transform must skip them without raising.
    chapters, stats = transform(_features())
    assert len(chapters) == stats.as_dict()["passed"]
