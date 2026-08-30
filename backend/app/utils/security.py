from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory revoked-token store (by JWT id). Fine for a single-process
# deployment / demo; back this with Redis for a multi-process rollout.
_REVOKED_JTIS: set[str] = set()


def revoke_jti(jti: str) -> None:
    if jti:
        _REVOKED_JTIS.add(jti)


def is_revoked(jti: Optional[str]) -> bool:
    return bool(jti) and jti in _REVOKED_JTIS


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str, role: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "jti": str(uuid4()),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, role: str) -> str:
    return _create_token(
        str(user_id),
        role,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID, role: str) -> str:
    return _create_token(
        str(user_id),
        role,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
    if is_revoked(payload.get("jti")):
        return None
    return payload
