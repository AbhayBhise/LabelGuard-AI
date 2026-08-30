from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- User ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str = "OFFICER"
    state: Optional[str] = None
    district: Optional[str] = None
    department: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str
    state: Optional[str] = None
    district: Optional[str] = None
    department: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    google_id_token: str


# ---------- Product ----------
class ProductOut(BaseModel):
    id: UUID
    barcode: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Scan ----------
class ScanCreate(BaseModel):
    product_name: Optional[str] = None
    net_weight_grams: Optional[float] = None
    category: Optional[str] = None
    is_imported: bool = False
    source: str = "web"
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class ScanStatus(BaseModel):
    scan_id: UUID
    status: str
    progress: int = 0


class ScanOut(BaseModel):
    id: UUID
    scanned_at: Optional[datetime] = None
    overall_status: Optional[str] = None
    compliance_score: Optional[float] = None
    source: Optional[str] = None
    product: Optional[ProductOut] = None

    class Config:
        from_attributes = True


class ScanResultOut(BaseModel):
    scan_id: UUID
    scanned_at: Optional[datetime] = None
    overall_status: Optional[str] = None
    compliance_score: Optional[float] = None
    product: Optional[ProductOut] = None
    extracted_fields: list = Field(default_factory=list)
    violations: list = Field(default_factory=list)
    annotated_image_url: Optional[str] = None


# ---------- Violation ----------
class ViolationOut(BaseModel):
    rule_id: str
    rule_title: Optional[str] = None
    violation_type: Optional[str] = None
    severity: Optional[str] = None
    finding: Optional[str] = None
    found_value: Optional[str] = None
    expected_format: Optional[str] = None
    evidence_bbox: Optional[dict] = None

    class Config:
        from_attributes = True
