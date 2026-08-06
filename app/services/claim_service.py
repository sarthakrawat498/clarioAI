import logging
from typing import Dict, Any
from app.schemas.claim import ClaimCheckRequest, ClaimCheckResponse
from app.rag.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


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
