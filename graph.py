import asyncio
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from judge import run_judge
from llm_config import get_cerebras_llm, get_gemini_llm, get_groq_llm
from main import call_llm_all_chunks, rate_limiter


# 1. Define the State
class AgentState(TypedDict):
    company_name: str
    max_retries: int
    retry_count: int

    # Intermediate raw results for visibility in Studio
    gemini_raw: Optional[Dict[str, Any]]
    groq_raw: Optional[Dict[str, Any]]
    cerebras_raw: Optional[Dict[str, Any]]

    # Aggregated results for consolidation
    raw_results: Annotated[Dict[str, Any], operator.ior]

    final_output: Optional[Dict[str, Any]]
    validation_errors: List[str]


# 2. Define the Nodes


async def start_node(state: AgentState):
    """Entry point to ensure clean parallel visualization and retry routing."""
    return {"retry_count": state.get("retry_count", 0)}


async def extract_gemini(state: AgentState):
    """Extract raw data using Gemini."""
    llm = get_gemini_llm()
    _, result = await call_llm_all_chunks("gemini", llm, state["company_name"])
    return {"gemini_raw": result, "raw_results": {"gemini": result}}


async def extract_groq(state: AgentState):
    """Extract raw data using Groq."""
    llm = get_groq_llm()
    _, result = await call_llm_all_chunks("groq", llm, state["company_name"])
    return {"groq_raw": result, "raw_results": {"groq": result}}


async def extract_cerebras(state: AgentState):
    """Extract raw data using Cerebras."""
    llm = get_cerebras_llm()
    _, result = await call_llm_all_chunks("cerebras", llm, state["company_name"])
    return {"cerebras_raw": result, "raw_results": {"cerebras": result}}


async def local_merge_node(state: AgentState):
    """
    Phase 1: Deterministic merge based on consensus and majority.
    No LLM call here, just logic.
    """
    from judge import smart_merge

    results = state["raw_results"]
    merged, source_map, fields_to_judge = smart_merge(results)

    # Store intermediate state for the judge node
    return {
        "final_output": {
            "consolidated": merged,
            "source_map": source_map,
            "fields_to_judge": fields_to_judge,
        }
    }


async def gemini_judge_node(state: AgentState):
    """
    Phase 2: Use Gemini to arbitrate conflicts and fill missing data.
    This fulfills the 'gemini for specific parameters' requirement.
    """
    from judge import CompanyIntel, JudgeOutput, llm_judge_resolve
    from main import rate_limiter

    data = state["final_output"]
    merged = data["consolidated"]
    source_map = data["source_map"]
    fields_to_judge = data["fields_to_judge"]

    # Call Gemini to research/arbitrate
    resolved_fields = await llm_judge_resolve(
        fields_to_judge,
        state["company_name"],
        state["raw_results"],
        merged,
        source_map,
        rate_limiter,
    )

    # Final Pydantic construction
    try:
        consolidated_model = CompanyIntel(**merged)
    except Exception:
        consolidated_model = CompanyIntel.model_construct(**merged)

    # Rebuild final output structure
    consolidated_with_source = {}
    for field, value in consolidated_model.model_dump().items():
        consolidated_with_source[field] = {
            "value": value,
            "source": source_map.get(field, "unknown"),
        }

    final_output = {
        "company": state["company_name"],
        "agent1_results": state["raw_results"],
        "consolidated": consolidated_with_source,
        "judge_metadata": {
            "conflict_fields": [
                f for f in fields_to_judge if source_map.get(f) != "none"
            ],
            "missing_fields": [
                f for f in fields_to_judge if source_map.get(f) == "none"
            ],
            "llm_judged_fields": [
                f
                for f in resolved_fields
                if f in fields_to_judge and source_map.get(f) != "none"
            ],
            "llm_filled_fields": [
                f
                for f in resolved_fields
                if f in fields_to_judge and source_map.get(f) == "none"
            ],
        },
    }

    return {"final_output": final_output}


async def validate_node(state: AgentState):
    """Check for essential field coverage."""
    output = state["final_output"]
    consolidated = output["consolidated"]
    errors = []

    essentials = ["name", "industry", "headquarters_address", "annual_revenue"]
    for field in essentials:
        field_data = consolidated.get(field, {})
        if field_data.get("source") == "none" or field_data.get("value") is None:
            errors.append(f"Missing essential field: {field}")

    return {"validation_errors": errors}


def should_retry(state: AgentState):
    """Decide whether to loop back to start or finish."""
    if not state["validation_errors"]:
        return END

    if state["retry_count"] < state["max_retries"]:
        return "retry"

    return END


# 3. Build the Graph
builder = StateGraph(AgentState)

builder.add_node("start", start_node)
builder.add_node("extract_gemini", extract_gemini)
builder.add_node("extract_groq", extract_groq)
builder.add_node("extract_cerebras", extract_cerebras)
builder.add_node("local_merge", local_merge_node)
builder.add_node("gemini_judge", gemini_judge_node)
builder.add_node("validate", validate_node)

# Flow
builder.add_edge(START, "start")
builder.add_edge("start", "extract_gemini")
builder.add_edge("start", "extract_groq")
builder.add_edge("start", "extract_cerebras")

builder.add_edge("extract_gemini", "local_merge")
builder.add_edge("extract_groq", "local_merge")
builder.add_edge("extract_cerebras", "local_merge")

builder.add_edge("local_merge", "gemini_judge")
builder.add_edge("gemini_judge", "validate")

# Conditional Retry Loop
builder.add_conditional_edges("validate", should_retry, {"retry": "start", END: END})

# Export the compiled graph for Studio
graph = builder.compile()
