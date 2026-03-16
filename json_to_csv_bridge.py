import csv
import json
import os
from pathlib import Path


def convert_json_to_csv(json_path: str, output_csv_path: str, mapping_path: str):
    """
    Converts the consolidated company intel JSON into a single-row CSV
    based on the metadata_mapping.csv rules.
    """
    print(f"Bridge: Converting {json_path} to {output_csv_path}...")

    # 1. Load the JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The consolidated data might be under the "consolidated" key,
    # or at the root level depending on which file we load.
    if "consolidated" in data:
        consolidated = data["consolidated"]
    elif "agent1_results" in data:
        # This is the full _intel.json structure
        consolidated = data.get("consolidated", {})
    else:
        # This is the _consolidated.json structure (fields at root)
        consolidated = data

    # 2. Load the mapping to determine CSV headers
    # Mapping format: column_name,csv_header
    # csv_header in mapping matches the keys in our JSON
    mapping = []
    with open(mapping_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["csv_header"]:
                mapping.append(row)

    # 3. Build the CSV row
    # The validation suite expects CSV headers to match 'csv_header' from mapping?
    # No, validation_utils.py load_mapping() says:
    # column_name = mapping['column_name'], csv_header = mapping['csv_header']
    # And then it looks for 'csv_header' in the intelligence CSV.

    headers = [m["csv_header"] for m in mapping]
    row_data = {}
    for m in mapping:
        field_key = m["csv_header"]
        # Extract value from JSON: consolidated[field_key]['value']
        field_info = consolidated.get(field_key, {})
        row_data[field_key] = field_info.get("value")

    # 4. Write to CSV
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row_data)

    print(f"Bridge: Created {output_csv_path}")


if __name__ == "__main__":
    # Example usage (can be called with arguments if needed)
    import sys

    if len(sys.argv) > 1:
        company_name = sys.argv[1].lower().replace(" ", "_")
        base_dir = Path(__file__).resolve().parent
        json_file = base_dir / f"{company_name}_consolidated.json"

        # Validation directory is one level up
        val_dir = base_dir.parent / "validation" / "validation"
        output_csv = (
            val_dir / "csv" / "companies.csv"
        )  # The default name used by validation_utils.py
        mapping_file = val_dir / "tests_generated" / "metadata_mapping.csv"

        if json_file.exists():
            convert_json_to_csv(str(json_file), str(output_csv), str(mapping_file))
        else:
            print(f"❌ Bridge: JSON file not found: {json_file}")
