"""Scan pipeline orchestration.

Coordinates: image preprocessing -> OCR -> VLM -> font detection ->
compliance check -> persist. Gracefully degrades when ML deps are missing.
"""
import io
import re
from typing import Optional

import numpy as np
from PIL import Image

from app.services.compliance_engine import ComplianceEngine
from app.services.datatypes import (
    ExtractedFields,
    FontMeasurements,
    OCRResult,
    ProductMeta,
)
from app.services.font_detector import FontSizeDetector
from app.services.image_processor import ImageProcessor
from app.services.ocr_engine import OCREngine
from app.services.vlm_engine import VLMEngine


class ScanService:
    # Rule -> the extracted field(s) whose region is the visual evidence for a
    # violation of that rule. Used to attach a bounding box the report can draw.
    RULE_FIELDS = {
        "R6_1_a": ["manufacturer_name", "manufacturer_address"],
        "R6_1_b": ["product_name"],
        "R6_1_c": ["net_quantity"],
        "R6_1_e": ["manufacture_date"],
        "R6_1_f": ["mrp"],
        "R6_1_g": ["consumer_care"],
        "R6_1_h": ["fssai_license"],
        "R6_1_i": ["country_of_origin"],
        "R6_1_j": ["batch_number"],
    }

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.ocr_engine = OCREngine()
        self.vlm_engine = VLMEngine()
        self.font_detector = FontSizeDetector()
        self.compliance = ComplianceEngine()

    async def process(
        self,
        image_bytes: bytes,
        product_meta: ProductMeta,
    ) -> dict:
        """Run full pipeline and return consolidated result."""
        # 1. Preprocess
        processed = self.image_processor.preprocess(image_bytes)
        array = np.array(processed.image)

        # 2. OCR
        ocr_result = self.ocr_engine.extract(array)
        ocr_text = self.ocr_engine.to_text(ocr_result)

        # 3. VLM (async, may return {})
        vlm_data = await self.vlm_engine.extract_fields(image_bytes)
        ocr_fields = self._ocr_to_fields(ocr_text)

        # Merge: VLM primary, OCR as fallback for missing fields
        merged = {**ocr_fields, **vlm_data}
        fields = ExtractedFields.from_dict(merged)

        # 4. Font detection
        calibration = self.font_detector.calibrate(array)
        field_bboxes = self._map_field_bboxes(fields, ocr_result)
        font_measurements = self.font_detector.measure_text_heights(
            ocr_result, calibration, field_bboxes
        )

        # 5. Compliance
        image_height = float(array.shape[0]) if array.ndim >= 2 else None
        result = self.compliance.check(
            fields,
            font_measurements,
            product_meta,
            field_bboxes=field_bboxes,
            raw_text=ocr_text,
            image_height=image_height,
        )

        # 6. Attach visual evidence (bounding box) to violations where the
        #    offending field was actually located on the label.
        self._attach_evidence(result.violations, field_bboxes)

        return {
            "fields": fields,
            "ocr_text": ocr_text,
            "font_measurements": font_measurements,
            "result": result,
            "bboxes": field_bboxes,
            "ocr_available": self.ocr_engine.available,
        }

    @classmethod
    def _attach_evidence(cls, violations, field_bboxes: dict) -> None:
        """Set ``evidence_bbox`` on each violation to the region of the field
        it concerns, when that field was located on the label.

        MISSING violations are left without a box (there is nothing on the
        label to point at).
        """
        if not field_bboxes:
            return
        for v in violations:
            if v.evidence_bbox or v.violation_type == "MISSING":
                continue
            candidates = list(cls.RULE_FIELDS.get(v.rule_id, []))
            if v.rule_id == "R6_2" and v.finding:
                candidates.insert(0, v.finding.split()[0])
            for field in candidates:
                if field in field_bboxes:
                    v.evidence_bbox = field_bboxes[field]
                    break

    @staticmethod
    def _ocr_to_fields(ocr_text: str) -> dict:
        """Crude extraction of key fields from raw OCR text (fallback)."""
        text = ocr_text.lower()
        out = {}

        mrp_match = re.search(
            r"(mrp|maximum retail price|m\.r\.p)\s*:?\s*([₹\d].*)", text
        )
        if mrp_match:
            out["mrp"] = mrp_match.group(0)

        mfg_match = re.search(
            r"(mfg\s*(date\s*)?:?\s*[0-9]{1,2}[/-][0-9]{2,4})|"
            r"((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
            r"\s*20[0-9]{2})",
            text,
        )
        if mfg_match:
            out["manufacture_date"] = mfg_match.group(0)

        net_match = re.search(
            r"(net\s*(wt|qty|quantity|weight|volume|contents)?\s*:?\s*"
            r"\d+\.?\d*\s*(g|kg|ml|l|gm|gram|kilogram|litre|liter|pcs|nos))",
            text,
        )
        if net_match:
            out["net_quantity"] = net_match.group(1)

        return out

    @staticmethod
    def _map_field_bboxes(fields: ExtractedFields, ocr_result: OCRResult) -> dict:
        """Locate each extracted field's value among the OCR words and return
        its union bounding box as ``{x, y, w, h}``.

        This gives the font-size detector real regions to measure and gives the
        compliance layer coordinates to attach as violation evidence. Fields
        that cannot be matched to any OCR word are simply omitted.
        """
        words = getattr(ocr_result, "words", None) or []
        if not words:
            return {}

        def norm(s: str) -> str:
            return re.sub(r"[^a-z0-9]", "", s.lower())

        indexed = [
            (norm(w.text), w) for w in words if w.text and w.text.strip()
        ]

        bboxes: dict = {}
        for name, value in fields.as_dict().items():
            if name == "all_text" or not value:
                continue
            tokens = {
                norm(t)
                for t in re.findall(r"[A-Za-z0-9]+", str(value))
                if len(t) >= 3
            }
            tokens.discard("")
            if not tokens:
                continue

            def hits(key: str) -> bool:
                return any(
                    key == t or (len(t) >= 3 and (t in key or key in t))
                    for t in tokens
                )

            matched = [w for key, w in indexed if key and hits(key)]
            if not matched:
                continue
            x1 = min(w.bbox.x for w in matched)
            y1 = min(w.bbox.y for w in matched)
            x2 = max(w.bbox.x + w.bbox.w for w in matched)
            y2 = max(w.bbox.y + w.bbox.h for w in matched)
            bboxes[name] = {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
        return bboxes
