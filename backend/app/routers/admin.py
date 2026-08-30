import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import ComplianceRule, User
from app.db.session import get_db
from app.deps import get_current_user, require_permission
from app.utils.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("user:manage")),
):
    users = db.query(User).all()
    return [
        {
            "id": str(u.id), "name": u.name, "email": u.email,
            "role": u.role, "state": u.state, "district": u.district,
            "is_active": u.is_active,
        }
        for u in users
    ]


@router.post("/users", status_code=201)
def create_user(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("user:manage")),
):
    email = payload.get("email", "").lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    u = User(
        name=payload.get("name", ""),
        email=email,
        role=payload.get("role", "OFFICER"),
        state=payload.get("state"),
        district=payload.get("district"),
        department=payload.get("department"),
        hashed_password=hash_password(payload.get("password", "changeme")),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": str(u.id), "email": u.email, "role": u.role}


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("user:manage")),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if "role" in payload:
        u.role = payload["role"]
    if "is_active" in payload:
        u.is_active = payload["is_active"]
    db.commit()
    return {"id": str(u.id), "role": u.role, "is_active": u.is_active}


@router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rules = db.query(ComplianceRule).all()
    return [
        {
            "rule_id": r.rule_id, "rule_title": r.rule_title,
            "description": r.description, "severity": r.severity,
            "check_type": r.check_type, "is_active": r.is_active,
        }
        for r in rules
    ]


@router.patch("/rules/{rule_id}")
def update_rule(
    rule_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("rule:configure")),
):
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.rule_id == rule_id
    ).first()
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    if "is_active" in payload:
        rule.is_active = payload["is_active"]
    if "severity" in payload:
        rule.severity = payload["severity"]
    db.commit()
    return {"rule_id": rule.rule_id, "is_active": rule.is_active}
