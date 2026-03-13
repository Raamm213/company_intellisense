import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parents[1]
SPECS_DIR = BASE_DIR / "specs"
CSV_DIR = BASE_DIR / "csv"
OUTPUT_DIR = BASE_DIR / "output"
METADATA_PATH = BASE_DIR / "metadata params.csv"
MAPPING_PATH = Path(__file__).resolve().parent / "metadata_mapping.csv"
COMPANIES_PATH = CSV_DIR / "companies.csv"


EMPTY_TOKENS = {
    "",
    "null",
    "none",
    "na",
    "n/a",
    "not applicable",
    "not available",
}


@dataclass
class FieldRule:
    rule_id: Optional[str]
    column_name: str
    regex_pattern: str
    nullability: str
    minimum_element: Optional[int]
    maximum_element: Optional[int]


@dataclass
class ValidationResult:
    status: str
    errors: List[str]


def _normalize_empty(value: Optional[str]) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_TOKENS
    return False


def _sanitize_regex(pattern: str) -> str:
    if pattern is None:
        return ""
    cleaned = pattern.strip()
    if cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("\"") and cleaned.endswith("\""):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _safe_compile(pattern: str) -> Optional[re.Pattern]:
    cleaned = _sanitize_regex(pattern)
    if not cleaned:
        return None
    try:
        return re.compile(cleaned)
    except re.error:
        return None


def load_metadata() -> Dict[str, FieldRule]:
    rules: Dict[str, FieldRule] = {}
    with METADATA_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            column_name = row.get("column_name", "").strip()
            if not column_name:
                continue
            min_val = _to_int(row.get("minimum_element"))
            max_val = _to_int(row.get("maximum_element"))
            rules[column_name] = FieldRule(
                rule_id=(row.get("sr_no") or "").strip() or None,
                column_name=column_name,
                regex_pattern=row.get("regex_pattern", ""),
                nullability=(row.get("nullability", "") or "").strip(),
                minimum_element=min_val,
                maximum_element=max_val,
            )
    return rules


def _to_int(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def load_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with MAPPING_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            column_name = (row.get("column_name") or "").strip()
            csv_header = (row.get("csv_header") or "").strip()
            if column_name:
                mapping[column_name] = csv_header
    return mapping


def load_companies() -> List[Dict[str, str]]:
    with COMPANIES_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _normalize_spec_row(row: Dict[str, str]) -> Dict[str, str]:
    """Strip BOM from keys (e.g. '\\ufeffcolumn_name' -> 'column_name')."""
    return {k.lstrip("\ufeff"): v for k, v in row.items()}


def load_spec_rows(spec_filename: str) -> List[Dict[str, str]]:
    spec_path = SPECS_DIR / spec_filename
    with spec_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            row = _normalize_spec_row(row)
            test_id = (row.get("Test ID") or "").strip()
            if not test_id:
                continue
            rows.append(row)
        return rows


def list_csv_files() -> List[Path]:
    if not CSV_DIR.exists():
        return []
    return sorted(
        path for path in CSV_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".csv"
    )


def load_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def iter_csv_rows() -> Iterable[Tuple[str, Dict[str, str]]]:
    for csv_path in list_csv_files():
        rows = load_csv_rows(csv_path)
        for index, row in enumerate(rows, start=1):
            source_id = f"{csv_path.name}#row{index}"
            yield source_id, row


def build_csv_validation_report(output_filename: str = "csv_validation_results.csv") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename
    rules = load_metadata()
    mapping = load_mapping()

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "test_case_id",
                "test_case_name",
                "test_case_result",
                "test_case_error",
            ],
        )
        writer.writeheader()

        for source_id, record in iter_csv_rows():
            for column_name, rule in rules.items():
                csv_header = mapping.get(column_name, "")
                if not csv_header:
                    continue
                value = record.get(csv_header)
                errors = validate_field_value(column_name, value, rule)
                result = "pass" if not errors else "fail"
                error_text = ""
                if errors:
                    error_text = f"{source_id}: " + "; ".join(errors)

                writer.writerow(
                    {
                        "test_case_id": rule.rule_id or column_name,
                        "test_case_name": column_name,
                        "test_case_result": result,
                        "test_case_error": error_text,
                    }
                )

    return output_path


def get_company_by_name(companies: List[Dict[str, str]], name: str) -> Optional[Dict[str, str]]:
    target = name.strip().lower()
    for row in companies:
        candidate = (row.get("name") or "").strip().lower()
        if candidate == target:
            return row
    return None


def get_value(record: Dict[str, str], column_name: str, mapping: Dict[str, str]) -> Optional[str]:
    csv_header = mapping.get(column_name, "")
    if not csv_header:
        return None
    return record.get(csv_header)


# Company Name business rules (ID 1.5 / 1.4): official list and legal suffixes when strict_company_name=True.
_OFFICIAL_COMPANY_NAMES = frozenset({
    "Microsoft Corporation", "Apple Inc.", "Google LLC", "Tesla, Inc.",
})
_LEGAL_SUFFIXES = ("Inc.", "Ltd.", "Corp.", "LLC", "Corporation")


def _validate_company_name_business_rules(value: str) -> List[str]:
    """Return business-rule errors for Company Name (min words, official list, legal suffix)."""
    errors: List[str] = []
    stripped = value.strip()
    words = stripped.split()
    if len(words) < 2:
        errors.append("Below minimum legal identity completeness")
    if stripped not in _OFFICIAL_COMPANY_NAMES:
        errors.append("Must match official government registration documents")
    if not any(stripped.endswith(s) for s in _LEGAL_SUFFIXES):
        errors.append("Missing legal suffix (Inc., Ltd., Corp.)")
    return errors


def validate_field_value(
    column_name: str,
    value: Optional[str],
    rule: FieldRule,
    *,
    strict_company_name: bool = False,
) -> List[str]:
    errors: List[str] = []
    if rule.nullability.lower() == "not null" and _normalize_empty(value):
        errors.append(f"{column_name} is required but missing")
        return errors

    if _normalize_empty(value):
        return errors

    regex = _safe_compile(rule.regex_pattern)
    if regex is not None:
        if not regex.fullmatch(str(value).strip()):
            errors.append(f"{column_name} does not match regex {rule.regex_pattern}")

    if rule.minimum_element is not None:
        if len(str(value)) < rule.minimum_element:
            errors.append(f"{column_name} length below minimum {rule.minimum_element}")

    if rule.maximum_element is not None:
        if len(str(value)) > rule.maximum_element:
            errors.append(f"{column_name} length above maximum {rule.maximum_element}")

    if strict_company_name and column_name == "Company Name" and value and str(value).strip():
        errors.extend(_validate_company_name_business_rules(str(value).strip()))

    return errors


def validate_record_nullability(
    record: Dict[str, str],
    rules: Dict[str, FieldRule],
    mapping: Dict[str, str],
) -> List[str]:
    errors: List[str] = []
    for column_name, rule in rules.items():
        csv_header = mapping.get(column_name, "")
        if not csv_header:
            continue
        value = record.get(csv_header)
        errors.extend(validate_field_value(column_name, value, rule))
    return errors


def evaluate_profile_completeness(
    record: Dict[str, str],
    rules: Dict[str, FieldRule],
    mapping: Dict[str, str],
    optional_threshold: float,
    warn_threshold: Optional[float] = None,
) -> ValidationResult:
    mandatory_errors = validate_record_nullability(record, rules, mapping)
    optional_total = 0
    optional_filled = 0

    for column_name, rule in rules.items():
        csv_header = mapping.get(column_name, "")
        if not csv_header:
            continue
        if rule.nullability.lower() == "not null":
            continue
        optional_total += 1
        if not _normalize_empty(record.get(csv_header)):
            optional_filled += 1

    optional_ratio = 1.0 if optional_total == 0 else optional_filled / optional_total

    if mandatory_errors:
        return ValidationResult(status="fail", errors=mandatory_errors)

    if warn_threshold is not None and optional_ratio < warn_threshold:
        return ValidationResult(
            status="warn",
            errors=[f"Optional coverage {optional_ratio:.2f} below warn threshold {warn_threshold:.2f}"],
        )

    if optional_ratio < optional_threshold:
        return ValidationResult(
            status="fail",
            errors=[f"Optional coverage {optional_ratio:.2f} below threshold {optional_threshold:.2f}"],
        )

    return ValidationResult(status="pass", errors=[])


def validate_dependency(
    record: Dict[str, str],
    dependent_column: str,
    related_columns: Iterable[str],
    mapping: Dict[str, str],
) -> List[str]:
    errors: List[str] = []
    dependent_value = get_value(record, dependent_column, mapping)

    related_values = []
    for related in related_columns:
        related_values.append(get_value(record, related, mapping))

    related_present = any(not _normalize_empty(value) for value in related_values)
    dependent_present = not _normalize_empty(dependent_value)

    if related_present and not dependent_present:
        errors.append(
            f"{dependent_column} missing while related fields are present: {', '.join(related_columns)}"
        )
    if not related_present and dependent_present:
        errors.append(
            f"{dependent_column} present while related fields are empty: {', '.join(related_columns)}"
        )

    return errors


def parse_expected_outcome(expected_text: str) -> str:
    lowered = expected_text.lower()
    if "fail" in lowered or "reject" in lowered:
        return "fail"
    if "warn" in lowered:
        return "warn"
    return "pass"


def parse_related_fields(raw: str) -> List[str]:
    cleaned = raw.replace("'", "")
    parts = [part.strip() for part in re.split(r"\||,", cleaned) if part.strip()]
    return parts


def matches_known_name(value: str, known_names: Iterable[str]) -> bool:
    value_clean = value.strip().lower()
    for name in known_names:
        if value_clean == name.strip().lower():
            return True
    return False


def extract_input_value(row: Dict[str, str]) -> str:
    keys = [
        "Input Data (Valid Examples Based on Regex & Format Constraints)",
        "Input Data (Regex-Aligned Example)",
        "Input Data (Malformed Example)",
        "Input Data (Case Variations)",
        "Input Data",
        "Input Data (if applicable)",
    ]
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""
