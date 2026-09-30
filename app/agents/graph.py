import logging
import re
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router_agent import router_agent_node
from app.agents.profile_agent import profile_agent_node
from app.agents.coverage_agent import coverage_agent_node
from app.agents.comparison_agent import comparison_agent_node
from app.agents.sales_agent import sales_agent_node
from app.agents.chat_agent import chat_agent_node
from app.schemas.recommendation import PremiumEstimateRequest
from app.schemas.claim import ClaimCheckRequest
from app.services.premium_service import calculate_actuarial_premium
from app.services.claim_service import (
    evaluate_claim_eligibility,
    evaluate_policy_claim_amount_coverage,
)

logger = logging.getLogger(__name__)


_KNOWN_TREATMENT_HINTS = {
    "cataract": "Cataract Surgery",
    "appendectomy": "Appendectomy",
    "robotic surgery": "Robotic Surgery",
    "knee": "Knee Replacement",
    "heart": "Cardiac Treatment",
    "diabetes": "Diabetes Complications",
    "hospitalization": "Hospitalization",
}


def _extract_money_value(query: str) -> float | None:
    match = re.search(r"(?:₹|rs\.?|inr|rupees?|amount of|claim of)\s*([0-9][0-9,]*(?:\.[0-9]+)?)", query, re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_policy_name(query: str, policy_catalog: List[Dict[str, Any]], default: str | None = None) -> str | None:
    query_lower = query.lower()
    for policy in policy_catalog or []:
        insurer = str(policy.get("insurer_name", "")).strip()
        policy_name = str(policy.get("policy_name", "")).strip()
        if insurer and insurer.lower() in query_lower and policy_name and policy_name.lower() in query_lower:
            return f"{insurer} {policy_name}".strip()
        if policy_name and policy_name.lower() in query_lower:
            return f"{insurer} {policy_name}".strip() if insurer else policy_name
    return default


def _resolve_policy_from_catalog(
    query: str,
    policy_catalog: List[Dict[str, Any]],
    filter_company: str | None = None,
    filter_policy: str | None = None,
) -> Dict[str, Any] | None:
    normalized_company = (filter_company or "").strip().lower()
    normalized_policy = (filter_policy or "").strip().lower()
    query_lower = query.lower()

    for policy in policy_catalog or []:
        insurer = str(policy.get("insurer_name", "")).strip()
        policy_name = str(policy.get("policy_name", "")).strip()
        combined = f"{insurer} {policy_name}".strip().lower()

        if normalized_company and normalized_policy:
            if insurer.lower() == normalized_company and policy_name.lower() == normalized_policy:
                return policy
        elif normalized_policy:
            if policy_name.lower() == normalized_policy or combined == normalized_policy:
                return policy

        if insurer and policy_name and insurer.lower() in query_lower and policy_name.lower() in query_lower:
            return policy
        if policy_name and policy_name.lower() in query_lower:
            return policy

    return None


def _policy_label(policy: Dict[str, Any] | None) -> str:
    if not policy:
        return ""
    insurer = str(policy.get("insurer_name", "")).strip()
    policy_name = str(policy.get("policy_name", "")).strip()
    return f"{insurer} {policy_name}".strip()


def _extract_treatment_name(query: str) -> str:
    query_lower = query.lower()
    for hint, treatment in _KNOWN_TREATMENT_HINTS.items():
        if hint in query_lower:
            return treatment
    if "hospital stay" in query_lower or "hospitalization" in query_lower:
        return "Hospitalization"
    return query.strip()[:80] or "General Hospitalization"


def _premium_agent_node(state: AgentState) -> AgentState:
    profile = state.get("user_profile", {}) or {}
    query = state.get("query", "")
    policy_catalog = state.get("policy_catalog") or []
    selected_policy = _resolve_policy_from_catalog(
        query=query,
        policy_catalog=policy_catalog,
        filter_company=state.get("filter_company"),
        filter_policy=state.get("filter_policy"),
    )

    if selected_policy is None:
        premium_options = []
        for policy in policy_catalog[:5]:
            premium_value = policy.get("base_annual_premium_estimate")
            premium_text = f"₹{float(premium_value):,.0f}" if premium_value is not None else "Not available"
            premium_options.append(
                f"- {policy.get('insurer_name', 'Unknown Insurer')} - {policy.get('policy_name', 'Unknown Policy')} ({premium_text})"
            )

        state["final_response"] = (
            "### 💰 Premium Estimate\n\n"
            "Please choose one policy from the catalogue first so I can calculate a policy-specific premium.\n\n"
            "**Suggested policies:**\n"
            + "\n".join(premium_options or ["- No policies are available in the catalogue right now."])
        )
        state["agent_used"] = "PremiumAgent (Selection Required)"
        state["recommended_policies"] = None
        state["comparison_table"] = None
        return state

    request = PremiumEstimateRequest(
        age=int(profile.get("age") or 30),
        city_tier=str(profile.get("city_tier") or "Tier 1"),
        sum_insured=float(profile.get("sum_insured_preference") or 1000000.0),
        coverage_type=str(profile.get("coverage_type") or "Individual"),
        family_members_count=int(profile.get("family_members_count") or 1),
        pre_existing_diseases=profile.get("pre_existing_diseases") or [],
        tobacco_user=bool(profile.get("tobacco_user") or False),
        add_on_riders=profile.get("add_on_riders") or [],
        policy_id=selected_policy.get("policy_id") or selected_policy.get("id"),
        policy_name=f"{selected_policy.get('insurer_name', '')} {selected_policy.get('policy_name', '')}".strip(),
    )

    premium = calculate_actuarial_premium(request)
    breakdown_lines = [
        "### 💰 Premium Estimate",
        f"- **Policy:** {premium.policy_name}",
        f"- **Total Annual Premium:** ₹{premium.total_annual_premium:,.2f}",
        f"- **Base Premium:** ₹{premium.base_premium:,.2f}",
        f"- **GST (18%):** ₹{premium.gst_18_percent:,.2f}",
        f"- **Monthly Installment:** ₹{premium.monthly_installment:,.2f}",
        "",
        "**Breakdown**",
    ]
    for item in premium.breakdown:
        breakdown_lines.append(f"- {item.name}: ₹{item.amount:,.2f} ({item.description})")

    state["final_response"] = "\n".join(breakdown_lines)
    state["agent_used"] = "PremiumAgent (Actuarial Service)"
    state["recommended_policies"] = None
    state["comparison_table"] = None
    return state


def _claim_agent_node(state: AgentState) -> AgentState:
    profile = state.get("user_profile", {}) or {}
    query = state.get("query", "")
    policy_catalog = state.get("policy_catalog") or []
    query_lower = query.lower()
    claim_amount = state.get("claim_amount")
    selected_policy = _resolve_policy_from_catalog(
        query=query,
        policy_catalog=policy_catalog,
        filter_company=state.get("filter_company"),
        filter_policy=state.get("filter_policy"),
    )

    if selected_policy is None:
        premium_options = []
        for policy in policy_catalog[:5]:
            premium_value = policy.get("base_annual_premium_estimate")
            premium_text = f"₹{float(premium_value):,.0f}" if premium_value is not None else "Not available"
            premium_options.append(
                f"- {policy.get('insurer_name', 'Unknown Insurer')} - {policy.get('policy_name', 'Unknown Policy')} ({premium_text})"
            )

        state["final_response"] = (
            "### 🧾 Claim Eligibility Check\n\n"
            "Please choose one policy from the catalogue first so I can evaluate claim eligibility against that policy.\n\n"
            "**Suggested policies:**\n"
            + "\n".join(premium_options or ["- No policies are available in the catalogue right now."])
        )
        state["agent_used"] = "ClaimAgent (Selection Required)"
        state["recommended_policies"] = None
        state["comparison_table"] = None
        return state

    claimed_amount = claim_amount if claim_amount is not None else _extract_money_value(query)
    if claimed_amount is None:
        policy_label = _policy_label(selected_policy)
        room_rent = selected_policy.get("room_rent_limit") or "Not available"
        ped_months = selected_policy.get("ped_waiting_period_months")
        pre_hosp = selected_policy.get("pre_hospitalization_days")
        post_hosp = selected_policy.get("post_hospitalization_days")
        co_pay = selected_policy.get("co_pay_percentage")
        claim_settlement = selected_policy.get("claim_settlement_ratio")
        network_hospitals = selected_policy.get("network_hospitals_count")

        state["final_response"] = (
            "### 🧾 Claim Chart\n"
            f"- **Policy:** {policy_label}\n"
            f"- **Room Rent:** {room_rent}\n"
            f"- **PED Waiting Period:** {f'{int(ped_months)} months' if ped_months is not None else 'Not available'}\n"
            f"- **Pre-Hospitalization:** {pre_hosp if pre_hosp is not None else 'Not available'} days\n"
            f"- **Post-Hospitalization:** {post_hosp if post_hosp is not None else 'Not available'} days\n"
            f"- **Co-pay:** {f'{float(co_pay):.0f}%' if co_pay is not None else 'Not available'}\n"
            f"- **Claim Settlement Ratio:** {f'{float(claim_settlement):.1f}%' if claim_settlement is not None else 'Not available'}\n"
            f"- **Network Hospitals:** {network_hospitals if network_hospitals is not None else 'Not available'}\n\n"
            "If you want a specific claim amount checked against this policy, reply with the amount in rupees."
        )
        state["agent_used"] = "ClaimAgent (Policy Chart)"
        state["recommended_policies"] = None
        state["comparison_table"] = None
        return state

    policy_label = _policy_label(selected_policy)
    coverage_check = evaluate_policy_claim_amount_coverage(
        policy_name=policy_label,
        claimed_amount=claimed_amount,
        treatment_name=_extract_treatment_name(query),
    )

    evidence_lines = []
    for item in coverage_check.get("best_evidence", [])[:3]:
        limit = item.get("limit")
        limit_text = f" (limit: ₹{limit:,.0f})" if isinstance(limit, (int, float)) else ""
        evidence_lines.append(
            f"- Page {item.get('page', 'N/A')}: {item.get('snippet', '').strip()}{limit_text}"
        )

    evidence_block = "\n".join(evidence_lines) if evidence_lines else "- No relevant hospital/surgery claim chunks were found."

    if coverage_check.get("status") == "UNKNOWN":
        state["final_response"] = (
            "### 🧾 Claim Amount Check\n"
            f"- **Policy:** {policy_label}\n"
            f"- **Claim Amount:** ₹{claimed_amount:,.0f}\n"
            "- **Result:** Unable to verify from the available policy chunks.\n\n"
            f"- **Best Supported Coverage:** Not available"
        )
        state["agent_used"] = "ClaimAgent (Amount Verification Missing Evidence)"
    else:
        verdict = coverage_check.get("status", "NO")
        supported_limit = coverage_check.get("supported_limit")
        support_text = f"₹{supported_limit:,.0f}" if isinstance(supported_limit, (int, float)) else "Not available"
        result_text = "YES" if verdict == "YES" else "NO"

        state["final_response"] = (
            "### 🧾 Claim Amount Check\n"
            f"- **Policy:** {policy_label}\n"
            f"- **Claim Amount:** ₹{claimed_amount:,.0f}\n"
            f"- **Result:** {result_text}\n"
            f"- **Best Supported Coverage:** {support_text}\n\n"
        )
        state["agent_used"] = "ClaimAgent (Amount Verification)"

    state["recommended_policies"] = None
    state["comparison_table"] = None
    return state


def _ped_agent_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    policy_catalog = state.get("policy_catalog") or []
    selected_policy = _resolve_policy_from_catalog(
        query=query,
        policy_catalog=policy_catalog,
        filter_company=state.get("filter_company"),
        filter_policy=state.get("filter_policy"),
    )

    if not selected_policy:
        state["final_response"] = (
            "### ⏳ PED Waiting Period\n\n"
            "Please choose a policy from the catalogue first so I can tell you the exact PED waiting period."
        )
        state["agent_used"] = "CoverageAgent (Selection Required)"
        state["recommended_policies"] = None
        state["comparison_table"] = None
        return state

    ped_months = selected_policy.get("ped_waiting_period_months")
    policy_label = _policy_label(selected_policy)
    ped_text = (
        f"{int(ped_months)} months"
        if ped_months is not None
        else "not available in the policy data"
    )

    state["final_response"] = f"### ⏳ PED Waiting Period\n\n{policy_label}: {ped_text}."
    state["agent_used"] = "CoverageAgent (Policy Lookup)"
    state["recommended_policies"] = None
    state["comparison_table"] = None
    return state


def _catalog_agent_node(state: AgentState) -> AgentState:
    policy_catalog = state.get("policy_catalog") or []
    query = state.get("query", "")
    budget = state.get("budget_annual_max")

    if budget is not None:
        try:
            budget_value = float(budget)
            filtered_catalog = [
                policy
                for policy in policy_catalog
                if policy.get("base_annual_premium_estimate") is None
                or float(policy.get("base_annual_premium_estimate")) <= budget_value
            ]
        except Exception:
            filtered_catalog = policy_catalog
    else:
        filtered_catalog = policy_catalog

    if not filtered_catalog:
        state["final_response"] = (
            "### 📚 Policy Catalogue\n"
            "No policies are available in the catalogue right now. Please try refreshing the policy data."
        )
        state["agent_used"] = "CatalogAgent"
        state["recommended_policies"] = None
        state["comparison_table"] = None
        return state

    top_policies = filtered_catalog[:8]
    lines = [
        "### 📚 Policy Catalogue",
        f"Showing {len(top_policies)} policies that match the available catalogue{' and your budget' if budget is not None else ''}.",
        "",
    ]

    for idx, policy in enumerate(top_policies, start=1):
        premium = policy.get("base_annual_premium_estimate")
        description = policy.get("description") or "No detailed description is available in the provided policy data."
        highlights = policy.get("key_highlights") or ""
        lines.extend([
            f"#### {idx}. {policy.get('insurer_name', 'Unknown Insurer')} - {policy.get('policy_name', 'Unknown Policy')}",
            f"- **Description:** {description}",
            f"- **Room Rent:** {policy.get('room_rent_limit') or 'Not available in the provided policy data.'}",
            f"- **PED Waiting:** {policy.get('ped_waiting_period_months') if policy.get('ped_waiting_period_months') is not None else 'Not available in the provided policy data.'} months",
            f"- **Claim Settlement Ratio:** {policy.get('claim_settlement_ratio') if policy.get('claim_settlement_ratio') is not None else 'Not available in the provided policy data.'}%",
            f"- **Est. Annual Premium:** ₹{float(premium):,.0f}" if premium is not None else "- **Est. Annual Premium:** Not available in the provided policy data.",
            f"- **Highlights:** {highlights if highlights else 'No extra highlights available in the provided policy data.'}",
            "",
        ])

    if len(filtered_catalog) > len(top_policies):
        lines.append(f"More policies are available in the full Policy Catalogue view. Search or open the catalogue panel to see all {len(filtered_catalog)} matched plans.")

    state["final_response"] = "\n".join(lines).strip()
    state["agent_used"] = "CatalogAgent"
    state["recommended_policies"] = None
    state["comparison_table"] = None
    return state


def route_intent(state: AgentState) -> str:
    """Conditional routing function returning next agent node key."""
    intent = state.get("intent", "FAQ").upper()
    if state.get("claim_amount") is not None:
        return "claim"
    if intent == "PROFILE":
        return "profile"
    elif intent == "COVERAGE":
        return "coverage"
    elif intent == "COMPARISON":
        return "comparison"
    elif intent == "SALES":
        return "sales"
    elif intent == "PREMIUM":
        return "premium"
    elif intent == "CLAIM":
        return "claim"
    elif intent == "CATALOG":
        return "catalog"
    elif intent == "PED":
        return "ped"
    else:
        return "chat"



def build_health_insurance_graph():
    """Build and compile the LangGraph multi-agent workflow."""
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("router", router_agent_node)
    workflow.add_node("profile", profile_agent_node)
    workflow.add_node("coverage", coverage_agent_node)
    workflow.add_node("comparison", comparison_agent_node)
    workflow.add_node("sales", sales_agent_node)
    workflow.add_node("premium", _premium_agent_node)
    workflow.add_node("claim", _claim_agent_node)
    workflow.add_node("ped", _ped_agent_node)
    workflow.add_node("catalog", _catalog_agent_node)
    workflow.add_node("chat", chat_agent_node)

    # Set Entry Point
    workflow.set_entry_point("router")

    # Add Conditional Edges from Router
    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "profile": "profile",
            "coverage": "coverage",
            "comparison": "comparison",
            "sales": "sales",
            "premium": "premium",
            "claim": "claim",
            "ped": "ped",
            "catalog": "catalog",
            "chat": "chat"
        }
    )

    # Connect leaf nodes to END
    workflow.add_edge("profile", END)
    workflow.add_edge("coverage", END)
    workflow.add_edge("comparison", END)
    workflow.add_edge("sales", END)
    workflow.add_edge("premium", END)
    workflow.add_edge("claim", END)
    workflow.add_edge("ped", END)
    workflow.add_edge("catalog", END)
    workflow.add_edge("chat", END)

    app_graph = workflow.compile()
    logger.info("LangGraph Health Insurance Multi-Agent workflow compiled successfully.")
    return app_graph


# Global Compiled Graph Singleton
agent_graph = build_health_insurance_graph()


def run_agent_workflow(
    query: str,
    messages: List[Dict[str, str]] = None,
    user_profile: Dict[str, Any] = None,
    policy_catalog: List[Dict[str, Any]] = None,
    uploaded_policy_baseline: Dict[str, Any] = None,
    filter_company: str = None,
    filter_policy: str = None,
    claim_amount: float | None = None,
    compare_policy_ids: List[int] | None = None,
) -> AgentState:
    """Convenience execution wrapper for multi-agent graph processing."""
    profile = user_profile or {}
    initial_state: AgentState = {
        "query": query,
        "user_profile": profile,
        "age": profile.get("age"),
        "gender": profile.get("gender"),
        "city": profile.get("city"),
        "coverage_type": profile.get("coverage_type"),
        "sum_insured_preference": profile.get("sum_insured_preference"),
        "budget_annual_max": profile.get("budget_annual_max"),
        "pre_existing_diseases": profile.get("pre_existing_diseases"),
        "messages": messages or [{"role": "user", "content": query}],
        "intent": "FAQ",
        "retrieved_docs": [],
        "sources": [],
        "final_response": "",
        "agent_used": "",
        "recommended_policies": None,
        "comparison_table": None,
        "policy_catalog": policy_catalog or [],
        "uploaded_policy_baseline": uploaded_policy_baseline or {},
        "filter_company": filter_company,
        "filter_policy": filter_policy,
        "claim_amount": claim_amount,
        "compare_policy_ids": compare_policy_ids or [],
    }

    final_output = agent_graph.invoke(initial_state)
    return final_output
