import logging
import re
from typing import Dict, Any, List
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def _display_comparison_value(value: Any) -> str:
    if value is None or value == "":
        return "Not available in the provided policy data."
    return str(value)


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
        return selected

    # Fallback: extract "Insurer - Policy" lines from markdown recommendation lists.
    pattern = re.compile(r"\d+\.\s*([A-Za-z0-9 .&]+)\s*-\s*([A-Za-z0-9 .&]+)", re.IGNORECASE)
    for insurer, policy in pattern.findall(content):
        candidate = f"{insurer.strip()} {policy.strip()}"
        for key in valid_keys:
            if candidate.lower() == key.lower() and key not in selected:
                selected.append(key)
    return selected

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


def _build_dynamic_comparison_benchmarks(policy_catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    benchmarks = {}
    for policy in policy_catalog:
        key = f"{policy.get('insurer_name', 'Unknown')} {policy.get('policy_name', 'Policy')}"
        benchmarks[key] = {
            "insurer": policy.get("insurer_name", "Unknown"),
            "policy_name": policy.get("policy_name", "Policy"),
            "room_rent": _display_comparison_value(policy.get("room_rent_limit")),
            "co_pay": _display_comparison_value(f"{policy.get('co_pay_percentage')}%" if policy.get("co_pay_percentage") is not None else None),
            "ped_waiting": _display_comparison_value(f"{policy.get('ped_waiting_period_months')} Months" if policy.get("ped_waiting_period_months") is not None else None),
            "restoration": _display_comparison_value(policy.get("restoration_benefit")),
            "no_claim_bonus": _display_comparison_value(policy.get("no_claim_bonus")),
            "pre_post_days": _display_comparison_value(
                f"{policy.get('pre_hospitalization_days')} Days / {policy.get('post_hospitalization_days')} Days"
                if policy.get("pre_hospitalization_days") is not None and policy.get("post_hospitalization_days") is not None
                else None
            ),
            "daycare_robotic": "Covered" if policy.get("daycare_treatments_covered", True) else "Not Specified",
            "air_ambulance": "Covered" if policy.get("air_ambulance_cover", True) else "Not Specified",
            "est_premium_30yr_10l": _display_comparison_value(
                f"₹{float(policy.get('base_annual_premium_estimate')):,.0f} / year" if policy.get("base_annual_premium_estimate") is not None else None
            ),
            "highlight": _display_comparison_value(policy.get("description")),
            "claim_settlement_ratio": float(policy.get("claim_settlement_ratio") or 0.0),
            "network_hospitals_count": int(policy.get("network_hospitals_count") or 0),
        }
    return benchmarks


def _build_uploaded_policy_benchmark(uploaded_policy_baseline: Dict[str, Any]) -> Dict[str, Any] | None:
    if not uploaded_policy_baseline:
        return None

    extracted = uploaded_policy_baseline.get("extracted_summary") or {}
    benefits = uploaded_policy_baseline.get("benefits") or extracted.get("benefits") or []
    policy_label = uploaded_policy_baseline.get("policy_name") or uploaded_policy_baseline.get("source_file_name") or "Uploaded Policy"

    pre_hosp = extracted.get("pre_hospitalization_days")
    post_hosp = extracted.get("post_hospitalization_days")
    co_pay = extracted.get("co_pay_percentage")
    ped_waiting = extracted.get("ped_waiting_period_months")
    claim_settlement = extracted.get("claim_settlement_ratio")
    network_hospitals = extracted.get("network_hospitals_count")

    if co_pay is not None and co_pay != "":
        co_pay_display = f"{co_pay}%" if not str(co_pay).strip().endswith("%") else str(co_pay)
    else:
        co_pay_display = None

    if ped_waiting is not None:
        ped_display = f"{ped_waiting} Months"
    else:
        ped_display = None

    if pre_hosp is not None and post_hosp is not None:
        pre_post_display = f"{pre_hosp} Days / {post_hosp} Days"
    else:
        pre_post_display = None

    if claim_settlement is not None and claim_settlement != "":
        claim_settlement_value = float(claim_settlement)
    else:
        claim_settlement_value = 0.0

    if network_hospitals is not None and network_hospitals != "":
        network_hospitals_value = int(network_hospitals)
    else:
        network_hospitals_value = 0

    return {
        "insurer": "Your Uploaded Policy",
        "policy_name": policy_label,
        "room_rent": _display_comparison_value(extracted.get("room_rent_limit")),
        "co_pay": _display_comparison_value(co_pay_display),
        "ped_waiting": _display_comparison_value(ped_display),
        "restoration": _display_comparison_value(extracted.get("restoration_benefit")),
        "no_claim_bonus": _display_comparison_value(extracted.get("no_claim_bonus")),
        "pre_post_days": _display_comparison_value(pre_post_display),
        "daycare_robotic": _display_comparison_value("Covered" if extracted.get("daycare_treatments_covered") is True else ("Not Specified" if extracted.get("daycare_treatments_covered") is False else None)),
        "air_ambulance": _display_comparison_value("Covered" if extracted.get("air_ambulance_cover") is True else ("Not Specified" if extracted.get("air_ambulance_cover") is False else None)),
        "est_premium_30yr_10l": _display_comparison_value(
            f"₹{float(uploaded_policy_baseline.get('uploaded_premium')):,.0f} / year"
            if uploaded_policy_baseline.get("uploaded_premium") is not None
            else None
        ),
        "highlight": _display_comparison_value(
            "; ".join([str(item) for item in benefits[:3] if item]) if benefits else None
        ),
        "claim_settlement_ratio": claim_settlement_value,
        "network_hospitals_count": network_hospitals_value,
    }


def _extract_selected_policy_keys_from_ids(
    policy_catalog: List[Dict[str, Any]],
    comparison_benchmarks: Dict[str, Dict[str, Any]],
    selected_ids: List[int],
) -> List[str]:
    if not selected_ids:
        return []

    id_map = {str(policy.get("policy_id") or policy.get("id")): policy for policy in policy_catalog}
    ordered_keys: List[str] = []
    for raw_id in selected_ids:
      
        policy = id_map.get(str(raw_id))
        if not policy:
            continue
        key = f"{policy.get('insurer_name', 'Unknown')} {policy.get('policy_name', 'Policy')}"
        if key in comparison_benchmarks and key not in ordered_keys:
            ordered_keys.append(key)
    return ordered_keys


def comparison_agent_node(state: AgentState) -> AgentState:
    """
    Comparison Agent: Generates side-by-side policy matrix comparing top health plans.
    """
    query = state.get("query", "").lower()
    messages = state.get("messages", []) or []
    policy_catalog = state.get("policy_catalog") or []
    compare_policy_ids = state.get("compare_policy_ids") or []
    uploaded_policy_baseline = state.get("uploaded_policy_baseline") or {}
    comparison_benchmarks = _build_dynamic_comparison_benchmarks(policy_catalog) if policy_catalog else COMPARISON_BENCHMARKS
    uploaded_policy_benchmark = _build_uploaded_policy_benchmark(uploaded_policy_baseline)
    uploaded_policy_key = None
    if uploaded_policy_benchmark:
        uploaded_policy_key = uploaded_policy_benchmark["policy_name"] or "Uploaded Policy"
        comparison_benchmarks = {**comparison_benchmarks, uploaded_policy_key: uploaded_policy_benchmark}
    
    # Identify target policies from query or pick default top 3
    selected_keys = []

    selected_from_ids = _extract_selected_policy_keys_from_ids(policy_catalog, comparison_benchmarks, compare_policy_ids)
    if selected_from_ids:
        selected_keys = selected_from_ids
    else:
        selected_from_history = _extract_recommended_policy_names(messages, list(comparison_benchmarks.keys()))
        if selected_from_history:
            selected_keys = selected_from_history

    if not selected_keys:
        for key in comparison_benchmarks:
            policy_words = key.lower().split()
            if any(w in query for w in policy_words if len(w) > 3):
                if key not in selected_keys:
                    selected_keys.append(key)

    if len(selected_keys) < 2 and not compare_policy_ids:
        if policy_catalog:
            ranked = sorted(
                comparison_benchmarks.items(),
                key=lambda item: (
                    item[1].get("claim_settlement_ratio", 0.0),
                    item[1].get("network_hospitals_count", 0),
                ),
                reverse=True,
            )
            selected_keys = [key for key, _ in ranked[:3] if key != uploaded_policy_key]
        else:
            selected_keys = ["HDFC ERGO Optima Secure", "Care Health Supreme"]

    display_keys = list(selected_keys)
    if uploaded_policy_key and uploaded_policy_key not in display_keys:
        display_keys.append(uploaded_policy_key)

    if len(display_keys) < 2:
        state["final_response"] = (
            "### 📊 Side-by-Side Policy Comparison Matrix\n\n"
            "Please select at least one catalogue policy to compare against your uploaded policy."
        )
        state["comparison_table"] = None
        state["agent_used"] = "ComparisonAgent (Selection Required)"
        return state

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
        matrix[label] = {p_key: comparison_benchmarks[p_key][field] for p_key in display_keys}

    # Markdown Table Generation
    headers = ["Feature / Parameter"] + display_keys
    table_lines = [
        "### 📊 Side-by-Side Policy Comparison Matrix",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for label, field in params:
        row_vals = [_display_comparison_value(comparison_benchmarks[p_key][field]) for p_key in display_keys]
        table_lines.append(f"| **{label}** | " + " | ".join(row_vals) + " |")

    table_lines.extend([
        "",
        "#### 💡 Neutral Comparison Verdict:",
    ])

    table_lines.extend([
        "#### Factual Summary:",
        "- The table above shows the structured differences available in the current policy catalogue.",
        "- Any missing value should be treated as not available in the provided policy data.",
        "- No unsupported expert winner is inferred here."
    ])

    state["final_response"] = "\n".join(table_lines)
    state["comparison_table"] = matrix
    state["agent_used"] = "ComparisonAgent"
    return state
