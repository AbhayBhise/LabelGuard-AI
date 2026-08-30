import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Product, Scan
from app.db.session import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(
    search: str = None,
    category: str = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Product)
    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Product.category == category)
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": [
            {
                "id": str(p.id), "product_name": p.product_name,
                "barcode": p.barcode, "brand": p.brand, "category": p.category,
            }
            for p in items
        ],
    }


@router.get("/{product_id}")
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    scans = db.query(Scan).filter(Scan.product_id == product_id).all()
    return {
        "id": str(product.id),
        "product_name": product.product_name,
        "barcode": product.barcode,
        "brand": product.brand,
        "category": product.category,
        "scans": [
            {
                "id": str(s.id),
                "overall_status": s.overall_status,
                "compliance_score": float(s.compliance_score) if s.compliance_score else None,
                "scanned_at": s.scanned_at.isoformat() if s.scanned_at else None,
            }
            for s in scans
        ],
    }
