from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Product, Scan, User, Violation
from app.db.session import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("")
def list_violations(
    rule_id: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cross-scan violation feed. Officers see only their own scans;
    supervisors/admins/viewers see all."""
    q = (
        db.query(Violation, Scan, Product)
        .join(Scan, Violation.scan_id == Scan.id)
        .outerjoin(Product, Scan.product_id == Product.id)
    )
    if user.role == "OFFICER":
        q = q.filter(Scan.officer_id == user.id)
    if rule_id:
        q = q.filter(Violation.rule_id == rule_id)
    if severity:
        q = q.filter(Violation.severity == severity.upper())

    total = q.count()
    rows = (
        q.order_by(Violation.created_at.desc())
        .offset(max(0, (page - 1) * limit))
        .limit(limit)
        .all()
    )
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": [
            {
                "id": str(v.id),
                "rule_id": v.rule_id,
                "rule_title": v.rule_title,
                "severity": v.severity,
                "violation_type": v.violation_type,
                "finding": v.finding,
                "found_value": v.found_value,
                "scan_id": str(s.id),
                "scanned_at": s.scanned_at.isoformat() if s.scanned_at else None,
                "product_name": p.product_name if p else None,
            }
            for v, s, p in rows
        ],
    }
