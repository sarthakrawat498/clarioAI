import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.profile_service import get_user_profile
from app.services.policy_service import get_all_policies, serialize_policy_catalog
from app.agents.sales_agent import sales_agent_node

router = APIRouter(prefix="/recommendations", tags=["Smart Policy Recommendations"])


@router.get("", response_model=RecommendationResponse)
def get_recommendations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Generate smart policy recommendations scored against user profile."""
    profile_obj = get_user_profile(db, current_user.id)
    peds = profile_obj.pre_existing_diseases
    if isinstance(peds, str):
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []

    profile_dict = {
        "age": profile_obj.age,
        "city_tier": profile_obj.city_tier,
        "pre_existing_diseases": peds,
        "tobacco_user": profile_obj.tobacco_user,
        "coverage_type": profile_obj.coverage_type,
        "family_members_count": profile_obj.family_members_count,
        "sum_insured_preference": profile_obj.sum_insured_preference,
        "budget_annual_max": profile_obj.budget_annual_max
    }

    policy_catalog = serialize_policy_catalog(get_all_policies(db, profile_obj.budget_annual_max))

    state_input = {"query": "recommend best health policy for my profile", "user_profile": profile_dict, "policy_catalog": policy_catalog}
    sales_output = sales_agent_node(state_input)

    top_recs = sales_output.get("recommended_policies", [])

    cards = []
    for r in top_recs:
        cards.append({
            "policy_id": r["policy_id"],
            "insurer_name": r["insurer_name"],
            "policy_name": r["policy_name"],
            "match_score": r["match_score"],
            "estimated_annual_premium": r["est_premium"],
            "key_features": r["highlights"],
            "why_recommended": r["suitable_for"],
            "suitable_for": r["suitable_for"],
            "recommended_riders": r["riders"]
        })

    return RecommendationResponse(
        user_profile_summary=profile_dict,
        top_recommendations=cards,
        general_advice="Our AI multi-attribute scoring model evaluated room rent capping, PED waiting period clauses, and premium affordability against your health profile."
    )
