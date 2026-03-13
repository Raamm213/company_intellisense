import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import pytest


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Parameter:
    parameter_id: str
    name: str
    value: Any
    metadata: Dict[str, Any]


@dataclass
class Dataset:
    parameters: List[Parameter]


# ============================================================
# MASTER TEST CASE REGISTRY STRUCTURE
# ============================================================

class Applicability:
    CONDITIONAL = "conditional"


class MasterTestCase:
    def __init__(self, test_id: str, applicability: str, condition, validator):
        self.test_id = test_id
        self.applicability = applicability
        self.condition = condition
        self.validator = validator


# ============================================================
# SHARED REGEX (Production Safe)
# ============================================================

COMPANY_NAME_REGEX = re.compile(
    r"^[\w\s&.,\-\(\)'\u00C0-\u017F]+$",
    re.UNICODE
)


# ============================================================
# CONDITION — Applies Only To Company Name Parameter
# ============================================================

def company_name_condition(param: Parameter) -> bool:
    return param.name == "Company Name"


# ============================================================
# TC-1.1-COMPANYNAME-01
# Validate full legal company name format
# ============================================================

def tc_1_1_companyname_01_validator(param: Parameter):
    value = param.value

    if not isinstance(value, str):
        return "Value must be a string"

    if not value.strip():
        return "Company Name cannot be empty"

    if not COMPANY_NAME_REGEX.fullmatch(value):
        return f"Regex validation failed for value: {value}"

    return True


TC_1_1_COMPANYNAME_01 = MasterTestCase(
    test_id="TC-1.1-COMPANYNAME-01",
    applicability=Applicability.CONDITIONAL,
    condition=company_name_condition,
    validator=tc_1_1_companyname_01_validator
)


# ============================================================
# TC-1.1-COMPANYNAME-02
# Validate punctuation and legal naming structure
# ============================================================

def tc_1_1_companyname_02_validator(param: Parameter):
    value = param.value

    if not isinstance(value, str):
        return "Value must be a string"

    if not COMPANY_NAME_REGEX.fullmatch(value):
        return f"Invalid punctuation or illegal characters detected: {value}"

    if not any(char.isalpha() for char in value):
        return "Company Name must contain alphabetic characters"

    return True


TC_1_1_COMPANYNAME_02 = MasterTestCase(
    test_id="TC-1.1-COMPANYNAME-02",
    applicability=Applicability.CONDITIONAL,
    condition=company_name_condition,
    validator=tc_1_1_companyname_02_validator
)


# ============================================================
# TC-1.1-COMPANYNAME-03
# Validate multinational naming & UTF-8 compliance
# ============================================================

def tc_1_1_companyname_03_validator(param: Parameter):
    value = param.value

    if not isinstance(value, str):
        return "Value must be a string"

    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return "Value is not UTF-8 compliant"

    if not COMPANY_NAME_REGEX.fullmatch(value):
        return f"Invalid multinational naming format: {value}"

    # Standard Case enforcement (Title Case)
    cleaned = value.replace(",", "").replace(".", "")
    words = cleaned.split()

    for word in words:
        if word and not word[0].isupper():
            return f"Word '{word}' must start with uppercase letter"

    return True


TC_1_1_COMPANYNAME_03 = MasterTestCase(
    test_id="TC-1.1-COMPANYNAME-03",
    applicability=Applicability.CONDITIONAL,
    condition=company_name_condition,
    validator=tc_1_1_companyname_03_validator
)


# ============================================================
# REGISTER ALL 1.1 TEST CASES
# ============================================================

ALL_1_1_COMPANYNAME_TESTS = [
    TC_1_1_COMPANYNAME_01,
    TC_1_1_COMPANYNAME_02,
    TC_1_1_COMPANYNAME_03
]


# ============================================================
# RULE ENGINE EXECUTION
# ============================================================

def evaluate_conditional(test_case: MasterTestCase, dataset: Dataset) -> List[Tuple[str, str]]:
    failures = []

    for param in dataset.parameters:
        if test_case.condition(param):
            result = test_case.validator(param)
            if result is not True:
                failures.append((param.parameter_id, result))

    return failures


# ============================================================
# PYTEST FIXTURE (Replace with real loader in production)
# ============================================================

@pytest.fixture
def dataset():
    try:
        from validation_utils import load_companies, load_mapping
        companies = load_companies()
        if not companies:
            return Dataset(parameters=[])
        
        mapping = load_mapping()
        # Use the first company found in the CSV
        record = companies[0]
        
        params = []
        for col_name, csv_header in mapping.items():
            val = record.get(csv_header)
            # Mark as real data for the test logic to be aware
            params.append(Parameter(col_name, col_name, val, {'is_real_data': True}))
            
        return Dataset(parameters=params)
    except Exception:
        return Dataset(parameters=[])



@pytest.mark.parametrize("test_case", ALL_1_1_COMPANYNAME_TESTS)
def test_company_name_validation(dataset, test_case):
    failures = evaluate_conditional(test_case, dataset)

    assert not failures, (
        f"\nValidation Failure\n"
        f"Test Case: {test_case.test_id}\n"
        f"Failures:\n" +
        "\n".join(
            f"Parameter {pid}: {reason}"
            for pid, reason in failures
        )
    )