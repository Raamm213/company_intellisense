import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class CompanyValidator:
    def __init__(self, metadata_path: str = None):
        base_dir = Path(__file__).resolve().parent
        if metadata_path is None:
            metadata_path = (
                base_dir / "validation" / "validation" / "metadata params.csv"
            )

        # Fallback for Docker
        if not metadata_path.exists():
            metadata_path = Path("/app/validation/validation/metadata params.csv")

        self.metadata_path = metadata_path
        self.rules = {}
        self.mapping = {}

        # Try to load mapping first
        mapping_path = (
            base_dir
            / "validation"
            / "validation"
            / "tests_generated"
            / "metadata_mapping.csv"
        )
        if not mapping_path.exists():
            mapping_path = Path(
                "/app/validation/validation/tests_generated/metadata_mapping.csv"
            )

        if mapping_path.exists():
            try:
                map_df = pd.read_csv(mapping_path)
                # Map column_name -> csv_header
                self.mapping = dict(zip(map_df["column_name"], map_df["csv_header"]))
            except Exception as e:
                print(f"[Validator Warning] Failed to load mapping: {e}")

        self.load_rules()

    def load_rules(self):
        """Load validation rules from the metadata CSV."""
        if not os.path.exists(self.metadata_path):
            print(
                f"[Validator Warning] Metadata file not found at {self.metadata_path}"
            )
            return

        try:
            df = pd.read_csv(self.metadata_path)
            for _, row in df.iterrows():
                col_name = str(row["column_name"]).strip()
                self.rules[col_name] = {
                    "regex": (
                        str(row["regex_pattern"])
                        if pd.notna(row["regex_pattern"])
                        else None
                    ),
                    "nullability": str(row["nullability"]).strip().lower(),
                    "min_len": (
                        row["minimum_element"]
                        if pd.notna(row["minimum_element"])
                        else None
                    ),
                    "max_len": (
                        row["maximum_element"]
                        if pd.notna(row["maximum_element"])
                        else None
                    ),
                    "category": row["category"],
                }
            print(
                f"[Validator] Loaded {len(self.rules)} rules from {self.metadata_path}"
            )
        except Exception as e:
            print(f"[Validator Error] Failed to load rules: {e}")

    def _flatten_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested dictionary into a single level."""
        flat = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # If it's a nested dict (like overview/culture), merge it
                flat.update(self._flatten_data(value))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # If it's a list of dicts (like key_leaders), we keep it as is for now
                # or we could try to serialize it. Business rules usually check strings.
                flat[key] = str(value)
            else:
                flat[key] = value
        return flat

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the provided data dictionary against the loaded rules.
        """
        if not self.rules:
            return {"status": "unchanged", "errors": ["Validator rules not loaded."]}

        errors = []
        import sys

        # Flatten the incoming nested data (CompanyIntel structure)
        flat_data = self._flatten_data(data)

        print(f"\n[Validator] Running {len(self.rules)} business rules...")

        for field_rule_name, rule in self.rules.items():
            # Get the actual JSON key from the mapping
            json_key = self.mapping.get(field_rule_name)

            # Fetch value using the mapped key, if missing try field_rule_name directly
            if json_key:
                value = flat_data.get(str(json_key))
            else:
                value = flat_data.get(field_rule_name)

            rule_failed = False

            # 1. Nullability Check
            is_empty = value is None or (isinstance(value, str) and not value.strip())
            if rule["nullability"] == "not null" and is_empty:
                errors.append(f"Field '{field_rule_name}' is required but missing.")
                rule_failed = True

            if not rule_failed and not is_empty:
                # 2. Regex Check
                reg_pattern = rule.get("regex")
                if (
                    reg_pattern
                    and isinstance(reg_pattern, str)
                    and reg_pattern != "None"
                    and reg_pattern.strip()
                ):
                    try:
                        pattern = reg_pattern.strip()
                        if pattern.startswith("`") and pattern.endswith("`"):
                            pattern = pattern[1:-1]

                        # Use search to handle patterns that might be intended as prefixes
                        # like "^(19|20)" in the spreadsheet.
                        if not re.search(pattern, str(value).strip()):
                            errors.append(
                                f"Field '{field_rule_name}' format mismatch ({value})."
                            )
                            rule_failed = True
                    except Exception:
                        pass

                # 3. Length Checks
                if not rule_failed:
                    val_str = str(value)
                    try:
                        min_l = rule.get("min_len")
                        max_l = rule.get("max_len")

                        if min_l is not None and min_l != "None":
                            if len(val_str) < int(float(str(min_l))):
                                errors.append(
                                    f"Field '{field_rule_name}' is too short."
                                )
                                rule_failed = True

                        if not rule_failed and max_l is not None and max_l != "None":
                            if len(val_str) > int(float(str(max_l))):
                                errors.append(f"Field '{field_rule_name}' is too long.")
                                rule_failed = True
                    except (ValueError, TypeError):
                        pass

            # Visual Feedback
            if rule_failed:
                sys.stdout.write("F")
            else:
                sys.stdout.write(".")
            sys.stdout.flush()

        status = "pass" if not errors else "fail"
        print(f"\n\n[Validator] Rules check complete. Status: {status.upper()}")

        return {
            "status": status,
            "errors": errors,
            "error_count": len(errors),
            "total_rules": len(self.rules),
        }


# Test Usage
if __name__ == "__main__":
    v = CompanyValidator()
    # Simple test data matching CompanyIntel structure
    test_data = {
        "overview": {"name": "Apple", "category": "Enterprise"},
        "financials": {"annual_revenue": "$394B"},
    }
    print(v.validate(test_data))
