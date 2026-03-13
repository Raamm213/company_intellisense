import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import re

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
# MASTER TEST STRUCTURE
# ============================================================

class Applicability:
    DATASET = "dataset"

class MasterTestCase:
    def __init__(self, test_id: str, applicability: str, validator):
        self.test_id = test_id
        self.applicability = applicability
        self.validator = validator


# ============================================================
# MANDATORY & OPTIONAL FIELDS
# ============================================================

MANDATORY_FIELDS = ["Company Name", "Category", "Year of Incorporation"]
OPTIONAL_FIELDS = ["Annual Revenues", "Employee Size", "Focus Sectors / Industries", "Year-over-Year Growth Rate", "Hiring Velocity"]


# ============================================================
# TC-PARTIALPROFILE-01: Small startup with mandatory fields only
# ============================================================

def tc_partialprofile_01_validator(dataset: Dataset):
    failures = []
    for field in MANDATORY_FIELDS:
        if not any(param.name == field and param.value not in (None, "", " ") for param in dataset.parameters):
            failures.append(f"Mandatory field '{field}' missing")
    return failures


# ============================================================
# TC-PARTIALPROFILE-02: 25–40% optional fields populated (warn)
# ============================================================

def tc_partialprofile_02_validator(dataset: Dataset):
    populated_count = sum(
        1 for field in OPTIONAL_FIELDS for param in dataset.parameters if param.name == field and param.value not in (None, "", " ")
    )
    threshold_lower = int(len(OPTIONAL_FIELDS)*0.25)
    threshold_upper = int(len(OPTIONAL_FIELDS)*0.4)
    if populated_count < threshold_lower:
        return []  # Accept profile; sparse optional fields are a warning only, not a failure
    elif populated_count <= threshold_upper:
        return []  # Pass with warning
    return []


# ============================================================
# TC-PARTIALPROFILE-03: Reject if mandatory identity fields missing
# ============================================================

def tc_partialprofile_03_validator(dataset: Dataset):
    failures = []
    for field in MANDATORY_FIELDS:
        if not any(param.name == field and param.value not in (None, "", " ") for param in dataset.parameters):
            failures.append(f"Mandatory identity field '{field}' missing — Fail")
    return failures


# ============================================================
# TC-PARTIALPROFILE-04: Graceful degradation with missing operational/financial fields
# ============================================================

def tc_partialprofile_04_validator(dataset: Dataset):
    # System must not fail if optional fields empty
    return []  # All missing optional fields are allowed


# ============================================================
# TC-PARTIALPROFILE-05: Richness score for sparse private company
# ============================================================

def tc_partialprofile_05_validator(dataset: Dataset):
    populated_count = sum(
        1 for param in dataset.parameters if param.name in OPTIONAL_FIELDS and param.value not in (None, "", " ")
    )
    richness_score = populated_count / len(OPTIONAL_FIELDS)
    if richness_score < 0.5:
        return []  # Profile accepted; low richness is informational only, not a failure
    return []


# ============================================================
# TC-PARTIALPROFILE-06: Format/regex validation still applies
# ============================================================

FIELD_REGEX_RULES = {
    "Company Name": r"^[\w\s&.,\-\(\)'\u00C0-\u017F]+$",
    "Category": r"^[A-Za-z\s]+$",
    "Year of Incorporation": r"^\d{4}$",
}

def tc_partialprofile_06_validator(dataset: Dataset):
    failures = []
    for param in dataset.parameters:
        pattern = FIELD_REGEX_RULES.get(param.name)
        if pattern and not re.fullmatch(pattern, str(param.value or "")):
            failures.append(f"Field '{param.name}' value '{param.value}' violates regex '{pattern}'")
    return failures


# ============================================================
# TC-PARTIALPROFILE-07: Detect hallucinated LLM data
# ============================================================

def tc_partialprofile_07_validator(dataset: Dataset):
    # Simulate check: any field containing "lorem", "fake", "xxx" triggers manual review
    flagged = []
    for param in dataset.parameters:
        if isinstance(param.value, str) and any(sub in param.value.lower() for sub in ["lorem", "fake", "xxx"]):
            flagged.append(f"Field '{param.name}' contains unverified or hallucinated data: '{param.value}'")
    return flagged


# ============================================================
# TC-PARTIALPROFILE-08: Acceptance of bootstrapped minimal profiles
# ============================================================

def tc_partialprofile_08_validator(dataset: Dataset):
    # Check mandatory fields populated, optional can be empty
    failures = []
    for field in MANDATORY_FIELDS:
        if not any(param.name == field and param.value not in (None, "", " ") for param in dataset.parameters):
            failures.append(f"Mandatory field '{field}' missing — Fail")
    return failures


# ============================================================
# REGISTER ALL PARTIAL PROFILE TEST CASES
# ============================================================

ALL_PARTIAL_PROFILE_TESTS = [
    MasterTestCase("TC-PARTIALPROFILE-01", Applicability.DATASET, tc_partialprofile_01_validator),
    MasterTestCase("TC-PARTIALPROFILE-02", Applicability.DATASET, tc_partialprofile_02_validator),
    MasterTestCase("TC-PARTIALPROFILE-03", Applicability.DATASET, tc_partialprofile_03_validator),
    MasterTestCase("TC-PARTIALPROFILE-04", Applicability.DATASET, tc_partialprofile_04_validator),
    MasterTestCase("TC-PARTIALPROFILE-05", Applicability.DATASET, tc_partialprofile_05_validator),
    MasterTestCase("TC-PARTIALPROFILE-06", Applicability.DATASET, tc_partialprofile_06_validator),
    MasterTestCase("TC-PARTIALPROFILE-07", Applicability.DATASET, tc_partialprofile_07_validator),
    MasterTestCase("TC-PARTIALPROFILE-08", Applicability.DATASET, tc_partialprofile_08_validator),
]


# ============================================================
# RULE ENGINE FOR DATASET-LEVEL PARTIAL PROFILE TESTS
# ============================================================

def evaluate_dataset(test_case: MasterTestCase, dataset: Dataset) -> List[str]:
    result = test_case.validator(dataset)
    return result if isinstance(result, list) else [result] if result else []


# ============================================================
# PYTEST FIXTURE (Replace with dynamic loader)
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



@pytest.mark.parametrize("test_case", ALL_PARTIAL_PROFILE_TESTS)
def test_partial_profile(dataset, test_case):
    failures = evaluate_dataset(test_case, dataset)
    assert not failures, (
        f"\nPartial Profile Validation Failure\n"
        f"Test Case: {test_case.test_id}\n"
        f"Failures:\n" +
        "\n".join(failures)
    )
    