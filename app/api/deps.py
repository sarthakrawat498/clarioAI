from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """Dependency to retrieve currently authenticated JWT user.
    
    Requires a valid Bearer token. If demo mode is enabled, falls back to demo user
    when no token is provided.
    """
    from app.config import settings
    
    if not token:
        # Demo mode fallback (must be explicitly enabled)
        if settings.ENABLE_DEMO_MODE:
            user = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
            if not user:
                from app.core.security import get_password_hash
                user = User(
                    full_name="Demo User",
                    email=settings.DEMO_USER_EMAIL,
                    hashed_password=get_password_hash(settings.DEMO_USER_PASSWORD),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        else:
            # Authentication required - no token provided
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide a valid bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
