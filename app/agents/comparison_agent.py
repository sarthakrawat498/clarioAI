import logging
from typing import Dict, Any, List
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

# Benchmark Policy Database for structured comparison
COMPARISON_BENCHMARKS = {
    "HDFC ERGO Optima Secure": {
        "insurer": "HDFC ERGO",
        "policy_name": "Optima Secure",
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
        "room_rent": "Single Private Room (No Capping)",
        "co_pay": "0%",
        "ped_waiting": "36 Months",
        "restoration": "ReAssure Forever (Active lifetime after 1st claim)",
        "no_claim_bonus": "Lock the Premium (No rate hike until 1st claim)",
        "pre_post_days": "60 Days / 180 Days",
        "daycare_robotic": "100% Covered (In-house claims team)",
        "air_ambulance": "Covered up to Sum Insured",
        "est_premium_30yr_10l": "₹13,900 / year",
        "highlight": "Lock-the-premium feature prevents age-based price increases until claim."
    }
}


def comparison_agent_node(state: AgentState) -> AgentState:
    """
    Comparison Agent: Generates side-by-side policy matrix comparing top health plans.
    """
    query = state.get("query", "").lower()
    
    # Identify target policies from query or pick default top 3
    selected_keys = []
    for key in COMPARISON_BENCHMARKS:
        policy_words = key.lower().split()
        if any(w in query for w in policy_words if len(w) > 3):
            if key not in selected_keys:
                selected_keys.append(key)

    if len(selected_keys) < 2:
        selected_keys = ["HDFC ERGO Optima Secure", "Care Health Supreme", "Star Health Optima Restore"]

    matrix = {}
    params = [
        ("Insurer", "insurer"),
        ("Room Rent Category", "room_rent"),
        ("Co-Payment", "co_pay"),
        ("PED Waiting Period", "ped_waiting"),
        ("Restoration Benefit", "restoration"),
        ("No Claim Bonus (NCB)", "no_claim_bonus"),
        ("Pre & Post Days", "pre_post_days"),
        ("Daycare & Robotic", "daycare_robotic"),
        ("Air Ambulance Limit", "air_ambulance"),
        ("Estimated Premium (10L)", "est_premium_30yr_10l"),
        ("Standout Advantage", "highlight")
    ]

    for label, field in params:
        matrix[label] = {p_key: COMPARISON_BENCHMARKS[p_key][field] for p_key in selected_keys}

    # Markdown Table Generation
    headers = ["Feature / Parameter"] + selected_keys
    table_lines = [
        "### 📊 Side-by-Side Policy Comparison Matrix",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for label, field in params:
        row_vals = [COMPARISON_BENCHMARKS[p_key][field] for p_key in selected_keys]
        table_lines.append(f"| **{label}** | " + " | ".join(row_vals) + " |")

    table_lines.extend([
        "",
        "#### 💡 Expert Recommendation & Verdict:",
        "- **Best overall feature richness**: **HDFC ERGO Optima Secure** (Provides instant 2x coverage & consumable protection).",
        "- **Best for high bonus accumulation**: **Care Health Supreme** (Up to 500% cumulative bonus super).",
        "- **Best for young buyers**: **Niva Bupa ReAssure 2.0** (Lock-the-premium guarantees constant pricing until first claim)."
    ])

    state["final_response"] = "\n".join(table_lines)
    state["comparison_table"] = matrix
    state["agent_used"] = "ComparisonAgent"
    return state
