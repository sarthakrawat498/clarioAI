import logging
import re
from typing import Dict, Any, List, Optional
from app.schemas.claim import ClaimCheckRequest, ClaimCheckResponse
from app.database import SessionLocal
from app.models.policy import PolicyCatalog
from app.rag.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


_RELEVANT_COVERAGE_KEYWORDS = (
    "hospital",
    "hospitalization",
    "surgery",
    "treatment",
    "claim",
    "covered",
    "coverage",
    "sum insured",
    "room rent",
    "cashless",
    "reimburse",
    "inpatient",
)


def _policy_label(policy: PolicyCatalog) -> str:
    return f"{policy.insurer_name} {policy.policy_name}".strip()


def _find_policy_record(policy_name: str) -> Optional[PolicyCatalog]:
    db = SessionLocal()
    try:
        normalized_target = " ".join((policy_name or "").lower().split())
        if not normalized_target:
            return None

        policies = db.query(PolicyCatalog).all()
        for policy in policies:
            label = " ".join(_policy_label(policy).lower().split())
            bare_name = " ".join((policy.policy_name or "").lower().split())
            insurer = " ".join((policy.insurer_name or "").lower().split())
            if normalized_target == label or normalized_target == bare_name:
                return policy
            if insurer and bare_name and insurer in normalized_target and bare_name in normalized_target:
                return policy
        return None
    finally:
        db.close()


def _format_money(value: float) -> str:
    return f"₹{value:,.0f}"


def _parse_amount_token(token: str, unit: str | None = None) -> Optional[float]:
    if not token:
        return None
    try:
        value = float(token.replace(",", ""))
    except ValueError:
        return None

    unit_normalized = (unit or "").lower().strip()
    if unit_normalized in {"crore", "crores", "cr"}:
        value *= 10000000
    elif unit_normalized in {"lakh", "lakhs", "lac", "lacs"}:
        value *= 100000
    elif unit_normalized in {"k", "thousand", "thousands"}:
        value *= 1000
    return value


def _extract_amounts(text: str) -> List[float]:
    if not text:
        return []

    amounts: List[float] = []
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(crores?|cr|lakhs?|lac|lacs|k|thousand|thousands)?",
        r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(crores?|cr|lakhs?|lac|lacs|k|thousand|thousands)\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount = _parse_amount_token(match.group(1), match.group(2) if match.lastindex and match.lastindex >= 2 else None)
            if amount is not None:
                amounts.append(amount)

    return amounts


def _is_full_sum_insured_text(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in [
            "full sum insured",
            "up to the sum insured",
            "up to sum insured",
            "100% sum insured",
            "no capping",
            "no room rent capping",
            "covered up to base sum insured",
            "up to base sum insured",
        ]
    )


def _infer_chunk_limit(chunk_text: str, policy: Optional[PolicyCatalog]) -> Optional[float]:
    if not chunk_text:
        return None

    amounts = _extract_amounts(chunk_text)
    candidates = [amount for amount in amounts if amount > 0]
    lowered = chunk_text.lower()

    if _is_full_sum_insured_text(chunk_text) and policy and policy.base_sum_insured_max:
        candidates.append(float(policy.base_sum_insured_max))

    if "up to" in lowered or "limited to" in lowered or "maximum" in lowered or "cap" in lowered:
        if candidates:
            return max(candidates)

    if "covered" in lowered and candidates:
        return max(candidates)

    if _is_full_sum_insured_text(chunk_text) and policy and policy.base_sum_insured_max:
        return float(policy.base_sum_insured_max)

    return max(candidates) if candidates else None


def evaluate_policy_claim_amount_coverage(
    policy_name: str,
    claimed_amount: float,
    treatment_name: str = "Hospitalization",
) -> Dict[str, Any]:
    """
    Checks whether a user-entered hospital/surgery amount is supported by policy wording.

    Returns a compact verdict with the strongest supported ceiling and the chunks used.
    """
    policy = _find_policy_record(policy_name)
    policy_filter = policy.policy_name if policy else policy_name
    company_filter = policy.insurer_name if policy else None

    query_text = (
        f"{policy_name} {treatment_name} hospital surgery coverage amount limit sum insured room rent claim "
        f"{_format_money(claimed_amount)}"
    )
    retrieved_docs = vector_store_manager.query(
        query_text=query_text,
        n_results=8,
        company_filter=company_filter,
        policy_filter=policy_filter,
    )

    evidence_chunks = []
    candidate_limits = []

    for doc in retrieved_docs:
        content = doc.get("content", "")
        if not any(keyword in content.lower() for keyword in _RELEVANT_COVERAGE_KEYWORDS):
            continue

        inferred_limit = _infer_chunk_limit(content, policy)
        if inferred_limit is not None:
            candidate_limits.append(inferred_limit)

        evidence_chunks.append(
            {
                "company": doc.get("company", "Unknown"),
                "policy_name": doc.get("policy_name", policy_name),
                "page": doc.get("page", "N/A"),
                "chunk_id": doc.get("chunk_id", ""),
                "snippet": content[:260].strip(),
                "limit": inferred_limit,
                "citation": doc.get("citation"),
            }
        )

    if not candidate_limits:
        return {
            "status": "UNKNOWN",
            "covered": None,
            "policy_name": policy_name,
            "claimed_amount": claimed_amount,
            "supported_limit": None,
            "best_evidence": [],
            "explanation": (
                "I could not find a reliable hospital/surgery coverage chunk for this policy, so I cannot verify the amount safely."
            ),
        }

    supported_limit = max(candidate_limits)
    covered = claimed_amount <= supported_limit

    return {
        "status": "YES" if covered else "NO",
        "covered": covered,
        "policy_name": policy_name,
        "claimed_amount": claimed_amount,
        "supported_limit": supported_limit,
        "best_evidence": evidence_chunks,
        "policy_record": policy,
        "explanation": (
            f"The strongest supported hospital/surgery limit found for this policy is {_format_money(supported_limit)}."
        ),
    }


def evaluate_claim_eligibility(req: ClaimCheckRequest) -> ClaimCheckResponse:
    """
    Evaluates treatment claim eligibility against policy terms, waiting periods,
    room rent sub-limits, and co-payment clauses.
    """
    claimed = req.claimed_amount
    approved = claimed
    deductions = 0.0
    warnings = []
    status = "Eligible"

    # Query RAG for grounding citations on treatment
    rag_docs = vector_store_manager.query(
        query_text=f"{req.treatment_name} {req.policy_name} waiting period room rent co-pay exclusions",
        n_results=2,
        policy_filter=req.policy_name if "optima" in req.policy_name.lower() or "care" in req.policy_name.lower() else None
    )

    citations = [
        {
            "company": d["company"],
            "policy_name": d["policy_name"],
            "page": d["page"],
            "citation": d["citation"],
            "snippet": d["content"][:150] + "..."
        }
        for d in rag_docs
    ]

    # Rule 1: Initial 30 days waiting period
    if req.policy_holding_duration_months < 1:
        status = "Excluded"
        approved = 0.0
        deductions = claimed
        warnings.append("Policy is under the initial 30-day waiting period. Claims for non-accidental illnesses are excluded.")
        explanation = "Claim rejected due to 30-day initial waiting period clause."
        return ClaimCheckResponse(
            status=status,
            estimated_approved_amount=0.0,
            deductions=claimed,
            coverage_breakdown={"Base Claim": claimed, "Approved": 0.0, "Deduction": claimed},
            warnings=warnings,
            citations=citations,
            explanation=explanation
        )

    # Rule 2: Pre-Existing Diseases (PED) waiting period
    if req.is_pre_existing_condition:
        if not req.ped_disclosed_at_purchase:
            status = "Excluded"
            approved = 0.0
            deductions = claimed
            warnings.append("Non-disclosure of pre-existing condition at inception leads to claim rejection and policy cancellation under Utmost Good Faith principles.")
            explanation = "Claim rejected due to non-disclosure of Pre-Existing Disease."
            return ClaimCheckResponse(
                status=status,
                estimated_approved_amount=0.0,
                deductions=claimed,
                coverage_breakdown={"Base Claim": claimed, "Approved": 0.0, "Deduction": claimed},
                warnings=warnings,
                citations=citations,
                explanation=explanation
            )
        elif req.policy_holding_duration_months < 36:
            status = "Excluded"
            approved = 0.0
            deductions = claimed
            warnings.append(f"Pre-existing condition requires 36 months waiting period. Current holding duration: {req.policy_holding_duration_months} months.")
            explanation = "Claim currently excluded under 36-month Pre-Existing Disease waiting period."
            return ClaimCheckResponse(
                status=status,
                estimated_approved_amount=0.0,
                deductions=claimed,
                coverage_breakdown={"Base Claim": claimed, "Approved": 0.0, "Deduction": claimed},
                warnings=warnings,
                citations=citations,
                explanation=explanation
            )

    # Rule 3: Specific Surgery sub-limits (e.g., Cataract)
    if "cataract" in req.treatment_name.lower():
        if req.policy_holding_duration_months < 24:
            status = "Excluded"
            approved = 0.0
            deductions = claimed
            warnings.append("Cataract surgery requires a mandatory 24-month specific disease waiting period.")
            explanation = "Excluded under 2-year specific procedure waiting period."
            return ClaimCheckResponse(
                status=status,
                estimated_approved_amount=0.0,
                deductions=claimed,
                coverage_breakdown={"Base Claim": claimed, "Approved": 0.0, "Deduction": claimed},
                warnings=warnings,
                citations=citations,
                explanation=explanation
            )
        # Apply Cataract capping for Star Optima Restore
        if "star" in req.policy_name.lower():
            cataract_cap = 40000.0
            if claimed > cataract_cap:
                approved = cataract_cap
                deductions = claimed - cataract_cap
                status = "Partially Eligible"
                warnings.append(f"Star Health Optima Restore caps Cataract surgery at ₹40,000 per eye.")

    # Rule 4: Room Rent Proportionate Deductions
    if req.room_category_chosen.lower() in ["suite", "deluxe room"]:
        if "care supreme" not in req.policy_name.lower(): # Care Supreme has no room capping
            room_deduction = claimed * 0.25 # 25% proportionate penalty
            approved -= room_deduction
            deductions += room_deduction
            status = "Partially Eligible"
            warnings.append(f"Choosing a '{req.room_category_chosen}' beyond Single Private Room triggered a 25% proportionate deduction on associate medical charges.")

    # Rule 5: Non-Network Hospital Co-pay penalty
    if req.hospital_type.lower() == "non-network":
        co_pay_deduction = approved * 0.10 # 10% co-pay for non-network
        approved -= co_pay_deduction
        deductions += co_pay_deduction
        if status == "Eligible":
            status = "Partially Eligible"
        warnings.append("A 10% co-payment was applied for treatment at a Non-Network hospital.")

    approved = max(0.0, round(approved, 2))
    deductions = round(deductions, 2)

    explanation = (
        f"Claim for '{req.treatment_name}' evaluated under '{req.policy_name}'. "
        f"Approved Amount: ₹{approved:,.2f} | Out-of-pocket Deductions: ₹{deductions:,.2f}."
    )

    return ClaimCheckResponse(
        status=status,
        estimated_approved_amount=approved,
        deductions=deductions,
        coverage_breakdown={
            "Base Claim Amount": claimed,
            "Approved Amount": approved,
            "Total Out-of-Pocket Deduction": deductions
        },
        warnings=warnings,
        citations=citations,
        explanation=explanation
    )
