import re
from typing import List, Optional

from app.services.datatypes import (
    ComplianceResult,
    ExtractedFields,
    FontMeasurements,
    ProductMeta,
    Violation,
)

SEVERITY_WEIGHTS = {"CRITICAL": 2.0, "MAJOR": 1.0, "MINOR": 0.5}
TOTAL_RULES = 8


def get_min_font_height_mm(net_quantity_grams: float) -> float:
    """LM (PC) Rules 2011, Rule 6(2) minimum lettering height."""
    if net_quantity_grams <= 200:
        return 1.0
    elif net_quantity_grams <= 1000:
        return 2.0
    elif net_quantity_grams <= 5000:
        return 4.0
    else:
        return 6.0


def compute_compliance_score(violations: List[Violation]) -> float:
    weighted = sum(SEVERITY_WEIGHTS[v.severity] for v in violations)
    max_weight = TOTAL_RULES * SEVERITY_WEIGHTS["CRITICAL"]
    score = max(0.0, 1 - (weighted / max_weight))
    return round(score, 2)


class ComplianceEngine:
    """Core rule-based checker against LM (PC) Rules 2011."""

    def check(
        self,
        extracted_fields: ExtractedFields,
        font_measurements: Optional[FontMeasurements] = None,
        product_meta: Optional[ProductMeta] = None,
        field_bboxes: Optional[dict] = None,
        raw_text: Optional[str] = None,
        image_height: Optional[float] = None,
    ) -> ComplianceResult:
        product_meta = product_meta or ProductMeta()
        font_measurements = font_measurements or FontMeasurements()
        fields = extracted_fields
        violations: List[Violation] = []

        violations += self._check_manufacturer(fields)
        violations += self._check_generic_name(fields)
        violations += self._check_net_quantity(fields)
        violations += self._check_manufacture_date(fields)
        violations += self._check_mrp(fields)
        violations += self._check_consumer_care(fields)
        violations += self._check_batch_number(fields)

        if product_meta.is_food:
            violations += self._check_fssai(fields)

        if product_meta.is_imported:
            violations += self._check_country_of_origin(fields)

        if font_measurements.measured or font_measurements.field_heights:
            violations += self._check_font_sizes(
                font_measurements, product_meta.net_weight_grams
            )

        # Rule 26 — misleading declarations (text-based, always checked).
        violations += self._check_misleading(fields, raw_text)

        # Rule 6(5) — MRP on the principal display panel (needs field layout).
        if field_bboxes and image_height:
            violations += self._check_mrp_position(field_bboxes, image_height)

        critical = [v for v in violations if v.severity == "CRITICAL"]
        major = [v for v in violations if v.severity == "MAJOR"]

        if critical:
            status = "NON_COMPLIANT"
        elif major:
            status = "PARTIAL"
        else:
            status = "COMPLIANT"

        return ComplianceResult(
            status=status,
            violations=violations,
            score=compute_compliance_score(violations),
        )

    # ---- Rule 6(1)(a): Manufacturer / packer / importer identity ----
    def _check_manufacturer(self, f: ExtractedFields) -> List[Violation]:
        v: List[Violation] = []
        rule = "R6_1_a"
        title = "Manufacturer / Packer / Importer Identity"

        if not f.manufacturer_name:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="MISSING",
                severity="CRITICAL",
                finding="Manufacturer/packer/importer name not found on label",
            ))
        if not f.manufacturer_address:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="MISSING",
                severity="CRITICAL",
                finding="Manufacturer/packer/importer address not found on label",
            ))
        elif self._address_completeness_score(f.manufacturer_address) < 2:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="CONTENT",
                severity="CRITICAL",
                finding=(
                    "Manufacturer address present but incomplete "
                    "(missing pincode, state, or street details)"
                ),
                found_value=f.manufacturer_address,
                expected_format=(
                    "Full address with street, city, state and 6-digit pincode"
                ),
            ))
        return v

    @staticmethod
    def _address_completeness_score(address: str) -> int:
        score = 0
        if re.search(r"\d", address):
            score += 1  # building/plot number
        if "," in address or "\n" in address:
            score += 1  # comma-separated parts
        if re.search(r"\b\d{6}\b", address):
            score += 1  # 6-digit pincode
        if re.search(
            r"\b(andhra|arunachal|assam|bihar|chhattisgarh|goa|gujarat|haryana|"
            r"himachal|jharkhand|karnataka|kerala|madhya|maharashtra|manipur|"
            r"meghalaya|mizoram|nagaland|odisha|orissa|punjab|rajasthan|sikkim|"
            r"tamil|telangana|tripura|uttar|uttarakhand|west bengal|delhi|jammu|"
            r"kashmir|puducherry|chandigarh|pondicherry)\b",
            address, re.IGNORECASE,
        ):
            score += 1  # state name
        return score

    # ---- Rule 6(1)(b): Common / generic name ----
    def _check_generic_name(self, f: ExtractedFields) -> List[Violation]:
        if f.product_name:
            return []
        return [Violation(
            rule_id="R6_1_b", rule_title="Common / Generic Name",
            violation_type="MISSING", severity="MAJOR",
            finding="Common or generic name of commodity not found on label",
        )]

    # ---- Rule 6(1)(c): Net quantity ----
    WEIGHT_RE = re.compile(
        r"(\d+\.?\d*)\s*(g|kg|mg|gm|gram|kilogram)\b", re.IGNORECASE
    )
    VOLUME_RE = re.compile(
        r"(\d+\.?\d*)\s*(ml|l|litre|liter|cc|ltr)\b", re.IGNORECASE
    )
    COUNT_RE = re.compile(
        r"(\d+)\s*(pcs|pieces|units|tablets|capsules|nos|tabs)\b",
        re.IGNORECASE,
    )

    def _check_net_quantity(self, f: ExtractedFields) -> List[Violation]:
        v: List[Violation] = []
        rule, title = "R6_1_c", "Net Quantity"
        if not f.net_quantity:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="MISSING",
                severity="CRITICAL",
                finding="Net quantity not found on label",
            ))
            return v
        value = f.net_quantity.strip()
        if not (
            self.WEIGHT_RE.search(value)
            or self.VOLUME_RE.search(value)
            or self.COUNT_RE.search(value)
        ):
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="FORMAT",
                severity="CRITICAL",
                finding=(
                    f"Net quantity '{value}' not in standard SI unit or "
                    "recognized format"
                ),
                found_value=value,
                expected_format='e.g. "150g", "500ml", "10 pcs"',
            ))
        return v

    # ---- Rule 6(1)(e): Month and year of manufacture ----
    DATE_RE = re.compile(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[\s/\-]?20\d{2}|"
        r"(0[1-9]|1[0-2])[\s/\-]20\d{2}|"
        r"mfg\.?\s*(date\s*)?:?\s*\d{1,2}/\d{4}",
        re.IGNORECASE,
    )

    def _check_manufacture_date(self, f: ExtractedFields) -> List[Violation]:
        v: List[Violation] = []
        rule, title = "R6_1_e", "Month and Year of Manufacture"
        if not f.manufacture_date:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="MISSING",
                severity="CRITICAL",
                finding="Month and year of manufacture not found on label",
            ))
            return v
        if not self.DATE_RE.search(f.manufacture_date):
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="FORMAT",
                severity="CRITICAL",
                finding=(
                    f"Manufacture date '{f.manufacture_date}' not in "
                    "MM/YYYY or Mon YYYY format"
                ),
                found_value=f.manufacture_date,
                expected_format='e.g. "03/2025" or "Mar 2025"',
            ))
        return v

    # ---- Rule 6(1)(f): MRP inclusive of all taxes ----
    MRP_VALUE_RE = re.compile(r"[₹rs\.\s]*\d+\.?\d*", re.IGNORECASE)
    INCLUSIVE_RE = re.compile(
        r"incl(usive)?\.?\s*of\s*all\s*tax", re.IGNORECASE
    )

    def _check_mrp(self, f: ExtractedFields) -> List[Violation]:
        v: List[Violation] = []
        rule, title = "R6_1_f", "Maximum Retail Price"
        if not f.mrp:
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="MISSING",
                severity="CRITICAL",
                finding="MRP declaration not found on label",
            ))
            return v
        value = f.mrp
        if not self.MRP_VALUE_RE.search(str(value)):
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="FORMAT",
                severity="CRITICAL",
                finding=f"MRP '{value}' has no numeric price value",
                found_value=value,
            ))
        elif not self.INCLUSIVE_RE.search(str(value).lower()):
            v.append(Violation(
                rule_id=rule, rule_title=title, violation_type="CONTENT",
                severity="CRITICAL",
                finding=(
                    f"MRP present as '{value}' but missing "
                    "'inclusive of all taxes' clause"
                ),
                found_value=value,
                expected_format="MRP ₹X.XX (Inclusive of all taxes)",
            ))
        return v

    # ---- Rule 6(1)(g): Consumer care details ----
    PHONE_RE = re.compile(r"(\+91)?\s?[6-9]\d{9}|1800[\s-]?\d{3,}")
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    WEBSITE_RE = re.compile(r"www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    def _check_consumer_care(self, f: ExtractedFields) -> List[Violation]:
        if f.consumer_care and (
            self.PHONE_RE.search(f.consumer_care)
            or self.EMAIL_RE.search(f.consumer_care)
            or self.WEBSITE_RE.search(f.consumer_care)
        ):
            return []
        return [Violation(
            rule_id="R6_1_g", rule_title="Consumer Care Details",
            violation_type="MISSING", severity="MAJOR",
            finding=(
                "Consumer care contact (phone, email or website) not found "
                "on label"
            ),
            found_value=f.consumer_care,
        )]

    # ---- Rule 6(1)(h): FSSAI license (food only) ----
    FSSAI_RE = re.compile(
        r"FSSAI\s*(Lic\.?\s*No\.?\s*:?\s*)?\d{14}", re.IGNORECASE
    )

    def _check_fssai(self, f: ExtractedFields) -> List[Violation]:
        if f.fssai_license and self.FSSAI_RE.search(f.fssai_license):
            return []
        return [Violation(
            rule_id="R6_1_h", rule_title="FSSAI License Number",
            violation_type="MISSING", severity="CRITICAL",
            finding="FSSAI license/registration number not found (food product)",
            found_value=f.fssai_license,
            expected_format="14-digit FSSAI license number",
        )]

    # ---- Rule 6(1)(i): Country of origin (imports only) ----
    COO_RE = re.compile(
        r"(made\s*in|country\s*of\s*origin\s*:?|product\s*of)\s+[A-Za-z\s]+",
        re.IGNORECASE,
    )

    def _check_country_of_origin(self, f: ExtractedFields) -> List[Violation]:
        if f.country_of_origin and self.COO_RE.search(f.country_of_origin):
            return []
        return [Violation(
            rule_id="R6_1_i", rule_title="Country of Origin",
            violation_type="MISSING", severity="CRITICAL",
            finding="Country of origin not found (imported product)",
            found_value=f.country_of_origin,
        )]

    # ---- Rule 6(1)(j): Batch / lot number ----
    BATCH_RE = re.compile(
        r"(batch|lot|b\.no|b/n|lot\s*no\.?)\s*:?\s*[A-Z0-9\-]+",
        re.IGNORECASE,
    )

    def _check_batch_number(self, f: ExtractedFields) -> List[Violation]:
        if f.batch_number and self.BATCH_RE.search(f.batch_number):
            return []
        return [Violation(
            rule_id="R6_1_j", rule_title="Batch / Lot Number",
            violation_type="MISSING", severity="MAJOR",
            finding="Batch/lot number not found on label",
            found_value=f.batch_number,
        )]

    # ---- Rule 6(2): Font size ----
    def _check_font_sizes(
        self, measurements: FontMeasurements, net_weight_grams: float
    ) -> List[Violation]:
        min_height = get_min_font_height_mm(net_weight_grams)
        v: List[Violation] = []
        for field, height_mm in measurements.field_heights.items():
            if height_mm < min_height:
                v.append(Violation(
                    rule_id="R6_2", rule_title="Font Size Compliance",
                    violation_type="FONT_SIZE", severity="MAJOR",
                    finding=(
                        f"{field} font height {height_mm:.2f}mm is below "
                        f"required {min_height:.1f}mm minimum"
                    ),
                    found_value=f"{height_mm:.2f}mm",
                    expected_format=f">= {min_height:.1f}mm",
                ))
        return v

    # ---- Rule 6(5): MRP on the principal display panel ----
    #: Fraction of the label height below which the MRP is considered
    #: "buried" rather than prominently on the principal display panel.
    PDP_BOTTOM_FRACTION = 0.8

    def _check_mrp_position(
        self, field_bboxes: dict, image_height: float
    ) -> List[Violation]:
        box = field_bboxes.get("mrp")
        if not box or not image_height:
            return []
        frac = box.get("y", 0) / image_height
        if frac <= self.PDP_BOTTOM_FRACTION:
            return []
        return [Violation(
            rule_id="R6_5",
            rule_title="MRP on Principal Display Panel",
            violation_type="CONTENT", severity="MAJOR",
            finding=(
                f"MRP appears {frac * 100:.0f}% down the label, near the "
                "bottom edge rather than prominently on the principal "
                "display panel"
            ),
            found_value=f"{frac * 100:.0f}% from top",
            expected_format=(
                "MRP within the upper "
                f"{self.PDP_BOTTOM_FRACTION * 100:.0f}% of the principal "
                "display panel"
            ),
            evidence_bbox=box,
        )]

    # ---- Rule 26: No misleading / unsubstantiated declarations ----
    MISLEADING_PATTERNS = [
        (re.compile(r"100\s*%\s*(natural|organic|pure|herbal|ayurvedic)",
                    re.IGNORECASE),
         "unqualified '100%' claim"),
        (re.compile(r"\b(no\.?\s*1|number\s*one|#\s*1)\b", re.IGNORECASE),
         "unsubstantiated ranking claim"),
        (re.compile(r"\bbest\s+in\s+(india|class|the\s+world)\b",
                    re.IGNORECASE),
         "unsubstantiated superiority claim"),
        (re.compile(r"\b(clinically|scientifically|lab)\s+proven\b",
                    re.IGNORECASE),
         "unverifiable 'proven' claim"),
        (re.compile(r"\babsolutely\s+free\b|\b100\s*%\s*free\b",
                    re.IGNORECASE),
         "'free' claim without stated eligibility"),
        (re.compile(r"\bmiracle\b|\bcures?\b|\bguaranteed\s+results?\b",
                    re.IGNORECASE),
         "exaggerated efficacy claim"),
    ]

    def _check_misleading(
        self, f: ExtractedFields, raw_text: Optional[str] = None
    ) -> List[Violation]:
        text = raw_text or f.all_text or ""
        if not text:
            return []
        seen = set()
        out: List[Violation] = []
        for rx, label in self.MISLEADING_PATTERNS:
            m = rx.search(text)
            if not m or label in seen:
                continue
            seen.add(label)
            out.append(Violation(
                rule_id="R26",
                rule_title="No Misleading Declarations",
                violation_type="CONTENT", severity="MAJOR",
                finding=(
                    f"Potentially misleading declaration ({label}): "
                    f"\"{m.group(0).strip()}\""
                ),
                found_value=m.group(0).strip(),
                expected_format=(
                    "Claims must be substantiated or removed (Rule 26)"
                ),
            ))
        return out
