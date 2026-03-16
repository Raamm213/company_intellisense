from typing import Dict, List

import pytest

# ------------------------------------------------------------------
# Relationship Validation Engine
# ------------------------------------------------------------------


class FieldRelationshipValidator:
    """
    Enforces cross-field population consistency rules.

    Rule:
        If ANY related field is populated → target field should be populated.
        If ALL related fields are NULL → target field MUST be NULL.
    """

    def is_populated(self, value):
        return value is not None and not (isinstance(value, str) and not value.strip())

    def validate(
        self, record: Dict[str, any], target: str, related: List[str]
    ) -> List[str]:
        errors = []

        related_values = [record.get(field) for field in related]
        any_related_populated = any(self.is_populated(v) for v in related_values)
        all_related_null = all(not self.is_populated(v) for v in related_values)

        target_value = record.get(target)
        target_populated = self.is_populated(target_value)

        if any_related_populated and not target_populated:
            errors.append(f"{target} should be populated because related fields exist.")

        if all_related_null and target_populated:
            errors.append(f"{target} must be NULL because related fields are NULL.")

        return errors


# ------------------------------------------------------------------
# Metadata Derived From CSV
# ------------------------------------------------------------------

RELATIONSHIP_RULES = [
    ("Short Name", ["Company Name"], "2.5.2"),
    ("Logo", ["Company Name"], "2.5.3"),
    ("Category", ["Nature of Company", "Focus Sectors / Industries"], "2.5.4"),
    (
        "Overview of the Company",
        [
            "Services / Offerings / Products",
            "Vision",
            "Mission",
            "Core Value Proposition",
        ],
        "2.5.6",
    ),
    ("Number of Offices (beyond HQ)", ["Office Locations"], "2.5.10"),
    ("Office Locations", ["Countries Operating In"], "2.5.11"),
    ("Hiring Velocity", ["Employee Size"], "2.5.13"),
    ("Employee Turnover", ["Employee Size"], "2.5.14"),
    ("Average Retention Tenure", ["Employee Turnover"], "2.5.15"),
    ("Pain Points Being Addressed", ["Focus Sectors / Industries"], "2.5.16"),
    ("Focus Sectors / Industries", ["Category", "Nature of Company"], "2.5.17"),
    ("Services / Offerings / Products", ["Focus Sectors / Industries"], "2.5.18"),
    (
        "Top Customers by Client Segments",
        ["Category", "Services / Offerings / Products"],
        "2.5.19",
    ),
    (
        "Core Value Proposition",
        ["Pain Points Being Addressed", "Services / Offerings / Products"],
        "2.5.20",
    ),
    ("Vision", ["Core Value Proposition"], "2.5.21"),
    ("Mission", ["Vision", "Core Value Proposition"], "2.5.22"),
    ("Values", ["Vision", "Mission"], "2.5.23"),
    ("Quality of Website", ["Website URL"], "2.5.33"),
    ("Website Rating", ["Website URL"], "2.5.34"),
    ("Website Traffic Rank", ["Website URL"], "2.5.35"),
    (
        "Social Media Followers – Combined",
        [
            "Instagram Page URL",
            "LinkedIn Profile URL",
            "Facebook Page URL",
            "Twitter (X) Handle",
        ],
        "2.5.36",
    ),
    ("CEO LinkedIn URL", ["CEO Name"], "2.5.45"),
    ("Profitability Status", ["Annual Profits"], "2.5.65"),
    (
        "Market Share (%)",
        ["Annual Revenues", "Total Addressable Market (TAM)"],
        "2.5.66",
    ),
    ("Key Investors / Backers", ["Recent Funding Rounds"], "2.5.67"),
    ("Total Capital Raised", ["Recent Funding Rounds"], "2.5.69"),
    (
        "CAC:LTV Ratio",
        ["Customer Acquisition Cost (CAC)", "Customer Lifetime Value (CLV)"],
        "2.5.74",
    ),
    (
        "Customer Concentration Risk",
        ["Revenue Mix", "Top Customers by Client Segments"],
        "2.5.77",
    ),
    ("Runway", ["Total Capital Raised", "Burn Rate"], "2.5.79"),
    ("Burn Multiplier", ["Burn Rate", "Annual Revenues"], "2.5.80"),
    (
        "Serviceable Addressable Market (SAM)",
        ["Total Addressable Market (TAM)"],
        "2.5.109",
    ),
    (
        "Serviceable Obtainable Market (SOM)",
        ["Serviceable Addressable Market (SAM)"],
        "2.5.110",
    ),
    (
        "Central vs peripheral location",
        ["Company Headquarters", "Office Locations"],
        "2.5.123",
    ),
    (
        "Commute time from airport",
        ["Company Headquarters", "Office Locations"],
        "2.5.126",
    ),
    ("Office zone type", ["Company Headquarters", "Office Locations"], "2.5.127"),
    ("Area safety", ["Company Headquarters", "Office Locations"], "2.5.128"),
    (
        "Company maturity",
        ["Year of Incorporation", "Employee Size", "Annual Revenues"],
        "2.5.146",
    ),
    ("Client quality", ["Company Name"], "2.5.148"),
    ("Layoff history", ["Recent News"], "2.5.149"),
    ("Global exposure", ["Countries Operating In"], "2.5.160"),
    ("Crisis behavior", ["Recent News", "Legal Issues / Controversies"], "2.5.163"),
]


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


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
            params.append(Parameter(col_name, col_name, val, {"is_real_data": True}))

        return Dataset(parameters=params)
    except Exception:
        return Dataset(parameters=[])


@pytest.fixture
def validator():
    return FieldRelationshipValidator()


@pytest.mark.parametrize("target, related, test_id", RELATIONSHIP_RULES)
def test_related_present_requires_target(target, related, test_id, validator):
    record = {field: "Some Value" for field in related}
    record[target] = None  # Simulate missing target

    errors = validator.validate(record, target, related)

    assert (
        errors
    ), f"{test_id} FAILED: {target} not populated despite related fields present."


# ------------------------------------------------------------------
# Scenario 2:
# Related NULL → Target must be NULL
# ------------------------------------------------------------------


@pytest.mark.parametrize("target, related, test_id", RELATIONSHIP_RULES)
def test_related_null_requires_target_null(target, related, test_id, validator):
    record = {field: None for field in related}
    record[target] = "Improper Value"  # Should not exist

    errors = validator.validate(record, target, related)

    assert errors, f"{test_id} FAILED: {target} populated despite related fields NULL."
