from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Union

class CompanyOverview(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        """Handle cases where LLMs return a list or number instead of a string."""
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    name: str
    short_name: Optional[str] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None
    industry: Optional[str] = None
    incorporation_year: Optional[str] = None
    overview_text: Optional[str] = None
    nature_of_company: Optional[str] = None
    headquarters_address: Optional[str] = None
    operating_countries: Optional[str] = None
    office_count: Optional[str] = None
    office_locations: Optional[str] = None
    vision_statement: Optional[str] = None
    mission_statement: Optional[str] = None
    core_values: Optional[str] = None
    history_timeline: Optional[str] = None
    recent_news: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_phone_number: Optional[str] = None
    marketing_video_url: Optional[str] = None
    customer_testimonials: Optional[str] = None
    website_quality: Optional[str] = None
    website_rating: Optional[str] = None
    website_traffic_rank: Optional[str] = None
    social_media_followers: Optional[str] = None
    awards_recognitions: Optional[str] = None
    brand_sentiment_score: Optional[str] = None
    event_participation: Optional[str] = None
    pain_points_addressed: Optional[str] = None
    focus_sectors: Optional[str] = None
    offerings_description: Optional[str] = None
    top_customers: Optional[str] = None
    core_value_proposition: Optional[str] = None
    unique_differentiators: Optional[str] = None
    competitive_advantages: Optional[str] = None
    weaknesses_gaps: Optional[str] = None
    key_challenges_needs: Optional[str] = None
    key_competitors: Optional[str] = None
    market_share_percentage: Optional[str] = None
    sales_motion: Optional[str] = None
    benchmark_vs_peers: Optional[str] = None
    future_projections: Optional[str] = None
    strategic_priorities: Optional[str] = None
    industry_associations: Optional[str] = None
    case_studies: Optional[str] = None
    go_to_market_strategy: Optional[str] = None
    innovation_roadmap: Optional[str] = None
    product_pipeline: Optional[str] = None
    tam: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None

class CompanyCulture(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        """Handle cases where LLMs return a list or number instead of a string."""
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    employee_size: Optional[str] = None
    glassdoor_rating: Optional[str] = None
    indeed_rating: Optional[str] = None
    google_rating: Optional[str] = None
    leave_policy: Optional[str] = None
    health_support: Optional[str] = None
    fixed_vs_variable_pay: Optional[str] = None
    bonus_predictability: Optional[str] = None
    esops_incentives: Optional[str] = None
    family_health_insurance: Optional[str] = None
    relocation_support: Optional[str] = None
    lifestyle_benefits: Optional[str] = None
    hiring_velocity: Optional[str] = None
    employee_turnover: Optional[str] = None
    avg_retention_tenure: Optional[str] = None
    diversity_metrics: Optional[str] = None
    work_culture_summary: Optional[str] = None
    manager_quality: Optional[str] = None
    psychological_safety: Optional[str] = None
    feedback_culture: Optional[str] = None
    diversity_inclusion_score: Optional[str] = None
    ethical_standards: Optional[str] = None
    burnout_risk: Optional[str] = None
    layoff_history: Optional[str] = None
    mission_clarity: Optional[str] = None
    sustainability_csr: Optional[str] = None
    crisis_behavior: Optional[str] = None
    remote_policy_details: Optional[str] = None
    typical_hours: Optional[str] = None
    overtime_expectations: Optional[str] = None
    weekend_work: Optional[str] = None
    flexibility_level: Optional[str] = None
    location_centrality: Optional[str] = None
    public_transport_access: Optional[str] = None
    cab_policy: Optional[str] = None
    airport_commute_time: Optional[str] = None
    office_zone_type: Optional[str] = None
    area_safety: Optional[str] = None
    safety_policies: Optional[str] = None
    infrastructure_safety: Optional[str] = None
    emergency_preparedness: Optional[str] = None
    training_spend: Optional[str] = None
    onboarding_quality: Optional[str] = None
    learning_culture: Optional[str] = None
    exposure_quality: Optional[str] = None
    mentorship_availability: Optional[str] = None
    internal_mobility: Optional[str] = None
    promotion_clarity: Optional[str] = None
    tools_access: Optional[str] = None
    role_clarity: Optional[str] = None
    early_ownership: Optional[str] = None
    work_impact: Optional[str] = None
    execution_thinking_balance: Optional[str] = None
    automation_level: Optional[str] = None
    cross_functional_exposure: Optional[str] = None
    exit_opportunities: Optional[str] = None
    skill_relevance: Optional[str] = None
    external_recognition: Optional[str] = None
    network_strength: Optional[str] = None
    global_exposure: Optional[str] = None

class CompanyFinancials(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        """Handle cases where LLMs return a list or number instead of a string."""
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    annual_revenue: Optional[str] = None
    annual_profit: Optional[str] = None
    revenue_mix: Optional[str] = None
    valuation: Optional[str] = None
    yoy_growth_rate: Optional[str] = None
    profitability_status: Optional[str] = None
    key_investors: Optional[str] = None
    recent_funding_rounds: Optional[str] = None
    total_capital_raised: Optional[str] = None
    customer_acquisition_cost: Optional[str] = None
    customer_lifetime_value: Optional[str] = None
    cac_ltv_ratio: Optional[str] = None
    churn_rate: Optional[str] = None
    net_promoter_score: Optional[str] = None
    burn_rate: Optional[str] = None
    runway_months: Optional[str] = None
    burn_multiplier: Optional[str] = None
    regulatory_status: Optional[str] = None
    legal_issues: Optional[str] = None
    esg_ratings: Optional[str] = None
    supply_chain_dependencies: Optional[str] = None
    geopolitical_risks: Optional[str] = None
    macro_risks: Optional[str] = None
    carbon_footprint: Optional[str] = None
    ethical_sourcing: Optional[str] = None
    customer_concentration_risk: Optional[str] = None
    exit_strategy_history: Optional[str] = None
    ceo_name: Optional[str] = None
    ceo_linkedin_url: Optional[str] = None
    key_leaders: Optional[str] = None
    warm_intro_pathways: Optional[str] = None
    decision_maker_access: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    board_members: Optional[str] = None
    company_maturity: Optional[str] = None
    brand_value: Optional[str] = None
    client_quality: Optional[str] = None
    technology_partners: Optional[str] = None
    intellectual_property: Optional[str] = None
    r_and_d_investment: Optional[str] = None
    ai_ml_adoption_level: Optional[str] = None
    tech_stack: Optional[str] = None
    cybersecurity_posture: Optional[str] = None
    partnership_ecosystem: Optional[str] = None
    tech_adoption_rating: Optional[str] = None

# ─── Combined Flat Model (all 163 fields from Overview + Culture + Financials) ───

class CompanyIntel(BaseModel):
    """Single consolidated Pydantic model with ALL company intelligence fields."""
    
    @field_validator("*", mode="before")
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        """Handle cases where LLMs (like Cerebras) return a list or number instead of a string."""
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    # --- Overview fields ---
    name: str
    short_name: Optional[str] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None
    industry: Optional[str] = None
    incorporation_year: Optional[str] = None
    overview_text: Optional[str] = None
    nature_of_company: Optional[str] = None
    headquarters_address: Optional[str] = None
    operating_countries: Optional[str] = None
    office_count: Optional[str] = None
    office_locations: Optional[str] = None
    vision_statement: Optional[str] = None
    mission_statement: Optional[str] = None
    core_values: Optional[str] = None
    history_timeline: Optional[str] = None
    recent_news: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_phone_number: Optional[str] = None
    marketing_video_url: Optional[str] = None
    customer_testimonials: Optional[str] = None
    website_quality: Optional[str] = None
    website_rating: Optional[str] = None
    website_traffic_rank: Optional[str] = None
    social_media_followers: Optional[str] = None
    awards_recognitions: Optional[str] = None
    brand_sentiment_score: Optional[str] = None
    event_participation: Optional[str] = None
    pain_points_addressed: Optional[str] = None
    focus_sectors: Optional[str] = None
    offerings_description: Optional[str] = None
    top_customers: Optional[str] = None
    core_value_proposition: Optional[str] = None
    unique_differentiators: Optional[str] = None
    competitive_advantages: Optional[str] = None
    weaknesses_gaps: Optional[str] = None
    key_challenges_needs: Optional[str] = None
    key_competitors: Optional[str] = None
    market_share_percentage: Optional[str] = None
    sales_motion: Optional[str] = None
    benchmark_vs_peers: Optional[str] = None
    future_projections: Optional[str] = None
    strategic_priorities: Optional[str] = None
    industry_associations: Optional[str] = None
    case_studies: Optional[str] = None
    go_to_market_strategy: Optional[str] = None
    innovation_roadmap: Optional[str] = None
    product_pipeline: Optional[str] = None
    tam: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None

    # --- Culture fields ---
    employee_size: Optional[str] = None
    glassdoor_rating: Optional[str] = None
    indeed_rating: Optional[str] = None
    google_rating: Optional[str] = None
    leave_policy: Optional[str] = None
    health_support: Optional[str] = None
    fixed_vs_variable_pay: Optional[str] = None
    bonus_predictability: Optional[str] = None
    esops_incentives: Optional[str] = None
    family_health_insurance: Optional[str] = None
    relocation_support: Optional[str] = None
    lifestyle_benefits: Optional[str] = None
    hiring_velocity: Optional[str] = None
    employee_turnover: Optional[str] = None
    avg_retention_tenure: Optional[str] = None
    diversity_metrics: Optional[str] = None
    work_culture_summary: Optional[str] = None
    manager_quality: Optional[str] = None
    psychological_safety: Optional[str] = None
    feedback_culture: Optional[str] = None
    diversity_inclusion_score: Optional[str] = None
    ethical_standards: Optional[str] = None
    burnout_risk: Optional[str] = None
    layoff_history: Optional[str] = None
    mission_clarity: Optional[str] = None
    sustainability_csr: Optional[str] = None
    crisis_behavior: Optional[str] = None
    remote_policy_details: Optional[str] = None
    typical_hours: Optional[str] = None
    overtime_expectations: Optional[str] = None
    weekend_work: Optional[str] = None
    flexibility_level: Optional[str] = None
    location_centrality: Optional[str] = None
    public_transport_access: Optional[str] = None
    cab_policy: Optional[str] = None
    airport_commute_time: Optional[str] = None
    office_zone_type: Optional[str] = None
    area_safety: Optional[str] = None
    safety_policies: Optional[str] = None
    infrastructure_safety: Optional[str] = None
    emergency_preparedness: Optional[str] = None
    training_spend: Optional[str] = None
    onboarding_quality: Optional[str] = None
    learning_culture: Optional[str] = None
    exposure_quality: Optional[str] = None
    mentorship_availability: Optional[str] = None
    internal_mobility: Optional[str] = None
    promotion_clarity: Optional[str] = None
    tools_access: Optional[str] = None
    role_clarity: Optional[str] = None
    early_ownership: Optional[str] = None
    work_impact: Optional[str] = None
    execution_thinking_balance: Optional[str] = None
    automation_level: Optional[str] = None
    cross_functional_exposure: Optional[str] = None
    exit_opportunities: Optional[str] = None
    skill_relevance: Optional[str] = None
    external_recognition: Optional[str] = None
    network_strength: Optional[str] = None
    global_exposure: Optional[str] = None

    # --- Financials fields ---
    annual_revenue: Optional[str] = None
    annual_profit: Optional[str] = None
    revenue_mix: Optional[str] = None
    valuation: Optional[str] = None
    yoy_growth_rate: Optional[str] = None
    profitability_status: Optional[str] = None
    key_investors: Optional[str] = None
    recent_funding_rounds: Optional[str] = None
    total_capital_raised: Optional[str] = None
    customer_acquisition_cost: Optional[str] = None
    customer_lifetime_value: Optional[str] = None
    cac_ltv_ratio: Optional[str] = None
    churn_rate: Optional[str] = None
    net_promoter_score: Optional[str] = None
    burn_rate: Optional[str] = None
    runway_months: Optional[str] = None
    burn_multiplier: Optional[str] = None
    regulatory_status: Optional[str] = None
    legal_issues: Optional[str] = None
    esg_ratings: Optional[str] = None
    supply_chain_dependencies: Optional[str] = None
    geopolitical_risks: Optional[str] = None
    macro_risks: Optional[str] = None
    carbon_footprint: Optional[str] = None
    ethical_sourcing: Optional[str] = None
    customer_concentration_risk: Optional[str] = None
    exit_strategy_history: Optional[str] = None
    ceo_name: Optional[str] = None
    ceo_linkedin_url: Optional[str] = None
    key_leaders: Optional[str] = None
    warm_intro_pathways: Optional[str] = None
    decision_maker_access: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    board_members: Optional[str] = None
    company_maturity: Optional[str] = None
    brand_value: Optional[str] = None
    client_quality: Optional[str] = None
    technology_partners: Optional[str] = None
    intellectual_property: Optional[str] = None
    r_and_d_investment: Optional[str] = None
    ai_ml_adoption_level: Optional[str] = None
    tech_stack: Optional[str] = None
    cybersecurity_posture: Optional[str] = None
    partnership_ecosystem: Optional[str] = None
    tech_adoption_rating: Optional[str] = None


class JudgeOutput(BaseModel):
    """Agent 2 output: consolidated best-of-breed result with source tracking."""
    company_name: str
    consolidated: CompanyIntel
    source_map: Dict[str, str] = {}      # field_name -> "gemini" | "groq" | "openrouter" | "majority" | "longest" | "llm_judge" | "llm_filled"
    conflict_fields: list[str] = []       # fields that had all-3-disagree conflicts
    missing_fields: list[str] = []        # fields that were None in all 3 LLM outputs
    llm_judged_fields: list[str] = []     # fields resolved by LLM judge call (conflicts)
    llm_filled_fields: list[str] = []     # fields filled by LLM judge call (missing)
