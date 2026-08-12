import logging
import re
from typing import Dict, Any, List
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def _extract_recommended_policy_names(messages: List[Dict[str, Any]], valid_keys: List[str]) -> List[str]:
    """Extract policy keys from the latest assistant recommendation text."""
    last_assistant = None
    for msg in reversed(messages or []):
        if msg.get("role") == "assistant" and "salesagent" in str(msg.get("agent_name", "")).lower():
            last_assistant = msg
            break

    if not last_assistant:
        return []

    content = str(last_assistant.get("content", ""))
    if not content:
        return []

    selected = []
    for key in valid_keys:
        insurer, _, policy = key.partition(" ")
        # Match by insurer + policy token hints to handle markdown variants.
        insurer_hit = insurer.lower() in content.lower()
        policy_hit = policy.lower() in content.lower()
        if insurer_hit and policy_hit:
            selected.append(key)

    if selected:
        return selected[:4]

    # Fallback: extract "Insurer - Policy" lines from markdown recommendation lists.
    pattern = re.compile(r"\d+\.\s*([A-Za-z0-9 .&]+)\s*-\s*([A-Za-z0-9 .&]+)", re.IGNORECASE)
    for insurer, policy in pattern.findall(content):
        candidate = f"{insurer.strip()} {policy.strip()}"
        for key in valid_keys:
            if candidate.lower() == key.lower() and key not in selected:
                selected.append(key)
    return selected[:4]

# Benchmark Policy Database for structured comparison
COMPARISON_BENCHMARKS = {
    "HDFC ERGO Optima Secure": {
        "insurer": "HDFC ERGO",
        "policy_name": "Optima Secure",
        "sum_insured": "₹5 Lakhs to ₹1 Crore (Flexible Sum Insured)",
        "room_rent": "Single Private AC Room (No Capping)",
        "co_pay": "0%",
        "ped_waiting": "36 Months (Option for 12 Months)",
        "restoration": "100% Automatic Restore (Unlimited times)",
        "no_claim_bonus": "50% in Year 1, 100% in Year 2 (Secure + Plus Benefit)",
        "pre_post_days": "60 Days / 180 Days",
        "daycare_robotic": "100% Covered (Zero deduction on consumables)",
        "air_ambulance": "Up to ₹5,00,000",
        "est_premium_30yr_10l": "₹14,500 / year",
        "highlight": "2x Base Coverage from Day 1 + Consumables Protect Rider included."
    },
    "Star Health Optima Restore": {
        "insurer": "Star Health",
        "policy_name": "Optima Restore",
        "sum_insured": "₹5 Lakhs to ₹1 Crore (Flexible Sum Insured)",
        "room_rent": "Single Private AC Room",
        "co_pay": "0% (<60 yrs) / 10% (>61 yrs)",
        "ped_waiting": "48 Months (4 Years)",
        "restoration": "100% Automatic Restore once per year",
        "no_claim_bonus": "20% per claim-free year up to 100%",
        "pre_post_days": "60 Days / 90 Days",
        "daycare_robotic": "Covered with Cataract Sub-limit ₹40,000/eye",
        "air_ambulance": "Up to ₹2,50,000",
        "est_premium_30yr_10l": "₹12,800 / year",
        "highlight": "Established pan-India network with 14,000+ hospital partnerships."
    },
    "Care Health Supreme": {
        "insurer": "Care Health",
        "policy_name": "Care Supreme",
        "sum_insured": "₹5 Lakhs to ₹1 Crore (Flexible Sum Insured)",
        "room_rent": "No Room Rent Capping (Any Room Category)",
        "co_pay": "0%",
        "ped_waiting": "36 Months (Instant PED Rider available)",
        "restoration": "Unlimited 100% Automatic Recharge",
        "no_claim_bonus": "50% per year up to 500% (5x Cumulative Bonus Super)",
        "pre_post_days": "60 Days / 180 Days",
        "daycare_robotic": "100% Covered across all modern treatments",
        "air_ambulance": "Up to Base Sum Insured",
        "est_premium_30yr_10l": "₹13,200 / year",
        "highlight": "Highest cumulative bonus potential (500%) & unlimited recharge."
    },
    "Niva Bupa ReAssure 2.0": {
        "insurer": "Niva Bupa",
        "policy_name": "ReAssure 2.0",
        "sum_insured": "₹5 Lakhs to ₹1 Crore (Flexible Sum Insured)",
        "room_rent": "Single Private Room (No Capping)",
        "co_pay": "0%",
        "ped_waiting": "36 Months",
        "restoration": "ReAssure Forever (Active lifetime after 1st claim)",
        "no_claim_bonus": "Lock the Premium (No rate hike until 1st claim)",
        "pre_post_days": "60 Days / 180 Days",
        "daycare_robotic": "100% Covered (In-house claims team)",
        "highlight": "Lock-the-premium feature prevents age-based price increases until first claim."
    }
}


def _build_dynamic_comparison_benchmarks(policy_catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    import re

    benchmarks = {}
    for policy in policy_catalog:
        key = f"{policy.get('insurer_name', 'Unknown')} {policy.get('policy_name', 'Policy')}"
        min_si = float(policy.get("base_sum_insured_min") or 500000)
        max_si = float(policy.get("base_sum_insured_max") or 100000000)
        min_str = f"₹{min_si/100000:,.0f} Lakhs" if min_si >= 100000 else f"₹{min_si:,.0f}"
        max_str = f"₹{max_si/10000000:,.0f} Crore" if max_si >= 10000000 else f"₹{max_si/100000:,.0f} Lakhs"

        raw_desc = str(policy.get("description") or "")
        cleaned_highlight = re.sub(r'Discovered from [^:]+:\s*', '', raw_desc).strip()
        if not cleaned_highlight:
            cleaned_highlight = f"Comprehensive coverage with {policy.get('room_rent_limit', 'Single Private Room')} and {policy.get('restoration_benefit', '100% Restoration')}."

        benchmarks[key] = {
            "insurer": policy.get("insurer_name", "Unknown"),
            "policy_name": policy.get("policy_name", "Policy"),
            "sum_insured": f"{min_str} to {max_str} (Flexible Sum Insured)",
            "room_rent": policy.get("room_rent_limit", "N/A"),
            "co_pay": f"{policy.get('co_pay_percentage', 0.0)}%",
            "ped_waiting": f"{policy.get('ped_waiting_period_months', 36)} Months",
            "restoration": policy.get("restoration_benefit", "N/A"),
            "no_claim_bonus": policy.get("no_claim_bonus", "N/A"),
            "pre_post_days": f"{policy.get('pre_hospitalization_days', 60)} Days / {policy.get('post_hospitalization_days', 180)} Days",
            "daycare_robotic": "Covered" if policy.get("daycare_treatments_covered", True) else "Not Specified",
            "air_ambulance": "Covered" if policy.get("air_ambulance_cover", True) else "Not Specified",
            "est_premium_30yr_10l": f"₹{float(policy.get('base_annual_premium_estimate') or 0):,.0f} / year",
            "highlight": cleaned_highlight,
            "claim_settlement_ratio": float(policy.get("claim_settlement_ratio") or 0.0),
            "network_hospitals_count": int(policy.get("network_hospitals_count") or 0),
        }
    return benchmarks


def comparison_agent_node(state: AgentState) -> AgentState:
    """
    Comparison Agent: Generates side-by-side policy matrix comparing top health plans.
    """
    query = state.get("query", "").lower()
    messages = state.get("messages", []) or []
    policy_catalog = state.get("policy_catalog") or []
    comparison_benchmarks = _build_dynamic_comparison_benchmarks(policy_catalog) if policy_catalog else COMPARISON_BENCHMARKS
    
    # Identify target policies from query or pick default top 3
    selected_keys = []
    selected_from_history = _extract_recommended_policy_names(messages, list(comparison_benchmarks.keys()))
    if len(selected_from_history) >= 2:
        selected_keys = selected_from_history

    for key in comparison_benchmarks:
        policy_words = key.lower().split()
        if any(w in query for w in policy_words if len(w) > 3):
            if key not in selected_keys:
                selected_keys.append(key)

    if len(selected_keys) < 2:
        if policy_catalog:
            ranked = sorted(
                comparison_benchmarks.items(),
                key=lambda item: (
                    item[1].get("claim_settlement_ratio", 0.0),
                    item[1].get("network_hospitals_count", 0),
                ),
                reverse=True,
            )
            selected_keys = [key for key, _ in ranked[:3]]
        else:
            selected_keys = ["HDFC ERGO Optima Secure", "Care Health Supreme", "Star Health Optima Restore"]

    matrix = {}
    params = [
        ("Insurer", "insurer"),
        ("Sum Insured Options", "sum_insured"),
        ("Room Rent Category", "room_rent"),
        ("Co-Payment", "co_pay"),
        ("PED Waiting Period", "ped_waiting"),
        ("Restoration Benefit", "restoration"),
        ("No Claim Bonus (NCB)", "no_claim_bonus"),
        ("Pre & Post Days", "pre_post_days"),
        ("Daycare & Robotic", "daycare_robotic"),
        ("Air Ambulance Limit", "air_ambulance"),
        ("Estimated Premium (10L)", "est_premium_30yr_10l"),
        ("Key Benefit Highlight", "highlight")
    ]

    for label, field in params:
        matrix[label] = {p_key: comparison_benchmarks[p_key][field] for p_key in selected_keys}

    # Clean Markdown Table Generation (No raw # hash symbols)
    headers = ["Feature / Parameter"] + selected_keys
    table_lines = [
        "📊 **Side-by-Side Policy Comparison Matrix**",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for label, field in params:
        row_vals = [str(comparison_benchmarks[p_key][field]) for p_key in selected_keys]
        table_lines.append(f"| **{label}** | " + " | ".join(row_vals) + " |")

    table_lines.extend([
        "",
        "💡 **Expert Recommendation & Verdict:**",
    ])

    if policy_catalog and selected_keys:
        top_policy = selected_keys[0]
        second_policy = selected_keys[1] if len(selected_keys) > 1 else selected_keys[0]
        third_policy = selected_keys[2] if len(selected_keys) > 2 else second_policy
        table_lines.extend([
            f"- **Best overall feature richness**: **{top_policy}** (Highest combined coverage, network, and premium balance).",
            f"- **Best for value and affordability**: **{second_policy}** (Strong features relative to premium).",
            f"- **Best network / fallback option**: **{third_policy}** (Broad cashless coverage and balanced benefits)."
        ])
    else:
        table_lines.extend([
            "- **Best overall feature richness**: **HDFC ERGO Optima Secure** (Provides instant 2x coverage & consumable protection).",
            "- **Best for high bonus accumulation**: **Care Health Supreme** (Up to 500% cumulative bonus super).",
            "- **Best for young buyers**: **Niva Bupa ReAssure 2.0** (Lock-the-premium guarantees constant pricing until first claim)."
        ])

    state["final_response"] = "\n".join(table_lines)
    state["comparison_table"] = matrix
    state["agent_used"] = "ComparisonAgent"
    return state

