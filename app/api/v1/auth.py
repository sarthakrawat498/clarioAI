from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.services.auth_service import register_user, authenticate_user
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    return register_user(db, user_in)


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and obtain JWT token (supports both JSON body and OAuth2 Form Data)."""
    email = None
    password = None

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            email = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            pass

    if not email or not password:
        raise HTTPException(status_code=422, detail="Email and Password are required")

    return authenticate_user(db, str(email), str(password))



@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
