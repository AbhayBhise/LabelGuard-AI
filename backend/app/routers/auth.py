import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.models.schemas import (
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    Token,
    UserOut,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> Token:
    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(
        body.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User deactivated"
        )
    return _token_response(user)


@router.post("/google", response_model=Token)
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    # TODO: verify Google ID token against GOOGLE_CLIENT_ID via google auth lib
    payload = decode_token(body.google_id_token) if body.google_id_token else None
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account linked to this Google email",
        )
    return _token_response(user)


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    try:
        sub = uuid.UUID(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    user = db.query(User).filter(User.id == sub).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return _token_response(user)


@router.post("/logout")
def logout():
    # TODO: invalidate refresh token in Redis/deny-list
    return {"detail": "Logged out"}


@router.post("/register", response_model=UserOut, status_code=201)
def register(user_data: dict, db: Session = Depends(get_db)):
    email = user_data.get("email", "").lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        name=user_data.get("name", ""),
        email=email,
        role=user_data.get("role", "OFFICER"),
        state=user_data.get("state"),
        district=user_data.get("district"),
        department=user_data.get("department"),
        hashed_password=hash_password(user_data.get("password", "")),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
