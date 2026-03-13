import asyncio
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from schema import CompanyOverview, CompanyCulture, CompanyFinancials
from llm_config import get_gemini_llm, get_groq_llm, get_cerebras_llm
from rate_limiter import RateLimiter
from judge import run_judge
import json
import os
import subprocess
import time
from json_to_csv_bridge import convert_json_to_csv

template = """
You are a senior corporate intelligence analyst with access to the latest public data.
Your job is to extract FACTUAL, VERIFIABLE, and PRECISE company intelligence.

STRICT RULES:
1. Return ONLY valid JSON. No explanations, no markdown fences, no commentary.
2. Every value MUST be factual and based on publicly available information (annual reports, SEC filings, press releases, official websites, Glassdoor, LinkedIn, etc.).
3. For numeric fields (revenue, employee count, ratings, percentages), provide EXACT numbers with units and time period (e.g., "$394.3 billion (FY2022)", "164,000 employees (Q4 2023)", "4.2/5.0").
4. For text fields, be SPECIFIC and CONCISE — avoid vague phrases like "generally good" or "varies". Give concrete details.
5. For URLs, provide EXACT working URLs — do not guess or fabricate.
6. If a value is genuinely unknown or not publicly available, return null — do NOT hallucinate or make up data.
7. Prefer the MOST RECENT data available. Always mention the date/period when possible.
8. For list-type fields (competitors, investors, leaders), provide at least 3-5 specific names.

Company Name: {company_name}

Follow this schema exactly:
{format_instructions}
"""

# Shared rate limiter: 4s between calls → max 15 RPM (safe for all free tiers)
rate_limiter = RateLimiter(min_interval=4.0)


def create_prompt(pydantic_object):
    parser = PydanticOutputParser(pydantic_object=pydantic_object)
    return PromptTemplate(
        template=template,
        input_variables=["company_name"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    ), parser


async def call_llm_chunk(name, llm, company_name, chunk_name, chunk_model):
    """Call a single LLM for one schema chunk, respecting rate limits."""
    prompt, parser = create_prompt(chunk_model)
    formatted_prompt = prompt.format(company_name=company_name)
    print(f"  [{name}] Extracting {chunk_name}...")
    tokens = 0
    try:
        await rate_limiter.wait()
        response = await llm.ainvoke(formatted_prompt)
        parsed_result = parser.parse(response.content)
        
        # Capture tokens if provided by LangChain metadata
        if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
            usage = response.response_metadata["token_usage"]
            tokens = usage.get("total_tokens", usage.get("total_tokens", 0))
        elif hasattr(response, "usage_metadata"): # Newer LangChain
            tokens = response.usage_metadata.get("total_tokens", 0)
            
        print(f"  [{name}] [OK] {chunk_name} done. ({tokens} tokens)")
        return chunk_name, parsed_result.model_dump(), tokens
    except Exception as e:
        print(f"  [{name}] [FAIL] {chunk_name} failed: {e}")
        return chunk_name, {}, 0


async def call_llm_all_chunks(name, llm, company_name):
    """Call one LLM for all 3 schema chunks, sequentially (rate-limit safe)."""
    chunks = {
        "overview": CompanyOverview,
        "culture": CompanyCulture,
        "financials": CompanyFinancials,
    }

    print(f"\n[SIGNAL] Agent 1 — {name.upper()}")
    combined = {}
    total_tokens = 0
    for chunk_name, chunk_model in chunks.items():
        _, data, tokens = await call_llm_chunk(name, llm, company_name, chunk_name, chunk_model)
        combined.update(data)
        total_tokens += tokens

    return name, combined, total_tokens


async def run_pipeline(company_name):
    """
    Full pipeline...
    """
    start_time = time.time()
    """
    Full pipeline:
      Agent 1 → 3 LLMs (sequentially, rate-limited) → 3 JSON outputs
      Agent 2 → Judge → 1 consolidated JSON with source attribution

    Returns dict structured for future pytest retry loop:
      - agent1_results: raw outputs per LLM
      - consolidated: best-of-breed with source per field
      - judge_metadata: conflict/resolution details
      - metrics: tokens_used, time_taken, parameter_count
    """
    models = {
        "gemini": get_gemini_llm(),
        "groq": get_groq_llm(),
        "cerebras": get_cerebras_llm(),
    }

    print("=" * 60)
    print("[AGENT] AGENT 1 — DATA COLLECTION (3 LLMs)")
    print("=" * 60)

    # Run each model sequentially to respect rate limits on free tiers
    results = {}
    total_tokens = 0
    for name, model in models.items():
        model_name, result, tokens = await call_llm_all_chunks(name, model, company_name)
        results[model_name] = result
        total_tokens += tokens

    # Agent 2: Judge consolidation
    judge_output = await run_judge(company_name, results, rate_limiter)

    # Build consolidated output with per-field source tracking
    consolidated_with_source = {}
    consolidated_data = judge_output.consolidated.model_dump()
    for field, value in consolidated_data.items():
        consolidated_with_source[field] = {
            "value": value,
            "source": judge_output.source_map.get(field, "unknown"),
        }

    # Step 6: Data Validation
    from validator import CompanyValidator
    _v = CompanyValidator()
    validation_results = _v.validate(consolidated_data)

    duration = round(time.time() - start_time, 1) # Calculate duration

    # Build final output
    final_output = {
        "company": company_name,
        "agent1_results": results,
        "consolidated": consolidated_with_source,
        "judge_metadata": {
            "conflict_fields": judge_output.conflict_fields,
            "missing_fields": judge_output.missing_fields,
            "llm_judged_fields": judge_output.llm_judged_fields,
            "llm_filled_fields": judge_output.llm_filled_fields,
        },
        "metrics": {
            "tokens_used": total_tokens,
            "parameter_count": len(consolidated_data),
            "time_taken": duration # Added time_taken to metrics
        },
        "validation": validation_results
    }

    return final_output


from supabase_client import push_agent1_raw, push_agent2_raw

def save_results(company: str, output: dict):
    """Save raw and consolidated results to their respective directories and Supabase."""
    # 1. Store Agent 1 Raw Data to Supabase
    for agent_name, raw_data in output.get("agent1_results", {}).items():
        push_agent1_raw(company, agent_name, raw_data)

    # 2. Store Agent 2 Consolidated Data to Supabase
    push_agent2_raw(company, output.get("consolidated", {}), output.get("metrics", {}), output.get("validation", {}))

    # Save full output locally (includes agent1 raw + consolidated + metadata)
    intel_dir = Path("intel")
    intel_dir.mkdir(exist_ok=True)
    filename = intel_dir / f"{company.lower().replace(' ', '_')}_intel.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)
    print(f"\n[OK] Full results saved to: {os.path.abspath(filename)}")

    # Save consolidated-only output locally (with source per field)
    consolidated = output["consolidated"]
    consolidated_dir = Path("consolidated")
    consolidated_dir.mkdir(exist_ok=True)
    consolidated_filename = consolidated_dir / f"{company.lower().replace(' ', '_')}_consolidated.json"
    with open(consolidated_filename, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=4)
    print(f"[OK] Consolidated output saved to: {os.path.abspath(consolidated_filename)}")
    
    return filename, consolidated_filename


if __name__ == "__main__":
    company = input("Enter company name: ")

    # Run the full pipeline
    output = asyncio.run(run_pipeline(company))

    # Print summary
    print("\n" + "=" * 60)
    print("[REPORT] FINAL CONSOLIDATED OUTPUT")
    print("=" * 60)
    consolidated = output["consolidated"]
    non_null = sum(1 for v in consolidated.values() if v.get("value") is not None)
    total = len(consolidated)
    print(f"  Fields populated: {non_null}/{total}")

    # Source distribution
    source_counts = {}
    for field_data in consolidated.values():
        src = field_data.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
    print("\n  [DATA] Source Distribution:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count} fields")

    # Save results
    filename, consolidated_filename = save_results(company, output)

    # Step 3: Run Validation Suite
    print("\n" + "=" * 60)
    print("[TEST] PHASE 3: AUTOMATED VALIDATION")
    print("=" * 60)
    
    # Define paths
    base_dir = Path(__file__).resolve().parent
    val_dir = base_dir.parent / "validation" / "validation"
    output_csv = val_dir / "csv" / "companies.csv"
    mapping_file = val_dir / "tests_generated" / "metadata_mapping.csv"
    
    # 1. Convert JSON to CSV for validation
    try:
        convert_json_to_csv(consolidated_filename, str(output_csv), str(mapping_file))
        
        # 2. Run Pytest
        print(f"\n[RUN] Running validation tests in {val_dir}...")
        # We run from the validation directory to ensure conftest.py is picked up
        result = subprocess.run(
            ["pytest", "tests_generated"], 
            cwd=str(val_dir),
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"[WARN]  Pytest Errors:\n{result.stderr}")
            
        print(f"\n[OK] Validation complete. Reports saved in: {val_dir / 'output'}")
        
    except Exception as e:
        print(f"[FAIL] Validation failed to run: {e}")
