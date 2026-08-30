from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Scan, User, Violation
from app.db.session import get_db
from app.deps import require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(
    from_: datetime = None,
    to: datetime = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    query = db.query(Scan)
    total = query.count()

    def count_status(status):
        return db.query(Scan).filter(Scan.overall_status == status).count()

    return {
        "total_scans": total,
        "compliant": count_status("COMPLIANT"),
        "partial": count_status("PARTIAL"),
        "non_compliant": count_status("NON_COMPLIANT"),
    }


@router.get("/violations-by-rule")
def violations_by_rule(
    from_: datetime = None,
    to: datetime = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    rows = (
        db.query(
            Violation.rule_id,
            func.count(Violation.id).label("count"),
        )
        .group_by(Violation.rule_id)
        .order_by(func.count(Violation.id).desc())
        .all()
    )
    total = sum(r[1] for r in rows)
    return [
        {
            "rule_id": r.rule_id,
            "count": r[1],
            "percentage": round((r[1] / total) * 100, 1) if total else 0,
        }
        for r in rows
    ]


@router.get("/violations-over-time")
def violations_over_time(
    days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    """Daily violation counts over the trailing `days` window (real data)."""
    since = datetime.utcnow() - timedelta(days=max(1, days))
    day = func.date(Violation.created_at)
    rows = (
        db.query(day.label("date"), func.count(Violation.id).label("count"))
        .filter(Violation.created_at >= since)
        .group_by(day)
        .order_by(day)
        .all()
    )
    return [
        {"date": str(r.date), "violations": int(r.count)} for r in rows
    ]


@router.get("/brand-compliance")
def brand_compliance(
    from_: datetime = None,
    to: datetime = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    # Join scans->products to group by brand
    from app.db.models import Product

    rows = (
        db.query(Product.brand, func.count(Scan.id).label("scans"))
        .join(Scan, Scan.product_id == Product.id)
        .group_by(Product.brand)
        .order_by(func.count(Scan.id).desc())
        .limit(20)
        .all()
    )
    return [
        {"brand": r.brand, "total_scans": r.scans} for r in rows
    ]
