import logging
import json
import re
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


def _normalize_money_requirement(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _display_policy_value(value: Any) -> str:
    if value is None or value == "":
        return "Not available in the provided policy data."
    return str(value)


def _passes_hard_eligibility(policy: Dict[str, Any], budget: float | None, target_sum_insured: float | None) -> bool:
    premium = _normalize_money_requirement(policy.get("est_premium") or policy.get("base_annual_premium_estimate"))
    max_sum_insured = _normalize_money_requirement(policy.get("base_sum_insured_max"))
    if budget is None or target_sum_insured is None or premium is None or max_sum_insured is None:
        return False
    return premium <= budget + 5000 and max_sum_insured >= target_sum_insured


def _build_dynamic_candidate(policy: Dict[str, Any], age: int, budget: float | None, peds: List[str]) -> Dict[str, Any]:
    premium_raw = policy.get("base_annual_premium_estimate")
    max_sum_insured_raw = policy.get("base_sum_insured_max")
    if premium_raw is None or max_sum_insured_raw is None:
        return {}

    premium = float(premium_raw)
    room_rent_limit = policy.get("room_rent_limit") or ""
    restoration_benefit = policy.get("restoration_benefit") or ""
    no_claim_bonus = policy.get("no_claim_bonus") or ""
    base_sum_insured_min = float(policy.get("base_sum_insured_min") or 0.0)
    base_sum_insured_max = float(max_sum_insured_raw)
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
    if age is not None and age <= 35 and ("lock" in no_claim_bonus.lower() or "forever" in restoration_benefit.lower()):
        score += 5
    if age is not None and age >= 60 and co_pay_percentage <= 0:
        score += 3
    if budget is not None:
        distance = abs(premium - budget)
        if premium > budget + 5000:
            score -= 8
        elif premium <= budget:
            score += max(0, 6 - int(distance / 1000))
        else:
            score += max(0, 8 - int(distance / 1000))
    if "unlimited" in description.lower():
        score += 2

    suitable_for = []
    if peds and ped_waiting_period_months <= 36:
        suitable_for.append("Users with pre-existing conditions seeking manageable waiting periods")
    if _is_no_capping(room_rent_limit):
        suitable_for.append("Buyers wanting flexible room category selection")
    if network_hospitals_count >= 12000:
        suitable_for.append("Families wanting a broad cashless hospital network")
    if budget is not None and premium <= budget + 5000:
        suitable_for.append("Budget-conscious buyers staying within your selected premium window")
    if not suitable_for:
        suitable_for.append("Users looking for a balanced health insurance option")

    riders = []
    if peds:
        riders.append("PED Reduction Rider")
    if age is not None and age < 45:
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
        "base_sum_insured_min": base_sum_insured_min,
        "base_sum_insured_max": base_sum_insured_max,
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
            "base_sum_insured_min": 500000,
            "base_sum_insured_max": 10000000,
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
            "base_sum_insured_min": 500000,
            "base_sum_insured_max": 10000000,
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
            "base_sum_insured_min": 500000,
            "base_sum_insured_max": 10000000,
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
            "base_sum_insured_min": 500000,
            "base_sum_insured_max": 10000000,
            "base_score": 84,
            "highlights": ["100% Automatic Restore", "14,000+ Cashless Hospital Network", "Free Annual Health Checkup"],
            "suitable_for": "Budget-conscious families wanting wide hospital network access.",
            "riders": ["Hospital Cash Rider", "Star Outpatient Consult Cover"]
        }
    ]


from app.config import settings
from app.rag.vector_store import vector_store_manager

def sales_agent_node(state: AgentState) -> AgentState:
    """
    Sales & Actuarial Agent: Evaluates user query, computes policy match scores,
    calculates premium estimates, and synthesizes dynamic LLM responses using RAG context.
    """
    query = state.get("query", "").strip()
    profile = state.get("user_profile", {}) or {}
    age = state.get("age", profile.get("age", 30))
    gender = state.get("gender", profile.get("gender"))
    city = state.get("city", profile.get("city"))
    coverage_type = state.get("coverage_type", profile.get("coverage_type"))
    sum_insured_preference = state.get("sum_insured_preference", profile.get("sum_insured_preference"))
    budget = _normalize_money_requirement(state.get("budget_annual_max", profile.get("budget_annual_max")))
    target_sum_insured = _normalize_money_requirement(sum_insured_preference)
    peds = state.get("pre_existing_diseases", profile.get("pre_existing_diseases", []))
    if isinstance(peds, str):
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []

    policy_catalog = state.get("policy_catalog") or []

    candidates = []
    if policy_catalog:
        for policy in policy_catalog:
            candidate = _build_dynamic_candidate(policy, age, budget, peds)
            if candidate and _passes_hard_eligibility(candidate, budget, target_sum_insured):
                candidates.append(candidate)
    else:
        candidates = _static_candidates()
        candidates = [plan for plan in candidates if _passes_hard_eligibility(plan, budget, target_sum_insured)]

    if not candidates:
        state["final_response"] = (
            "### 🛡️ No Eligible Policies Found\n"
            "No health insurance policy satisfies both your maximum annual premium budget and your sum insured preference. "
            "Please adjust your saved profile requirements to see matching plans."
        )
        state["recommended_policies"] = []
        state["agent_used"] = "SalesAgent (AI Actuarial & RAG)"
        return state

    scored = []
    for plan in candidates:
        premium_bonus = 0
        premium = float(plan.get("est_premium") or 0.0)

        if budget is not None:
            premium_distance = abs(premium - float(budget))
            if premium <= budget:
                premium_bonus += max(0, 10 - int(premium_distance / 500))
            elif premium <= budget + 5000:
                premium_bonus += max(0, 12 - int(premium_distance / 500))

        sum_insured_bonus = 0
        if target_sum_insured:
            min_si = float(plan.get("base_sum_insured_min") or 0.0)
            max_si = float(plan.get("base_sum_insured_max") or 0.0)
            if min_si and max_si and min_si <= float(target_sum_insured) <= max_si:
                sum_insured_bonus += 8
            else:
                sum_insured_bonus -= 4

        plan["match_score"] = min(99, max(60, int(plan["base_score"] + premium_bonus + sum_insured_bonus)))
        scored.append(plan)

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top_plans = scored[:4]

    # Perform policy-specific RAG search for each recommended policy so facts stay isolated.
    policy_contexts = []
    for plan in top_plans:
        retrieved = vector_store_manager.query(
            query_text=f"{plan['policy_name']} {query}",
            n_results=3,
            company_filter=plan.get("insurer_name"),
            policy_filter=plan.get("policy_name"),
        )
        policy_contexts.append({
            "policy_name": plan.get("policy_name"),
            "insurer_name": plan.get("insurer_name"),
            "structured_policy": plan,
            "retrieved_context": [
                {
                    "company": doc["company"],
                    "policy_name": doc["policy_name"],
                    "page": doc["page"],
                    "chunk_id": doc["chunk_id"],
                    "citation": doc["citation"],
                    "snippet": doc["content"][:250],
                }
                for doc in retrieved
            ],
        })

    # LLM Dynamic Answer Generation
    answer = ""
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
        try:
            from importlib import import_module

            ChatOpenAI = import_module("langchain_openai").ChatOpenAI
            llm_kwargs = {
                "model": settings.effective_model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "temperature": 0.2
            }
            if settings.OPENAI_BASE_URL and len(settings.OPENAI_BASE_URL.strip()) > 5:
                llm_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
            llm = ChatOpenAI(**llm_kwargs)

            profile_context = {
                "age": age,
                "gender": gender,
                "city": city,
                "coverage_type": coverage_type,
                "sum_insured_preference": sum_insured_preference,
                "budget_annual_max": budget,
                "pre_existing_diseases": peds,
            }

            prompt = (
                "You are a strict health insurance sales and recommendation assistant. Answer only recommendation and plan-selection questions. "
                "Do not answer premium calculators, claim eligibility, or generic coverage clause questions unless the request is clearly about choosing the best policy.\n\n"
                f"User Question: {query}\n"
                f"User Profile (structured): {json.dumps(profile_context, indent=2)}\n"
                f"Available Policy Catalog (Structured, Eligibility-Filtered):\n{json.dumps(top_plans, indent=2)}\n\n"
                f"Policy-Specific RAG Context (do not mix facts across policies):\n{json.dumps(policy_contexts, indent=2)}\n\n"
                "CRITICAL FORMATTING INSTRUCTIONS FOR PRODUCTION VISUALIZATION:\n"
                "- DO NOT use raw hash header symbols (like #, ##, ###). Use clean bold section titles (e.g. **Top Recommended Policies**).\n"
                "- DO NOT include bracketed citations, page numbers, or policy references in brackets (such as [Company: X, Policy: Y, Page: Z]). Present all details directly in natural, professional prose.\n"
                "- Structure your answer using clean paragraphs, bullet points (- point), and structured markdown tables (| Column 1 | Column 2 |).\n"
                "- If the user asks for recommendations, rank the top policies matching their profile with match scores and key features.\n"
                "- If the user asks for pricing or premium calculation, hand off to the premium calculator workflow instead of improvising a quote here.\n"
                "- Never transfer facts between policies. Use only the structured data and the policy-specific retrieved context for the matching policy.\n"
                "- Make the formatting executive-ready, highly readable, and professional."

            )
            res = llm.invoke(prompt)
            answer = res.content.strip()
        except Exception as e:
            logger.warning(f"SalesAgent LLM call failed: {e}")


    if not answer:
        # Fallback response generator
        response_lines = [
            "### 🛡️ Policy Recommendation Summary",
            f"Based on your profile (Age {age}, Budget ₹{budget:,.0f}, PED: {', '.join(peds) if peds else 'None'}), "
            "here are your top matched health insurance policies:\n"
        ]

        if any(value is not None for value in [gender, city, coverage_type, sum_insured_preference]):
            response_lines.append(
                f"Profile context: Gender={gender or 'Not specified'}, City={city or 'Not specified'}, Coverage Type={coverage_type or 'Not specified'}, Sum Insured Preference=₹{float(sum_insured_preference or 0):,.0f}."
            )

        for idx, plan in enumerate(top_plans, start=1):
            response_lines.append(f"#### {idx}. {plan['insurer_name']} - {plan['policy_name']} (Match Score: {plan['match_score']}%)")
            response_lines.append(f"- **Est. Annual Premium:** ₹{plan['est_premium']:,.0f}" if plan.get("est_premium") is not None else "- **Est. Annual Premium:** Not available in the provided policy data.")
            response_lines.append(f"- **Best Suited For:** {plan['suitable_for']}")
            response_lines.append(f"- **Key Features:** {', '.join(plan['highlights'])}")
            response_lines.append(f"- **Recommended Riders:** {', '.join(plan['riders'])}\n")

        response_lines.append("Would you like to compare these plans, estimate a premium, or check claim eligibility next?")
        answer = "\n".join(response_lines)

    state["final_response"] = answer
    state["recommended_policies"] = top_plans
    state["agent_used"] = "SalesAgent (AI Actuarial & RAG)"
    return state

