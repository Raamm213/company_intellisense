# Skipped Tests and Pytest Output Explained

## 1. What are the 290 skipped tests and why?

Skipped tests come from these places:

| Source | Approx. count | Reason |
|--------|----------------|--------|
| **test_csv_folder_validation.py** | 1 | The whole test is marked `@pytest.mark.skip` because `companies.csv` has known invalid/sample data. Re-enable when the CSV is compliant. |
| **test_id_2_4.py** | ~163 | One test per row in `specs/ID 2.4.csv`. Each run skips with `pytest.skip(...)` when there is **no CSV mapping** for that column (`MAPPING.get(column_name) == ""`) or **no metadata rule** for that column (`RULES.get(column_name) is None`). So any column in the spec that is missing from `metadata_mapping.csv` or `metadata params.csv` causes a skip. |
| **test_id_3_1.py** | 3 | One test per row in `specs/ID 3.1.csv`. Every test **unconditionally** skips with: `pytest.skip(f"{row['Test ID']}: requires external data validation")`. These cases are meant to be run only when external sources (e.g. LinkedIn, SEC) are available. |
| **test_id_3_2.py** | ~123 | One test per row in `specs/ID 3.2.csv`. Same as 3.1: every test **unconditionally** skips with: `pytest.skip(f"{row['Test ID']}: requires external data validation")`. They are freshness/staleness checks that need live APIs or external data. |

**Total:** 1 + ~163 + 3 + ~123 ≈ **290 skipped**.

So the 290 skips are by design: CSV test disabled for bad data, 2.4 skips when spec columns aren’t in mapping/metadata, and 3.1/3.2 are placeholders for future external validation.

---

## 2. What are the "sssssss" in test_id_3_2 (and similar)?

In pytest’s default progress output, **each character is one test**:

- **`.`** = passed  
- **`s`** = skipped  
- **`F`** = failed  
- **`E`** = error  

So when you see:

```text
test_id_3_2.py sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss
```

each **`s`** is one skipped test. test_id_3_2 is parametrized over every row in `ID 3.2.csv` (~123 rows), and each of those tests calls `pytest.skip(...)`, so you get a long line of **`s`**s. Same idea for test_id_2_4 (many **`s`**s) and test_id_3_1 (3 **`s`**s).

---

## 3. Why does the output “grow” (more characters as tests run)?

Pytest prints **one character per test** as it runs. So:

- Early: you see only a few characters (e.g. `...` for the first 3 tests).
- Later: the line gets longer (e.g. `....ssss....`), because more tests have already run and each added one more character.

There is **no `*` in standard pytest output**. If you see something that looks like a “*” or a growing pattern, it might be:

- A different character (e.g. **`.`** or **`s`**) that looks like a star in your font/terminal, or  
- The **percentage** (e.g. `[ 23%]`, `[ 49%]`) increasing as tests complete.

So the “growth” is simply: **more tests run → one more character per test → longer line**. It’s normal.

---

## Optional: reduce or change the output

- **See why each test was skipped:**  
  `pytest -v -rs`  
  (`-rs` = report skipped; `-v` = verbose)

- **Hide progress dots and only see a summary:**  
  `pytest -q`  
  (quiet)

- **List skip reasons for a specific file:**  
  `pytest tests_generated/test_id_3_2.py -v -rs`
