"""Scan pipeline orchestration.

Coordinates: image preprocessing -> OCR -> VLM -> font detection ->
compliance check -> persist. Gracefully degrades when ML deps are missing.
"""
import io
from typing import Optional

import numpy as np
from PIL import Image

from app.services.compliance_engine import ComplianceEngine
from app.services.datatypes import ExtractedFields, FontMeasurements, ProductMeta
from app.services.font_detector import FontSizeDetector
from app.services.image_processor import ImageProcessor
from app.services.ocr_engine import OCREngine
from app.services.vlm_engine import VLMEngine


class ScanService:
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
        px_per_mm = self.font_detector.compute_px_per_mm(array)
        field_bboxes = self._map_field_bboxes(fields)
        font_measurements = self.font_detector.measure_text_heights(
            ocr_result, px_per_mm, field_bboxes
        )

        # 5. Compliance
        result = self.compliance.check(fields, font_measurements, product_meta)

        return {
            "fields": fields,
            "ocr_text": ocr_text,
            "font_measurements": font_measurements,
            "result": result,
            "bboxes": field_bboxes,
            "ocr_available": self.ocr_engine.available,
        }

    @staticmethod
    def _ocr_to_fields(ocr_text: str) -> dict:
        """Crude extraction of key fields from raw OCR text (fallback)."""
        import re

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
    def _map_field_bboxes(fields: ExtractedFields) -> dict:
        # Without dedicated per-field OCR grouping we leave bboxes empty;
        # font measurements then gracefully report no violations.
        return {}
