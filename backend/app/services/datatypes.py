"""Data structures shared across the ML pipeline and compliance engine."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BoundingBox:
    x: float
    y: float
    w: float
    h: float

    @classmethod
    def from_quad(cls, quad) -> "BoundingBox":
        """Convert a 4-point polygon [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] to XYWH."""
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        x = min(xs)
        y = min(ys)
        w = max(xs) - x
        h = max(ys) - y
        return cls(x=x, y=y, w=w, h=h)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}


@dataclass
class Word:
    text: str
    bbox: BoundingBox
    confidence: float


@dataclass
class OCRResult:
    words: List[Word] = field(default_factory=list)


@dataclass
class ExtractedFields:
    """The consolidated field set used by the compliance engine."""

    manufacturer_name: Optional[str] = None
    manufacturer_address: Optional[str] = None
    product_name: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    consumer_care: Optional[str] = None
    country_of_origin: Optional[str] = None
    fssai_license: Optional[str] = None
    batch_number: Optional[str] = None
    all_text: str = ""

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedFields":
        known = {
            k
            for k in cls.__dataclass_fields__  # type: ignore[attr-defined]
        }
        kwargs = {k: v for k, v in data.items() if k in known and v}
        kwargs.setdefault(
            "all_text", " ".join(str(v) for v in data.values() if v)
        )
        return cls(**kwargs)


@dataclass
class FontMeasurements:
    """Per-field measured font heights in mm."""

    field_heights: dict = field(default_factory=dict)
    px_per_mm: Optional[float] = None
    measured: bool = False


@dataclass
class ProductMeta:
    net_weight_grams: float = 0.0
    is_imported: bool = False
    is_food: bool = False
    is_drinking_water: bool = False
    is_electronic: bool = False


@dataclass
class Violation:
    rule_id: str
    rule_title: str
    violation_type: str  # MISSING | FORMAT | CONTENT | FONT_SIZE
    severity: str  # CRITICAL | MAJOR | MINOR
    finding: str
    found_value: Optional[str] = None
    expected_format: Optional[str] = None
    evidence_bbox: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "finding": self.finding,
            "found_value": self.found_value,
            "expected_format": self.expected_format,
            "evidence_bbox": self.evidence_bbox,
        }


@dataclass
class ComplianceResult:
    status: str  # COMPLIANT | NON_COMPLIANT | PARTIAL
    violations: List[Violation] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "score": self.score,
            "violations": [v.to_dict() for v in self.violations],
        }
