import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

supabase: Client = None

if url and key:
    supabase = create_client(url, key)
else:
    print("[WARN] Supabase credentials not found. Database features will be disabled.")

def push_agent1_raw(company_name, agent_name, raw_data):
    """Store raw LLM output in agent1_raw table."""
    if not supabase:
        return
    
    try:
        data = {
            "company_name": company_name,
            "agent_name": agent_name,
            "raw_data": raw_data
        }
        supabase.table("agent1_raw").insert(data).execute()
        print(f"[Supabase] Stored raw data for {agent_name}")
    except Exception as e:
        print(f"[Supabase Error] Failed to store raw data for {agent_name}: {e}")

def push_agent2_raw(company_name, consolidated_data, metrics, validation=None):
    """Store consolidated output in agent2_raw table."""
    if not supabase:
        return
    
    try:
        data = {
            "company_name": company_name,
            "consolidated_data": consolidated_data,
            "metrics": metrics,
            "validation_status": validation.get("status") if validation else "unknown",
            "validation_errors": validation.get("errors") if validation else []
        }
        supabase.table("agent2_raw").insert(data).execute()
        print(f"[Supabase] Stored consolidated data for {company_name}")
    except Exception as e:
        print(f"[Supabase Error] Failed to store consolidated data for {company_name}: {e}")
