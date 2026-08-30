import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.utils.security import decode_token

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


ROLE_PERMISSIONS = {
    "OFFICER": [
        "scan:create",
        "scan:read_own",
        "report:read_own",
        "report:download_own",
        "product:read",
    ],
    "SUPERVISOR": [
        "scan:create",
        "scan:read_all",
        "report:read_all",
        "report:download_all",
        "product:read",
        "analytics:read",
        "violation:assign",
    ],
    "ADMIN": ["*", "user:manage", "rule:configure", "analytics:export"],
    "VIEWER": ["scan:read_all", "report:read_all", "analytics:read"],
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    try:
        sub = uuid.UUID(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )
    user = db.query(User).filter(User.id == sub).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )
    return user


def require_permission(permission: str):
    def _dependency(user: User = Depends(get_current_user)) -> User:
        perms = ROLE_PERMISSIONS.get(user.role, [])
        if "*" not in perms and permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return _dependency
