import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileOut, ProfileUpdate
from app.services.profile_service import get_user_profile, update_user_profile, get_latest_profile_snapshot

router = APIRouter(prefix="/profile", tags=["User Profile"])


@router.get("", response_model=ProfileOut)
def read_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Retrieve profile for the logged in user."""
    p = get_user_profile(db, current_user.id)
    latest_snapshot = get_latest_profile_snapshot(db, current_user.id)
    # Parse pre_existing_diseases JSON string if needed
    peds = p.pre_existing_diseases
    if isinstance(peds, str):
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []
            
    return ProfileOut(
        id=p.id,
        user_id=p.user_id,
        active_profile_session_id=latest_snapshot.id if latest_snapshot else None,
        age=p.age,
        gender=p.gender,
        city=p.city,
        city_tier=p.city_tier,
        pre_existing_diseases=peds,
        tobacco_user=p.tobacco_user,
        bmi=p.bmi,
        coverage_type=p.coverage_type,
        family_members_count=p.family_members_count,
        sum_insured_preference=p.sum_insured_preference,
        budget_annual_max=p.budget_annual_max,
        preferred_room_type=p.preferred_room_type
    )


@router.put("", response_model=ProfileOut)
def update_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update profile attributes for current user."""
    p = update_user_profile(db, current_user.id, profile_in)
    latest_snapshot = get_latest_profile_snapshot(db, current_user.id)
    peds = p.pre_existing_diseases
    if isinstance(peds, str):
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []

    return ProfileOut(
        id=p.id,
        user_id=p.user_id,
        active_profile_session_id=latest_snapshot.id if latest_snapshot else None,
        age=p.age,
        gender=p.gender,
        city=p.city,
        city_tier=p.city_tier,
        pre_existing_diseases=peds,
        tobacco_user=p.tobacco_user,
        bmi=p.bmi,
        coverage_type=p.coverage_type,
        family_members_count=p.family_members_count,
        sum_insured_preference=p.sum_insured_preference,
        budget_annual_max=p.budget_annual_max,
        preferred_room_type=p.preferred_room_type
    )
