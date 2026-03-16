from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
from pydantic import BaseModel
from typing import Dict, Any, List
import sys
import os
import json
from pathlib import Path

# Add the current directory to path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_pipeline, save_results

app = FastAPI(
    title="Company Intel API",
    description="AI-powered company intelligence extraction and validation",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for results (simple for now)
results_cache: Dict[str, Any] = {}
search_status: Dict[str, str] = {}  # "pending", "completed", "failed"
search_metrics: Dict[str, Dict[str, Any]] = {}


class SearchRequest(BaseModel):
    company_name: str


@app.post("/api/search")
async def search_company(request: SearchRequest, background_tasks: BackgroundTasks):
    company = request.company_name
    if not company:
        raise HTTPException(status_code=400, detail="Company name is required")

    # Initialize status
    search_status[company] = "pending"
    search_metrics[company] = {"time_taken": 0, "tokens_used": 0, "parameter_count": 0}

    # Run pipeline in background
    background_tasks.add_task(execute_pipeline, company)

    return {"message": "Search initiated", "company": company}


async def execute_pipeline(company: str):
    try:
        import time

        start_time = time.time()
        data = await run_pipeline(company)
        end_time = time.time()

        duration = round(end_time - start_time, 1)

        # Extract metrics from pipeline data
        metrics = data.get("metrics", {})
        search_metrics[company] = {
            "time_taken": duration,
            "tokens_used": metrics.get("tokens_used", 0),
            "parameter_count": metrics.get("parameter_count", 0),
        }

        results_cache[company] = data
        save_results(company, data)

        # Step 7: Run Full Validation Suite (700+ cases)
        print("\n" + "=" * 60)
        print(" [TEST] PHASE 4: COMPREHENSIVE VALIDATION (Pytest)")
        print("=" * 60)

        try:
            from json_to_csv_bridge import convert_json_to_csv
            import subprocess

            comp_slug = company.lower().replace(" ", "_")
            consolidated_filename = (
                Path("consolidated") / f"{comp_slug}_consolidated.json"
            )

            val_dir = Path("validation") / "validation"
            output_csv = val_dir / "csv" / "companies.csv"
            mapping_file = val_dir / "tests_generated" / "metadata_mapping.csv"

            # 1. Convert JSON to CSV for validation
            convert_json_to_csv(
                consolidated_filename, str(output_csv), str(mapping_file)
            )

            # 2. Run Pytest
            print(f"\n[RUN] Running {company} through 700+ validation cases...")
            # We run with -q to get a cleaner dot-based output
            subprocess.run(["pytest", "tests_generated", "-q"], cwd=str(val_dir))
            print(f"\n[OK] Validation suite complete.")

        except Exception as ve:
            print(f"[WARN] Could not run full validation suite: {ve}")

        search_status[company] = "completed"
    except Exception as e:
        print(f"Error in pipeline for {company}: {e}")
        search_status[company] = "failed"


@app.get("/api/status/{company}")
async def get_status(company: str):
    status = search_status.get(company, "not_found")
    metrics = search_metrics.get(company, {})
    return {"status": status, **metrics}


@app.get("/api/results/{company}")
async def get_results(company: str):
    # Check cache first
    if company in results_cache:
        return results_cache[company]

    # Paths
    comp_slug = company.lower().replace(" ", "_")
    intel_path = Path("intel") / f"{comp_slug}_intel.json"
    cons_path = Path("consolidated") / f"{comp_slug}_consolidated.json"

    # 1. Try Intel folder (Full data + Metadata + Metrics)
    if intel_path.exists():
        with open(intel_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            results_cache[company] = data
            return data

    # 2. Try Consolidated folder (Data only)
    if cons_path.exists():
        with open(cons_path, "r", encoding="utf-8") as f:
            cons_data = json.load(f)
            # Wrap in expected structure for frontend
            wrapped_data = {
                "consolidated": cons_data,
                "judge_metadata": {
                    "conflict_fields": [],
                    "llm_judged_fields": [],
                    "llm_filled_fields": [],
                    "missing_fields": [],
                },
                "metrics": {
                    "time_taken": 0,
                    "tokens_used": 0,
                    "parameter_count": len(cons_data),
                },
            }
            results_cache[company] = wrapped_data
            return wrapped_data

    raise HTTPException(status_code=404, detail="Results not found")


@app.get("/api/history")
async def get_history():
    """List all previously searched companies from the consolidated folder ONLY."""
    history = []
    cons_dir = Path("consolidated")

    if cons_dir.exists():
        for file in cons_dir.glob("*_consolidated.json"):
            # Extract company name from filename
            name_raw = file.name.replace("_consolidated.json", "").replace("_", " ")
            name = name_raw.title()

            history.append({"name": name, "timestamp": os.path.getmtime(file)})

    # Sort by recent
    history.sort(key=lambda x: x["timestamp"], reverse=True)
    return history


# Serve static files (HTML/CSS/JS)
static_path = Path(__file__).parent / "static"
if not static_path.exists():
    static_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def read_index():
    return FileResponse(static_path / "index.html")


if __name__ == "__main__":
    import uvicorn

    # Bind to 0.0.0.0 to allow Docker port forwarding,
    # but tell the user to use localhost
    print("\n" + "═" * 60)
    print(" 🚀 COMPANY INTEL SERVER IS LIVE!")
    print(f" 🌐 Access the Dashboard at:  http://localhost:8000")
    print(" " + "═" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
