import copy

import pytest

from validation_utils import (
    load_companies,
    load_mapping,
    load_metadata,
    load_spec_rows,
    parse_expected_outcome,
    validate_field_value,
)


RULES = load_metadata()
MAPPING = load_mapping()
COMPANIES = load_companies()
ALL_CASES = load_spec_rows("ID 2.4.csv")

# Only run tests for columns that have both a CSV mapping and a metadata rule (no skips).
CASES = [
    row for row in ALL_CASES
    if row.get("column_name", "").strip() in MAPPING
    and row.get("column_name", "").strip() in RULES
]


@pytest.mark.parametrize("row", CASES, ids=[(row.get("Test ID") or "").strip() or f"col_{i}" for i, row in enumerate(CASES)])
def test_mandatory_fields_only(row: dict) -> None:
    record = copy.deepcopy(COMPANIES[0])
    column_name = row.get("column_name", "").strip()
    expected = parse_expected_outcome(row.get("Expected Result", ""))

    csv_header = MAPPING[column_name]
    # Simulate NULL or missing key.
    record.pop(csv_header, None)

    rule = RULES[column_name]
    errors = validate_field_value(column_name, None, rule)

    if expected == "pass":
        assert not errors, f"{row['Test ID']}: {errors}"
    else:
        assert errors, f"{row['Test ID']}: expected errors but got none"
