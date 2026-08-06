import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.policy import ClaimCheckLog
from app.schemas.claim import ClaimCheckRequest, ClaimCheckResponse
from app.services.claim_service import evaluate_claim_eligibility

router = APIRouter(prefix="/claims", tags=["Claim Eligibility Diagnostics"])


@router.post("/check-eligibility", response_model=ClaimCheckResponse)
def check_claim(
    req: ClaimCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Diagnose treatment claim eligibility, out-of-pocket deductions, and grounded policy citations."""
    res = evaluate_claim_eligibility(req)

    # Save Log
    log = ClaimCheckLog(
        user_id=current_user.id,
        policy_name=req.policy_name,
        hospital_name=req.hospital_name,
        hospital_type=req.hospital_type,
        treatment_name=req.treatment_name,
        claimed_amount=req.claimed_amount,
        policy_duration_months=req.policy_holding_duration_months,
        is_ped_related=req.is_pre_existing_condition,
        approval_eligibility=res.status,
        estimated_approved_amount=res.estimated_approved_amount,
        deduction_reason=", ".join(res.warnings) if res.warnings else "None",
        citations=json.dumps(res.citations)
    )
    db.add(log)
    db.commit()

    return res
