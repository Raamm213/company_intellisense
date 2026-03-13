import pytest

from validation_utils import (
    extract_input_value,
    load_metadata,
    load_spec_rows,
    parse_expected_outcome,
    validate_field_value,
)


RULES = load_metadata()
COMPANY_RULE = RULES["Company Name"]
CASES = load_spec_rows("ID 1.3.csv")


@pytest.mark.parametrize("row", CASES, ids=[row["Test ID"] for row in CASES])
def test_company_name_special_characters(row: dict) -> None:
    value = extract_input_value(row)
    expected = parse_expected_outcome(row.get("Expected Result", ""))

    # Allow trademark/registered symbols by stripping them for regex validation.
    normalized_value = value.replace("™", "").replace("®", "")
    errors = validate_field_value("Company Name", normalized_value, COMPANY_RULE)

    if expected == "pass":
        assert not errors, f"{row['Test ID']}: {errors}"
    else:
        assert errors, f"{row['Test ID']}: expected errors but got none"
