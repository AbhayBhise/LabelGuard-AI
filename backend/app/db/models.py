import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(30), nullable=False, default="OFFICER")
    state = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)
    department = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    scans = relationship("Scan", back_populates="officer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    barcode = Column(String(50), index=True, nullable=True)
    product_name = Column(Text, nullable=True)
    brand = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    scans = relationship("Scan", back_populates="product")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        Uuid, ForeignKey("products.id"), nullable=True
    )
    officer_id = Column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    scanned_at = Column(DateTime, server_default=func.now())
    location_lat = Column(DECIMAL(9, 6), nullable=True)
    location_lng = Column(DECIMAL(9, 6), nullable=True)
    source = Column(String(50), default="web")
    raw_image_url = Column(Text, nullable=True)
    processed_image_url = Column(Text, nullable=True)
    status = Column(String(20), default="processing")
    overall_status = Column(String(20), nullable=True)
    compliance_score = Column(DECIMAL(4, 3), nullable=True)
    net_weight_grams = Column(DECIMAL(10, 2), nullable=True)

    product = relationship("Product", back_populates="scans")
    officer = relationship("User", back_populates="scans")
    extracted_fields = relationship(
        "ExtractedField", back_populates="scan", cascade="all, delete-orphan"
    )
    violations = relationship(
        "Violation", back_populates="scan", cascade="all, delete-orphan"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        Uuid, ForeignKey("scans.id"), index=True, nullable=False
    )
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=True)
    confidence = Column(DECIMAL(5, 4), nullable=True)
    bounding_box = Column(JSON, nullable=True)  # {x, y, w, h}
    extraction_method = Column(String(50), default="ocr")  # ocr|vlm|layout

    scan = relationship("Scan", back_populates="extracted_fields")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        Uuid, ForeignKey("scans.id"), index=True, nullable=False
    )
    rule_id = Column(String(20), nullable=False)  # e.g. R6_1_f
    rule_title = Column(Text, nullable=True)
    rule_description = Column(Text, nullable=True)
    violation_type = Column(String(30), default="MISSING")
    severity = Column(String(20), default="MAJOR")
    finding = Column(Text, nullable=True)
    found_value = Column(Text, nullable=True)
    expected_format = Column(Text, nullable=True)
    evidence_image_url = Column(Text, nullable=True)
    evidence_bbox = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    scan = relationship("Scan", back_populates="violations")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    rule_id = Column(String(20), primary_key=True)
    rule_title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)
    check_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    applies_to_categories = Column(JSON, nullable=True)  # null = all
