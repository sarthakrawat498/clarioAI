import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.policy import PolicyCompareRequest, PolicyCompareResponse, PolicyOut
from app.services.policy_service import get_policy_by_id, get_all_policies
from app.services.profile_service import get_user_profile
from app.agents.comparison_agent import COMPARISON_BENCHMARKS

router = APIRouter(prefix="/compare", tags=["Policy Comparison Matrix"])


@router.post("", response_model=PolicyCompareResponse)
def compare_policies(
    req: PolicyCompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate side-by-side comparative analysis matrix for selected policy IDs."""
    profile = get_user_profile(db, current_user.id)
    budget = profile.budget_annual_max

    if budget is not None:
        rejected = []
        for pid in req.policy_ids:
            p = get_policy_by_id(db, pid)
            if p and p.base_annual_premium_estimate is not None and p.base_annual_premium_estimate > budget:
                rejected.append(f"{p.insurer_name} {p.policy_name}")
        if rejected:
            raise HTTPException(
                status_code=400,
                detail=f"Selected policies exceed your budget of ₹{budget:,.0f}: {', '.join(rejected)}.",
            )

    selected_policies = []
    for pid in req.policy_ids:
        p = get_policy_by_id(db, pid)
        if p:
            selected_policies.append(p)

    if len(selected_policies) < 2:
        raise HTTPException(status_code=400, detail="Must select at least 2 valid policies to compare.")

    matrix = {}
    params = [
        ("Insurer", "insurer_name"),
        ("Sum Insured Options", "sum_insured_options"),
        ("Room Rent Category", "room_rent_limit"),
        ("Co-Pay Percentage", "co_pay_percentage"),
        ("PED Waiting Period (Months)", "ped_waiting_period_months"),
        ("Restoration Benefit", "restoration_benefit"),
        ("No Claim Bonus", "no_claim_bonus"),
        ("Pre / Post Hospitalization Days", "pre_post_days"),
        ("Network Hospitals", "network_hospitals_count"),
        ("Claim Settlement Ratio (%)", "claim_settlement_ratio"),
        ("Estimated Base Premium", "base_annual_premium_estimate")
    ]

    for label, attr in params:
        matrix[label] = {}
        for p in selected_policies:
            if attr == "sum_insured_options":
                min_l = f"₹{p.base_sum_insured_min/100000:,.0f} Lakhs" if p.base_sum_insured_min >= 100000 else f"₹{p.base_sum_insured_min:,.0f}"
                max_c = f"₹{p.base_sum_insured_max/10000000:,.0f} Crore" if p.base_sum_insured_max >= 10000000 else f"₹{p.base_sum_insured_max/100000:,.0f} Lakhs"
                val = f"{min_l} to {max_c} (Flexible)"
            elif attr == "pre_post_days":
                val = f"{p.pre_hospitalization_days} Days / {p.post_hospitalization_days} Days"

            elif attr == "co_pay_percentage":
                val = f"{p.co_pay_percentage}%"
            elif attr == "claim_settlement_ratio":
                val = f"{p.claim_settlement_ratio}%"
            elif attr == "base_annual_premium_estimate":
                val = f"₹{p.base_annual_premium_estimate:,.0f} / yr"
            else:
                val = getattr(p, attr, "N/A")
            matrix[label][p.policy_name] = val

    verdict = (
        f"Compared {len(selected_policies)} policies. "
        f"For highest feature coverage with instant 2x sum insured, choose '{selected_policies[0].policy_name}'. "
        f"For high cumulative bonus accumulation, consider '{selected_policies[1].policy_name}'."
    )

    policies_out = [PolicyOut.model_validate(p) for p in selected_policies]

    return PolicyCompareResponse(
        policies=policies_out,
        matrix=matrix,
        verdict=verdict
    )
