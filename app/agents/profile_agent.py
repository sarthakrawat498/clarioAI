import logging
from typing import Dict, Any
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def profile_agent_node(state: AgentState) -> AgentState:
    """
    Profile Agent: Analyzes user demographic profile, identifies health risk factors,
    and prompts for missing inputs if necessary.
    """
    profile = state.get("user_profile", {}) or {}
    query = state.get("query", "")
    
    age = profile.get("age", 30)
    peds = profile.get("pre_existing_diseases", [])
    if isinstance(peds, str):
        import json
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []
            
    city_tier = profile.get("city_tier", "Tier 1")
    coverage_type = profile.get("coverage_type", "Family Floater")
    budget = profile.get("budget_annual_max", 25000)

    # Health Risk Assessment
    risk_factors = []
    if age > 50:
        risk_factors.append("Higher age bracket (>50) requires strict room rent uncapping & lower co-pay clauses.")
    if peds:
        risk_factors.append(f"Pre-existing diseases declared ({', '.join(peds)}) require careful evaluation of PED waiting periods (12 to 36 months).")
    if profile.get("tobacco_user"):
        risk_factors.append("Tobacco usage requires underwriting clearance & potential 10-15% premium loading.")

    response_lines = [
        "👤 Customer Profile Analysis & Health Risk Card",
        f"- Age: {age} years",
        f"- City Tier: {city_tier}",
        f"- Coverage Type: {coverage_type} ({profile.get('family_members_count', 2)} members)",
        f"- Pre-existing Conditions: {', '.join(peds) if peds else 'None Declared'}",
        f"- Annual Budget: ₹{budget:,.0f}",
        ""
    ]

    if risk_factors:
        response_lines.append("⚠️ Key Risk Considerations for Policy Selection:")
        for rf in risk_factors:
            response_lines.append(f"- {rf}")
        response_lines.append("")

    response_lines.append(
        "💡 Next Steps: Use this profile to get policy recommendations, or switch to the premium, claim, coverage, or comparison routes for a narrower answer."
    )

    state["final_response"] = "\n".join(response_lines)
    state["agent_used"] = "ProfileAgent"
    return state
