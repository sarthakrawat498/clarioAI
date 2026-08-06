import json
import logging
from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate
from app.core.exceptions import EntityNotFoundException

logger = logging.getLogger(__name__)


def get_user_profile(db: Session, user_id: int) -> Profile:
    """Retrieve user profile by user_id."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        # Create default if missing
        profile = Profile(user_id=user_id)
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
    logger.info(f"Updated profile for user_id: {user_id}")
    return profile
