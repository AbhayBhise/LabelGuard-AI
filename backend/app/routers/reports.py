import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.models import ExtractedField, Product, Scan, User, Violation
from app.db.session import get_db
from app.deps import get_current_user, require_permission
from app.services.datatypes import ComplianceResult, ExtractedFields, Violation as V
from app.services.report_generator import ReportGenerator
from app.utils import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


def _build_scan_objects(db: Session, scan: Scan):
    scanned_fields = (
        db.query(ExtractedField).filter(ExtractedField.scan_id == scan.id).all()
    )
    scanned_violations = (
        db.query(Violation).filter(Violation.scan_id == scan.id).all()
    )
    product = None
    if scan.product_id:
        product = db.query(Product).filter(Product.id == scan.product_id).first()

    fields = ExtractedFields.from_dict(
        {f.field_name: f.extracted_value for f in scanned_fields}
    )
    violations = [
        V(
            rule_id=v.rule_id, rule_title=v.rule_title,
            violation_type=v.violation_type, severity=v.severity,
            finding=v.finding, found_value=v.found_value,
            expected_format=v.expected_format, evidence_bbox=v.evidence_bbox,
        )
        for v in scanned_violations
    ]
    result = ComplianceResult(
        status=scan.overall_status or "PENDING",
        violations=violations,
        score=float(scan.compliance_score) if scan.compliance_score else 1.0,
    )
    product_dict = {
        "product_name": product.product_name if product else None,
        "barcode": product.barcode if product else None,
        "brand": product.brand if product else None,
        "category": product.category if product else None,
    }
    return fields, result, product_dict


@router.get("/{scan_id}/pdf")
def download_pdf(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("report:download_own")),
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    fields, result, product_dict = _build_scan_objects(db, scan)

    annotated = None
    if scan.raw_image_url:
        try:
            raw = storage.get_file(scan.raw_image_url)
            import numpy as np
            import cv2

            arr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            rg = ReportGenerator()
            annotated_arr = rg.annotate_image(arr, result.violations, fields)
            ok, buf = cv2.imencode(".jpg", annotated_arr)
            annotated = buf.tobytes()
        except Exception:
            annotated = None

    pdf = ReportGenerator().generate_pdf(
        str(scan.id), product_dict, fields, result,
        officer={"name": user.name, "role": user.role},
        annotated_image=annotated,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="report-{scan.id}.pdf"'
            )
        },
    )


@router.get("/{scan_id}/docx")
def download_docx(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("report:download_own")),
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    fields, result, product_dict = _build_scan_objects(db, scan)
    docx = ReportGenerator().generate_docx(
        str(scan.id), product_dict, fields, result,
        officer={"name": user.name, "role": user.role},
    )
    return Response(
        content=docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="report-{scan.id}.docx"'
            )
        },
    )
