import json
import logging
from sqlalchemy.orm import Session
from app.models.profile import Profile, ProfileSnapshot
from app.schemas.profile import ProfileUpdate
from app.core.exceptions import EntityNotFoundException

logger = logging.getLogger(__name__)


def _profile_to_dict(profile: Profile) -> dict:
    peds = profile.pre_existing_diseases
    if isinstance(peds, str):
        try:
            peds = json.loads(peds)
        except Exception:
            peds = [peds] if peds else []

    return {
        "age": profile.age,
        "gender": profile.gender,
        "city": profile.city,
        "city_tier": profile.city_tier,
        "pre_existing_diseases": peds or [],
        "tobacco_user": profile.tobacco_user,
        "bmi": profile.bmi,
        "coverage_type": profile.coverage_type,
        "family_members_count": profile.family_members_count,
        "sum_insured_preference": profile.sum_insured_preference,
        "budget_annual_max": profile.budget_annual_max,
        "preferred_room_type": profile.preferred_room_type,
    }


def get_latest_profile_snapshot(db: Session, user_id: int) -> ProfileSnapshot | None:
    return (
        db.query(ProfileSnapshot)
        .filter(ProfileSnapshot.user_id == user_id)
        .order_by(ProfileSnapshot.created_at.desc(), ProfileSnapshot.id.desc())
        .first()
    )


def get_profile_snapshot_by_id(db: Session, user_id: int, snapshot_id: int) -> ProfileSnapshot | None:
    return (
        db.query(ProfileSnapshot)
        .filter(ProfileSnapshot.user_id == user_id, ProfileSnapshot.id == snapshot_id)
        .first()
    )


def snapshot_profile(db: Session, user_id: int, profile: Profile) -> ProfileSnapshot:
    snapshot = ProfileSnapshot(user_id=user_id, profile_data=json.dumps(_profile_to_dict(profile)))
    db.add(snapshot)
    db.flush()
    return snapshot


def get_user_profile(db: Session, user_id: int) -> Profile:
    """Retrieve user profile by user_id."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        # Create default if missing
        profile = Profile(user_id=user_id, age=30)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_user_profile(db: Session, user_id: int, profile_in: ProfileUpdate) -> Profile:
    """Update profile parameters."""
    profile = get_user_profile(db, user_id)
    
    data = profile_in.model_dump(exclude_unset=True)
    if "pre_existing_diseases" in data and isinstance(data["pre_existing_diseases"], list):
        data["pre_existing_diseases"] = json.dumps(data["pre_existing_diseases"])

    for field, val in data.items():
        if hasattr(profile, field) and val is not None:
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    snapshot_profile(db, user_id, profile)
    db.commit()
    logger.info(f"Updated profile for user_id: {user_id}")
    return profile
