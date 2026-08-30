import logging
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.models import ExtractedField, Product, Scan, User, Violation
from app.db.session import SessionLocal, get_db
from app.deps import get_current_user, require_permission
from app.models.schemas import ScanOut, ScanResultOut, ScanStatus
from app.services.datatypes import ProductMeta
from app.services.scan_service import ScanService
from app.utils import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scans", tags=["scans"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB, matches the upload UI


def _validate_image(upload: UploadFile) -> bytes:
    """Enforce content-type, size and that the bytes are a decodable image."""
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported image type '{upload.content_type or 'unknown'}'. "
            "Upload JPEG, PNG or WebP.",
        )
    data = upload.file.read()
    if not data:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Uploaded image is empty"
        )
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Image exceeds the 10 MB limit",
        )
    try:
        import io

        from PIL import Image

        Image.open(io.BytesIO(data)).verify()
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "File could not be read as an image",
        )
    return data


def _run_pipeline(scan_id: str, image_bytes: bytes, meta: dict):
    """Background task: run ML pipeline and persist results."""
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
        if not scan:
            return

        product_meta = ProductMeta(
            net_weight_grams=float(meta.get("net_weight_grams") or 0),
            is_imported=bool(meta.get("is_imported")),
            is_food=(meta.get("category") == "food"),
            is_drinking_water=(meta.get("category") == "water"),
            is_electronic=(meta.get("category") == "electronics"),
        )

        service = ScanService()
        result = await_run(service, image_bytes, product_meta)

        # Persist fields
        for name, value in result["fields"].as_dict().items():
            if name == "all_text":
                continue
            db.add(ExtractedField(
                scan_id=scan.id,
                field_name=name,
                extracted_value=str(value),
                extraction_method="vlm" if name in {
                    "manufacturer_name", "manufacturer_address", "country_of_origin",
                    "fssai_license", "batch_number", "expiry_date", "consumer_care",
                    "product_name",
                } else "ocr",
            ))

        # Persist violations
        for v in result["result"].violations:
            db.add(Violation(
                scan_id=scan.id,
                rule_id=v.rule_id,
                rule_title=v.rule_title,
                violation_type=v.violation_type,
                severity=v.severity,
                finding=v.finding,
                found_value=v.found_value,
                expected_format=v.expected_format,
                evidence_bbox=v.evidence_bbox,
            ))

        scan.overall_status = result["result"].status
        scan.compliance_score = result["result"].score
        scan.status = "complete"
        db.commit()
    except Exception:
        logger.exception("Pipeline failed for scan %s", scan_id)
        scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
        if scan:
            scan.status = "failed"
            db.commit()
    finally:
        db.close()


def await_run(service, image_bytes, meta):
    import asyncio

    return asyncio.run(service.process(image_bytes, meta))


@router.post("", status_code=201)
def create_scan(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    product_name: Optional[str] = Form(None),
    net_weight_grams: Optional[float] = Form(None),
    category: Optional[str] = Form(None),
    is_imported: bool = Form(False),
    source: str = Form("web"),
    location_lat: Optional[float] = Form(None),
    location_lng: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("scan:create")),
):
    if not images:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one image required")
    if len(images) > 10:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Max 10 images")

    # Validate + read first image (MVP) and store
    data = _validate_image(images[0])
    raw_url = storage.put_file(data, images[0].content_type)

    scan = Scan(
        officer_id=user.id,
        source=source,
        raw_image_url=raw_url,
        status="processing",
        net_weight_grams=net_weight_grams,
        location_lat=location_lat,
        location_lng=location_lng,
    )
    if product_name:
        product = Product(product_name=product_name, category=category)
        db.add(product)
        db.flush()
        scan.product_id = product.id
    db.add(scan)
    db.commit()
    db.refresh(scan)

    meta = {
        "net_weight_grams": net_weight_grams,
        "is_imported": is_imported,
        "category": category,
    }
    background_tasks.add_task(_run_pipeline, str(scan.id), data, meta)

    return {"scan_id": str(scan.id), "status": "processing", "estimated_seconds": 8}


@router.get("/{scan_id}/status", response_model=ScanStatus)
def get_status(scan_id: uuid.UUID, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    progress = 100 if scan.status == "complete" else (50 if scan.status == "failed" else 30)
    return ScanStatus(scan_id=scan.id, status=scan.status, progress=progress)


@router.get("/{scan_id}")
def get_scan(scan_id: uuid.UUID, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")

    fields = db.query(ExtractedField).filter(ExtractedField.scan_id == scan.id).all()
    violations = db.query(Violation).filter(Violation.scan_id == scan.id).all()

    product = None
    if scan.product_id:
        p = db.query(Product).filter(Product.id == scan.product_id).first()
        if p:
            product = {
                "id": str(p.id), "name": p.product_name, "barcode": p.barcode,
                "category": p.category, "brand": p.brand,
            }

    return {
        "scan_id": str(scan.id),
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None,
        "overall_status": scan.overall_status,
        "compliance_score": float(scan.compliance_score) if scan.compliance_score else None,
        "status": scan.status,
        "product": product,
        "extracted_fields": [
            {
                "field": f.field_name, "value": f.extracted_value,
                "confidence": float(f.confidence) if f.confidence else None,
                "bounding_box": f.bounding_box,
                "extraction_method": f.extraction_method,
            }
            for f in fields
        ],
        "violations": [
            {
                "rule_id": v.rule_id, "rule_title": v.rule_title,
                "violation_type": v.violation_type, "severity": v.severity,
                "finding": v.finding, "found_value": v.found_value,
                "expected_format": v.expected_format, "evidence_bbox": v.evidence_bbox,
            }
            for v in violations
        ],
        "annotated_image_url": scan.processed_image_url,
    }


@router.get("")
def list_scans(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    scans = db.query(Scan).offset(offset).limit(limit).all()
    total = db.query(Scan).count()
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": [
            {
                "id": str(s.id),
                "overall_status": s.overall_status,
                "compliance_score": float(s.compliance_score) if s.compliance_score else None,
                "scanned_at": s.scanned_at.isoformat() if s.scanned_at else None,
                "source": s.source,
            }
            for s in scans
        ],
    }
