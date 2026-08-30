import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.models.schemas import (
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
    revoke_jti,
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
def logout(body: RefreshRequest):
    """Revoke the presented refresh token so it can no longer be exchanged."""
    payload = decode_token(body.refresh_token)
    if payload and payload.get("jti"):
        revoke_jti(payload["jti"])
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
