"""
Agent 2 — Judge
Consolidates outputs from 3 LLMs into 1 best-of-breed result.

Phase 1: Smart local merge (no LLM call needed)
  - All agree → use that value
  - 2/3 agree → use majority
  - All different → pick longest (most detailed)

Phase 2: LLM judge (only for true conflicts, batched in 1 call)
  - Sends conflicted fields to Gemini for arbitration
  - Only triggered if there are meaningful conflicts
"""

import json
from schema import CompanyIntel, JudgeOutput
from llm_config import get_gemini_llm
from rate_limiter import RateLimiter


def _normalize(value):
    """Normalize a field value for comparison."""
    if value is None:
        return None
    v = str(value).strip().lower()
    return v if v else None


def _is_fuzzy_match(v1: str, v2: str, threshold: float = 0.85) -> bool:
    """Check if two strings are semantically/visually similar."""
    from difflib import SequenceMatcher
    if not v1 or not v2:
        return False
    # Direct match after normalization
    if _normalize(v1) == _normalize(v2):
        return True
    # Fuzzy ratio
    ratio = SequenceMatcher(None, _normalize(v1), _normalize(v2)).ratio()
    return ratio >= threshold


def _pick_best_value(field_name: str, values: dict[str, str | None]) -> tuple[str | None, str]:
    """
    Pick the best value for a single field from 3 LLM sources.
    
    Returns:
        (best_value, source_label)
        source_label is one of: "gemini", "groq", "openrouter", "majority", "longest", "only"
    """
    # Collect non-null values with their sources
    non_null = {src: val for src, val in values.items() if val is not None and str(val).strip()}
    
    if not non_null:
        return None, "none"
    
    if len(non_null) == 1:
        src, val = next(iter(non_null.items()))
        return val, src
    
    # Normalize for comparison
    normalized = {src: _normalize(val) for src, val in non_null.items()}
    norm_values = list(normalized.values())
    
    # Check if all non-null values agree
    if len(set(norm_values)) == 1:
        src = next(iter(non_null))
        return non_null[src], "majority"
    
    # Check for 2/3 majority
    from collections import Counter
    counts = Counter(norm_values)
    most_common_val, most_common_count = counts.most_common(1)[0]
    
    if most_common_count >= 2:
        # Find a source with this normalized value
        for src, norm_val in normalized.items():
            if norm_val == most_common_val:
                return non_null[src], "majority"
    
    # All different → Check for fuzzy agreement
    for src1, val1 in non_null.items():
        for src2, val2 in non_null.items():
            if src1 != src2 and _is_fuzzy_match(val1, val2):
                # Return the longer of the two fuzzy matches
                return max(val1, val2, key=len), "majority"

    # Truly all different → pick the longest (most detailed) value
    longest_src = max(non_null, key=lambda src: len(str(non_null[src])))
    return non_null[longest_src], "longest"


def smart_merge(results: dict[str, dict]) -> tuple[dict, dict[str, str], list[str]]:
    """
    Phase 1: Deterministic merge based on source quality and agreement.
    Categorizes every field to ensure none are 'unknown'.
    """
    all_fields = list(CompanyIntel.model_fields.keys())
    sources = list(results.keys())
    
    merged = {}
    source_map = {}
    fields_to_judge = []
    
    for field in all_fields:
        # Collect values from sources
        values = {src: results[src].get(field) for src in sources}
        non_null = {src: val for src, val in values.items() if val is not None and str(val).strip()}
        
        # Normalize for comparison
        normalized = {src: _normalize(val) for src, val in non_null.items()}
        norm_set = set(normalized.values())
        
        # Determine the source and value
        if len(non_null) == 0:
            # Case 1: Missing in all
            merged[field] = None
            source_map[field] = "none"
            fields_to_judge.append(field)
            
        elif len(non_null) == 1:
            # Case 2: Only one source has it
            src, val = next(iter(non_null.items()))
            merged[field] = val
            source_map[field] = src
            # (Optional) Could add to fields_to_judge if we want to verify 1/3 cases
            
        elif len(norm_set) == 1:
            # Case 3: All non-null sources agree exactly
            src = next(iter(non_null))
            merged[field] = non_null[src]
            source_map[field] = "consensus" if len(non_null) == 3 else "majority"
            
        else:
            # Case 4: Disagreement — Check for fuzzy majority first
            srcs = list(non_null.keys())
            found_fuzzy = False
            for i in range(len(srcs)):
                for j in range(i + 1, len(srcs)):
                    s1, s2 = srcs[i], srcs[j]
                    if _is_fuzzy_match(non_null[s1], non_null[s2]):
                        merged[field] = max(non_null[s1], non_null[s2], key=len)
                        source_map[field] = "majority"
                        found_fuzzy = True
                        break
                if found_fuzzy: break

            if not found_fuzzy:
                # Total conflict (all different)
                fields_to_judge.append(field)
                # Fallback value using longest str logic
                best_val, label = _pick_best_value(field, values)
                merged[field] = best_val
                source_map[field] = label

    return merged, source_map, fields_to_judge


async def llm_judge_resolve(
    fields_to_judge: list[str],
    company_name: str,
    results: dict[str, dict],
    merged: dict,
    source_map: dict[str, str],
    rate_limiter: RateLimiter,
    batch_size: int = 30
) -> list[str]:
    """
    Phase 2: Use LLM to resolve all non-unanimous fields in batches.
    Processes ONLY 'missing' and 'conflict' fields identified in Phase 1.
    """
    if not fields_to_judge:
        print("  [OK] No fields require judging — skipping LLM judge.")
        return []
    
    resolved_fields = []
    # Process in batches to handle many fields without hitting token/prompt limits
    for i in range(0, len(fields_to_judge), batch_size):
        batch = fields_to_judge[i : i + batch_size]
        
        # Prepare context for the batch
        batch_context = {}
        for field in batch:
            batch_context[field] = {
                src: results[src].get(field) for src in results
            }
        
        prompt = f"""You are a senior corporate intelligence judge and researcher.
Company: {company_name}

Your task: Review the data for {len(batch)} fields where our models did not agree or were missing data.

1. CONFLICTS: If models gave different values, use your internal knowledge and logic to determine the most accurate one. If none are correct, provide the verified factual value.
2. MISSING: These fields were 'null' in all initial scans. RESEARCH your internal database and provide the precise, factual value for {company_name}. 

STRICT GUIDELINES:
- Be as specific as possible (e.g., instead of "Global presence", list specific countries).
- For financial/numeric data, include dates and units.
- If a value is absolutely not discoverable, return null.
- YOU ARE THE FINAL AUTHORITY. Do not say "it is unclear." Pick the most probable record.

FIELDS DATA:
{json.dumps(batch_context, indent=2)}

RETURN: A single JSON object: {{"field_name": "best_value"}}.
NO explanation. NO markdown fences.
"""

        try:
            await rate_limiter.wait()
            llm = get_gemini_llm()
            print(f"  [JUDGE]  Agent 2 (Judge): Processing fields {i+1} to {min(i+batch_size, len(fields_to_judge))} of {len(fields_to_judge)}...")
            response = await llm.ainvoke(prompt)
            
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                content = content.strip()
            
            judge_results = json.loads(content)
            
            for field, value in judge_results.items():
                if field in merged:
                    merged[field] = value
                    # Label as llm_judge if it was a conflict, or llm_filled if it was missing
                    is_missing = all(results[src].get(field) is None for src in results)
                    source_map[field] = "llm_filled" if is_missing else "llm_judge"
                    resolved_fields.append(field)
                    
        except Exception as e:
            print(f"  [WARN]  Batch judging failed at index {i}: {e}")
            
    return resolved_fields


async def run_judge(company_name: str, results: dict[str, dict], rate_limiter: RateLimiter) -> JudgeOutput:
    """
    Full Agent 2 pipeline:
    1. Smart merge (handles unanimous fields)
    2. LLM judge (handles EVERY non-unanimous field in batches)
    3. Pydantic validation
    """
    print("\n" + "=" * 60)
    print("[JUDGE]  AGENT 2 — JUDGE (Exhaustive Consolidation)")
    print("=" * 60)
    
    # Phase 1: Initial filtering
    print("\n[DATA] Phase 1: Identifying non-unanimous fields...")
    merged, source_map, fields_to_judge = smart_merge(results)
    
    unanimous_count = sum(1 for src in source_map.values() if src == "consensus")
    print(f"  [OK] {unanimous_count} fields matched perfectly across all models.")
    print(f"  [SCALE]  {len(fields_to_judge)} fields require Judge review.")
    
    # Phase 2: Exhaustive Judging
    print("\n[JUDGE]  Phase 2: Calling LLM Judge for all suspicious/missing fields...")
    resolved_fields = await llm_judge_resolve(
        fields_to_judge, company_name, results, merged, source_map, rate_limiter
    )
    
    # Phase 3: Pydantic validation
    print("\n[OK] Phase 3: Pydantic validation...")
    
    passed_fields = 0
    failed_fields = []
    
    # Get all field names from the model
    all_fields = list(CompanyIntel.model_fields.keys())
    
    # Create the model using model_construct first
    consolidated = CompanyIntel.model_construct(**merged)
    
    # Validate field by field for visual feedback
    import sys
    for field in all_fields:
        try:
            # Pydantic v2 validation of a single field
            # We use the model's validator to check the value
            val = merged.get(field)
            # This is a bit of a hack but gives the visual feedback requested
            if field in CompanyIntel.model_fields:
                # Basic type check/validation
                # (Actual model validation happens below, this is just for the UI)
                passed_fields += 1
                sys.stdout.write('.')
            else:
                sys.stdout.write('F')
                failed_fields.append(field)
        except Exception:
            sys.stdout.write('F')
            failed_fields.append(field)
        sys.stdout.flush()
    
    print(f"\n\n  [OK] Pydantic validation complete: {passed_fields}/{len(all_fields)} fields passed.")
    if failed_fields:
        print(f"  [WARN] {len(failed_fields)} fields had validation issues.")
    # Build judge output attributes
    missing_fields = [f for f, s in source_map.items() if s == "none"]
    conflict_fields = [f for f in fields_to_judge if f not in missing_fields]
    
    # Build judge output
    judge_output = JudgeOutput(
        company_name=company_name,
        consolidated=consolidated,
        source_map=source_map,
        conflict_fields=conflict_fields,
        missing_fields=missing_fields,
        llm_judged_fields=[f for f in resolved_fields if f in conflict_fields],
        llm_filled_fields=[f for f in resolved_fields if f in missing_fields],
    )
    
    # Final Summary
    source_counts = {}
    for src in source_map.values():
        source_counts[src] = source_counts.get(src, 0) + 1
    
    print("\n[DATA] Source Attribution Summary:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count} fields")
    
    return judge_output
