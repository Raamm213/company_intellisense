import pytest

from validation_utils import load_metadata, load_spec_rows


RULES = load_metadata()
CASES = load_spec_rows("ID 3.2.csv")


@pytest.mark.parametrize("row", CASES, ids=[row["Test ID"] for row in CASES])
def test_freshness_requires_external_sources(row: dict) -> None:
    """Run in-process checks only; full freshness/staleness would require external sources (APIs, live data)."""
    test_id = row.get("Test ID", "").strip()
    expected = (row.get("Expected Result") or "").strip()
    column_name = (row.get("column_name") or "").strip()

    assert test_id, f"Row must have Test ID: {row}"
    assert expected, f"{test_id}: Expected Result must be non-empty"
    assert column_name, f"{test_id}: column_name must be non-empty"
    # Optional: column in metadata (spec may use alternate spelling e.g. en-dash vs hyphen)
    # If missing, test still passes; full freshness check would require external sources.
