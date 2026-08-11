import logging
import json
from typing import Dict, Any, List
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def _parse_highlights(raw_value: Any, policy: Dict[str, Any]) -> List[str]:
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str) and raw_value.strip():
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item).strip()]
        except Exception:
            pass

    highlights = []
    room_rent = policy.get("room_rent_limit")
    restoration = policy.get("restoration_benefit")
    bonus = policy.get("no_claim_bonus")
    if room_rent:
        highlights.append(str(room_rent))
    if restoration:
        highlights.append(str(restoration))
    if bonus:
        highlights.append(str(bonus))
    return highlights[:3]


def _is_no_capping(text: Any) -> bool:
    return isinstance(text, str) and "no capping" in text.lower()


def _build_dynamic_candidate(policy: Dict[str, Any], age: int, budget: float, peds: List[str]) -> Dict[str, Any]:
    premium = float(policy.get("base_annual_premium_estimate") or 12500.0)
    room_rent_limit = policy.get("room_rent_limit", "Standard Coverage")
    restoration_benefit = policy.get("restoration_benefit", "Restore Benefit")
    no_claim_bonus = policy.get("no_claim_bonus", "No Claim Bonus")
    network_hospitals_count = int(policy.get("network_hospitals_count") or 0)
    claim_settlement_ratio = float(policy.get("claim_settlement_ratio") or 0.0)
    ped_waiting_period_months = int(policy.get("ped_waiting_period_months") or 36)
    co_pay_percentage = float(policy.get("co_pay_percentage") or 0.0)
    description = policy.get("description") or ""
    key_highlights = _parse_highlights(policy.get("key_highlights"), policy)

    score = 70
    if _is_no_capping(room_rent_limit):
        score += 5
    if network_hospitals_count >= 12000:
        score += 4
    elif network_hospitals_count > 0 and network_hospitals_count < 9000:
        score -= 2
    if claim_settlement_ratio >= 98:
        score += 4
    if peds:
        if ped_waiting_period_months <= 36:
            score += 4
        else:
            score -= 3
    if age <= 35 and ("lock" in no_claim_bonus.lower() or "forever" in restoration_benefit.lower()):
        score += 5
    if age >= 60 and co_pay_percentage <= 0:
        score += 3
    if premium > budget:
        score -= 6
    elif premium <= budget * 0.8:
        score += 3
    if "unlimited" in description.lower():
        score += 2

    suitable_for = []
    if peds and ped_waiting_period_months <= 36:
        suitable_for.append("Users with pre-existing conditions seeking manageable waiting periods")
    if _is_no_capping(room_rent_limit):
        suitable_for.append("Buyers wanting flexible room category selection")
    if network_hospitals_count >= 12000:
        suitable_for.append("Families wanting a broad cashless hospital network")
    if premium <= budget:
        suitable_for.append("Budget-conscious buyers staying within premium limits")
    if not suitable_for:
        suitable_for.append("Users looking for a balanced health insurance option")

    riders = []
    if peds:
        riders.append("PED Reduction Rider")
    if age < 45:
        riders.append("Hospital Cash Rider")
    if network_hospitals_count >= 10000:
        riders.append("Cashless Network Access")
    if not riders:
        riders.append("Personal Accident Rider")

    return {
        "policy_id": int(policy.get("policy_id") or policy.get("id") or 0),
        "insurer_name": policy.get("insurer_name", "Unknown Insurer"),
        "policy_name": policy.get("policy_name", "Unknown Policy"),
        "est_premium": premium,
        "base_score": score,
        "highlights": key_highlights,
        "suitable_for": "; ".join(suitable_for),
        "riders": riders,
    }


def _static_candidates() -> List[Dict[str, Any]]:
    return [
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

    candidates = []
    policy_catalog = state.get("policy_catalog") or []
    if policy_catalog:
        for policy in policy_catalog:
            candidates.append(_build_dynamic_candidate(policy, age, budget, peds))
    else:
        candidates = _static_candidates()

    # Adjust scores dynamically based on profile
    scored = []
    for plan in candidates:
        plan["match_score"] = min(99, max(60, int(plan["base_score"])))
        scored.append(plan)

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top_plans = scored[:3]

    response_lines = [
        "Top AI Recommended Health Insurance Plans",
        f"Based on your profile (Age {age}, Budget ₹{budget:,.0f}, PED: {', '.join(peds) if peds else 'None'}), "
        "here are your top matched health insurance policies:\n"
    ]

    for idx, plan in enumerate(top_plans, start=1):
        response_lines.append(f"{idx}. {plan['insurer_name']} - {plan['policy_name']} (Match Score: {plan['match_score']}%)")
        response_lines.append(f"- Est. Annual Premium: ₹{plan['est_premium']:,.0f}")
        response_lines.append(f"- Best Suited For: {plan['suitable_for']}")
        response_lines.append(f"- Key Features: {', '.join(plan['highlights'])}")
        response_lines.append(f"- Recommended Riders: {', '.join(plan['riders'])}\n")

    response_lines.append("Would you like to run a side-by-side comparison of these plans or check custom claim scenarios?")

    state["final_response"] = "\n".join(response_lines)
    state["recommended_policies"] = top_plans
    state["agent_used"] = "SalesAgent"
    return state
