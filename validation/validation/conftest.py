import csv
from pathlib import Path

import pytest


OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def _init_result_store(config: pytest.Config) -> None:
    if not hasattr(config, "_per_file_results"):
        config._per_file_results = {}


def _record_result(item: pytest.Item, report: pytest.TestReport) -> None:
    config = item.config
    _init_result_store(config)

    test_file = Path(str(item.fspath))
    file_key = test_file.name
    file_results = config._per_file_results.setdefault(file_key, [])

    outcome = "pass"
    if report.failed:
        outcome = "fail"
    elif report.skipped:
        outcome = "skip"

    error_text = ""
    if report.failed and report.longreprtext:
        error_text = report.longreprtext.strip()

    file_results.append(
        {
            "test_case_id": item.nodeid,
            "test_case_name": item.name,
            "test_case_result": outcome,
            "test_case_error": error_text,
        }
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        _record_result(item, report)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    _init_result_store(config)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file_name, rows in config._per_file_results.items():
        stem = Path(file_name).stem
        output_path = OUTPUT_DIR / f"{stem}_results.csv"

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
            for row in rows:
                writer.writerow(row)
