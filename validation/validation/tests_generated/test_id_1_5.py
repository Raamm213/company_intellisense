import pytest

from validation_utils import (
    extract_input_value,
    load_metadata,
    load_spec_rows,
    validate_field_value,
)


RULES = load_metadata()
COMPANY_RULE = RULES["Company Name"]
CASES = load_spec_rows("ID 1.5.csv")


@pytest.mark.parametrize("row", CASES, ids=[row["Test ID"] for row in CASES])
def test_company_name_ambiguous_input(row: dict) -> None:
    value = extract_input_value(row)
    errors = validate_field_value(
        "Company Name", value, COMPANY_RULE, strict_company_name=True
    )
    assert errors, f"{row['Test ID']}: expected errors but got none"
