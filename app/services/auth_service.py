import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException
from app.services.profile_service import snapshot_profile

logger = logging.getLogger(__name__)


def register_user(db: Session, user_in: UserCreate) -> User:
    """Register a new user and initialize a default profile."""
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise UserAlreadyExistsException()

    user = User(
        full_name=user_in.full_name,
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        phone_number=user_in.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize empty profile for new user
    default_profile = Profile(
        user_id=user.id,
        age=30,
        gender=None,
        city=None,
        city_tier=None,
        pre_existing_diseases="[]",
        coverage_type=None,
        family_members_count=None,
        sum_insured_preference=None,
        budget_annual_max=None,
        tobacco_user=False
    )
    db.add(default_profile)
    db.commit()
    db.refresh(default_profile)

    snapshot_profile(db, user.id, default_profile)
    db.commit()

    logger.info(f"Successfully registered new user: {user.email}")
    return user


def authenticate_user(db: Session, email: str, password: str) -> dict:
    """Authenticate user credentials and return access token response."""
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise InvalidCredentialsException()
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()

    token = create_access_token(subject=user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email
    }
