import logging
from typing import Dict, Any, List
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def sales_agent_node(state: AgentState) -> AgentState:
    """
    Sales Agent: Computes multi-attribute policy match scores based on user profile,
    ranks recommendations, and suggests optional add-on riders.
    """
    profile = state.get("user_profile", {}) or {}
    age = profile.get("age", 30)
    budget = profile.get("budget_annual_max", 25000)
    peds = profile.get("pre_existing_diseases", [])
    if isinstance(peds, str):
        import json
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []

    # Scoring Algorithm for 4 major plans
    candidates = [
        {
            "policy_id": 1,
            "insurer_name": "HDFC ERGO",
            "policy_name": "Optima Secure",
            "est_premium": 14500,
            "base_score": 92,
            "highlights": ["2X Base Sum Insured from Day 1", "Zero Deductions on Consumables", "No Room Rent Limit"],
            "suitable_for": "Families seeking premium zero-hassle coverage with consumable protection.",
            "riders": ["Critical Illness Rider (₹25L)", "Hospital Daily Cash (₹2,000/day)"]
        },
        {
            "policy_id": 2,
            "insurer_name": "Care Health",
            "policy_name": "Care Supreme",
            "est_premium": 13200,
            "base_score": 90,
            "highlights": ["500% Cumulative Bonus Super", "Unlimited Automatic Restore", "Instant PED Add-On"],
            "suitable_for": "Individuals with pre-existing conditions looking for short waiting periods.",
            "riders": ["Instant PED Reduction Rider", "Maternity & Newborn Cover"]
        },
        {
            "policy_id": 3,
            "insurer_name": "Niva Bupa",
            "policy_name": "ReAssure 2.0",
            "est_premium": 13900,
            "base_score": 88,
            "highlights": ["Lock the Premium until 1st claim", "ReAssure Forever Restoration", "30% Live Healthier Discount"],
            "suitable_for": "Young professionals who want locked low premiums for years.",
            "riders": ["Personal Accident Cover", "International Medical Second Opinion"]
        },
        {
            "policy_id": 4,
            "insurer_name": "Star Health",
            "policy_name": "Optima Restore",
            "est_premium": 12800,
            "base_score": 84,
            "highlights": ["100% Automatic Restore", "14,000+ Cashless Hospital Network", "Free Annual Health Checkup"],
            "suitable_for": "Budget-conscious families wanting wide hospital network access.",
            "riders": ["Hospital Cash Rider", "Star Outpatient Consult Cover"]
        }
    ]

    # Adjust scores dynamically based on profile
    scored = []
    for plan in candidates:
        score = plan["base_score"]
        
        # PED adjustment: Care Supreme & HDFC gain for PED reduction options
        if peds:
            if plan["policy_name"] in ["Care Supreme", "Optima Secure"]:
                score += 4
            elif plan["policy_name"] == "Optima Restore":
                score -= 3 # 4 yr waiting period penalty

        # Age adjustment: Young buyers get boost for Niva Bupa Lock Premium
        if age <= 35 and plan["policy_name"] == "ReAssure 2.0":
            score += 5

        # Budget check
        if plan["est_premium"] > budget:
            score -= 6
        elif plan["est_premium"] <= budget * 0.7:
            score += 3

        plan["match_score"] = min(99, max(60, score))
        scored.append(plan)

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top_plans = scored[:3]

    response_lines = [
        "### 🎯 Top AI Recommended Health Insurance Plans",
        f"Based on your profile (*Age {age}, Budget ₹{budget:,.0f}, PED: {', '.join(peds) if peds else 'None'}*), "
        "here are your top matched health insurance policies:\n"
    ]

    for idx, plan in enumerate(top_plans, start=1):
        response_lines.append(f"#### #{idx} {plan['insurer_name']} - {plan['policy_name']} (Match Score: **{plan['match_score']}%**)")
        response_lines.append(f"- **Est. Annual Premium**: ₹{plan['est_premium']:,.0f}")
        response_lines.append(f"- **Best Suited For**: {plan['suitable_for']}")
        response_lines.append(f"- **Key Features**: {', '.join(plan['highlights'])}")
        response_lines.append(f"- **Recommended Riders**: {', '.join(plan['riders'])}\n")

    response_lines.append("💡 *Would you like to run a side-by-side comparison of these plans or check custom claim scenarios?*")

    state["final_response"] = "\n".join(response_lines)
    state["recommended_policies"] = top_plans
    state["agent_used"] = "SalesAgent"
    return state
