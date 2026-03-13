import pytest

# -------------------------------------------------------------------
# Mocked Data Access Layer (Replace with real implementation)
# -------------------------------------------------------------------

class CompanyProfileService:
    """
    Simulates company profile retrieval.
    Replace this with actual API / DB call.
    """

    def get_company_profile(self, entity_name: str) -> dict | None:
        """
        Returns None if company does not exist.
        """
        # Simulating non-existent lookup
        non_existent_entities = [
            "FakeCorpABC",
            "NonExistentCompanyXYZ123"
        ]

        if entity_name in non_existent_entities:
            return None

        # In real implementation this would return actual data
        return {"Company Name": "SomeCompany"}


# -------------------------------------------------------------------
# Test Configuration
# -------------------------------------------------------------------

NON_EXISTENT_COMPANIES = [
    "FakeCorpABC",
    "NonExistentCompanyXYZ123"
]

ALL_PROFILE_FIELDS = [
    "Company Name",
    "Short Name",
    "Logo",
    "Category",
    "Year of Incorporation",
    "Overview of the Company",
    "Nature of Company",
    "Company Headquarters",
    "Countries Operating In",
    "Number of Offices (beyond HQ)",
    "Office Locations",
    "Employee Size",
    "Hiring Velocity",
    "Employee Turnover",
    "Average Retention Tenure",
    "Pain Points Being Addressed",
    "Focus Sectors / Industries",
    "Services / Offerings / Products",
    "Top Customers by Client Segments",
    "Core Value Proposition",
    "Vision",
    "Mission",
    "Values",
    "Unique Differentiators",
    "Competitive Advantages",
    "Weaknesses / Gaps in Offering",
    "Key Challenges and Unmet Needs",
    "Key Competitors",
    "Technology Partners",
    "Interesting Facts",
    "Recent News",
    "Website URL",
    "Quality of Website",
    "Website Rating",
    "Website Traffic Rank",
    "Social Media Followers – Combined",
    "Glassdoor Rating",
    "Indeed Rating",
    "Google Reviews Rating",
    "LinkedIn Profile URL",
    "Twitter (X) Handle",
    "Facebook Page URL",
    "Instagram Page URL",
    "CEO Name",
    "CEO LinkedIn URL",
    "Key Business Leaders",
    "Warm Introduction Pathways",
    "Decision Maker Accessibility",
    "Company Contact Email",
    "Company Phone Number",
    "Primary Contact Person's Name",
    "Primary Contact Person's Title",
    "Primary Contact Person's Email",
    "Primary Contact Person's Phone Number",
    "Awards & Recognitions",
    "Brand Sentiment Score",
    "Event Participation",
    "Regulatory & Compliance Status",
    "Legal Issues / Controversies",
    "Annual Revenues",
    "Annual Profits",
    "Revenue Mix",
    "Company Valuation",
    "Year-over-Year Growth Rate",
    "Profitability Status",
    "Market Share (%)",
    "Key Investors / Backers",
    "Recent Funding Rounds",
    "Total Capital Raised",
    "ESG Practices or Ratings",
    "Sales Motion",
    "Customer Acquisition Cost (CAC)",
    "Customer Lifetime Value (CLV)",
    "CAC:LTV Ratio",
    "Churn Rate",
    "Net Promoter Score (NPS)",
    "Customer Concentration Risk",
    "Burn Rate",
    "Runway",
    "Burn Multiplier",
    "Intellectual Property",
    "R&D Investment",
    "AI/ML Adoption Level",
    "Tech Stack/Tools Used",
    "Cybersecurity Posture",
    "Supply Chain Dependencies",
    "Geopolitical Risks",
    "Macro Risks",
    "Diversity Metrics",
    "Remote Work Policy",
    "Training/Development Spend",
    "Partnership Ecosystem",
    "Exit Strategy/History",
    "Carbon Footprint/Environmental Impact",
    "Ethical Sourcing Practices",
    "Benchmark vs. Peers",
    "Future Projections",
    "Strategic Priorities",
    "Industry Associations / Memberships",
    "Case Studies / Public Success Stories",
    "Go-to-Market Strategy",
    "Innovation Roadmap",
    "Product Pipeline",
    "Board of Directors / Advisors",
    "Company Introduction / Marketing videos",
    "Customer testimonial",
    "Industry Benchmark Technology Adoption Rating",
    "Total Addressable Market (TAM)",
    "Serviceable Addressable Market (SAM)",
    "Serviceable Obtainable Market (SOM)",
    "Work culture",
    "Manager quality",
    "Psychological safety",
    "Feedback culture",
    "Diversity & inclusion",
    "Ethical standards",
    "Typical working hours",
    "Overtime expectations",
    "Weekend work",
    "Remote / hybrid / on-site flexibility",
    "Leave policy",
    "Burnout risk",
    "Central vs peripheral location",
    "Public transport access",
    "Cab availability and company cab policy",
    "Commute time from airport",
    "Office zone type",
    "Area safety",
    "Company safety policies",
    "Office infrastructure safety",
    "Emergency response preparedness",
    "Health support",
    "Onboarding and training quality",
    "Learning culture",
    "Exposure quality",
    "Mentorship availability",
    "Internal mobility",
    "Promotion clarity",
    "Tools and technology access",
    "Role clarity",
    "Early ownership",
    "Work impact",
    "Execution vs thinking balance",
    "Automation level",
    "Cross-functional exposure",
    "Company maturity",
    "Brand value",
    "Client quality",
    "Layoff history",
    "Fixed vs variable pay",
    "Bonus predictability",
    "ESOPs and long-term incentives",
    "Family health insurance",
    "Relocation support",
    "Lifestyle and wellness benefits",
    "Exit opportunities",
    "Skill relevance",
    "External recognition",
    "Network strength",
    "Global exposure",
    "Mission clarity",
    "Sustainability and CSR",
    "Crisis behavior"
]


# -------------------------------------------------------------------
# Core Test Logic
# -------------------------------------------------------------------

@pytest.mark.parametrize("entity_name", NON_EXISTENT_COMPANIES)
@pytest.mark.parametrize("field_name", ALL_PROFILE_FIELDS)
def test_all_fields_return_null_for_non_existent_company(entity_name, field_name):
    """
    Ensures that querying a non-existent company returns None
    and no field-level data is exposed.
    """

    service = CompanyProfileService()
    profile = service.get_company_profile(entity_name)

    # Entire profile should be None
    assert profile is None, (
        f"Expected None profile for non-existent company '{entity_name}', "
        f"but got: {profile}"
    )