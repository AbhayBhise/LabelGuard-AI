"""Font size detector.

Computes pixel-per-mm ratio via barcode module width (ISO 15416 ~0.33mm
module), then measures OCR bounding box heights against LM Rule 6(2) minimums.
"""
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np

from app.services.compliance_engine import get_min_font_height_mm
from app.services.datatypes import FontMeasurements, OCRResult

BARCODE_MODULE_WIDTH_MM = 0.33  # ISO 15416 standard minimum


@dataclass
class Calibration:
    """Result of trying to establish a pixel-per-mm scale for an image.

    ``reliable`` is only True when the scale came from a detected barcode; a
    heuristic fallback is exposed for display but must not drive violations.
    """

    px_per_mm: Optional[float] = None
    source: str = "none"  # "barcode" | "heuristic" | "none"
    reliable: bool = False


class FontSizeDetector:
    def calibrate(self, image: np.ndarray) -> Calibration:
        """Establish a pixel-per-mm scale, preferring barcode calibration."""
        module_width_px = self._barcode_module_width_px(image)
        if module_width_px:
            return Calibration(
                px_per_mm=module_width_px / BARCODE_MODULE_WIDTH_MM,
                source="barcode",
                reliable=True,
            )
        heuristic = self._document_proportion_px_per_mm(image)
        if heuristic:
            return Calibration(
                px_per_mm=heuristic, source="heuristic", reliable=False
            )
        return Calibration()

    def compute_px_per_mm(self, image: np.ndarray) -> Optional[float]:
        """Backwards-compatible scalar accessor (used by the layout worker)."""
        return self.calibrate(image).px_per_mm

    def _barcode_module_width_px(self, image: np.ndarray) -> Optional[float]:
        try:
            from pyzbar.pyzbar import decode  # type: ignore

            codes = decode(image)
            if not codes:
                return None
            # A 1-D barcode region: narrowest vertical bar width approximates
            # a module. We approximate module width as barcode "left" strip
            # region height/width ratio. For robustness, use a heuristic:
            buf_type = codes[0].type
            if buf_type and codes[0].rect.width > 0:
                # module width ~ rect.height / number of modules is unknown;
                # return a stable proxy from the pattern's bar width instead.
                return self._measure_bar_width(image, codes[0].rect)
        except Exception:
            return None
        return None

    def _measure_bar_width(self, image, rect) -> Optional[float]:
        # Estimate narrow-bar (module) width by scanning a horizontal line
        # across the barcode and finding minimum run-length of a color.
        x, y, w, h = rect.left, rect.top, rect.width, rect.height
        row = image[y + h // 2, x : x + w]
        if row.ndim > 1:
            gray = row.mean(axis=1)
        else:
            gray = row
        binary = gray > (gray.mean())
        min_run = float("inf")
        run = 0
        for val in binary:
            if val:
                run += 1
            else:
                if run > 0:
                    min_run = min(min_run, run)
                run = 0
        if min_run == float("inf"):
            return None
        return float(min_run)

    def _document_proportion_px_per_mm(
        self, image: np.ndarray
    ) -> Optional[float]:
        """Heuristic: assume label height corresponds to a typical ~50mm tall
        panel on the image. Rough fallback when no barcode present."""
        h = int(image.shape[0])
        if h <= 0:
            return None
        return h / 50.0

    def measure_text_heights(
        self,
        ocr_result: OCRResult,
        calibration: Union[Calibration, float, None],
        field_bboxes: dict,
    ) -> FontMeasurements:
        """Compute per-field font heights in mm from OCR words.

        ``calibration`` may be a :class:`Calibration` or a bare px/mm float
        (legacy callers). Per-field heights are only filled when the scale is
        reliable, so a heuristic fallback never produces a Rule 6(2) violation.
        """
        if isinstance(calibration, Calibration):
            px_per_mm = calibration.px_per_mm
            reliable = calibration.reliable
        else:
            px_per_mm = calibration
            reliable = px_per_mm is not None

        fm = FontMeasurements(px_per_mm=px_per_mm, measured=reliable)
        if not reliable or not px_per_mm or px_per_mm <= 0:
            return fm

        for field, bbox in field_bboxes.items():
            if not bbox:
                continue
            # Estimate field text height: average height of OCR words inside
            # (or nearest to) the field's bounding box.
            heights = [
                w.bbox.h
                for w in ocr_result.words
                if self._overlap(w, bbox) > 0.4
            ]
            if heights:
                fm.field_heights[field] = round(
                    (sum(heights) / len(heights)) / px_per_mm, 2
                )
        return fm

    @staticmethod
    def _overlap(word, bbox) -> float:
        wb, bb = word.bbox, bbox
        ix = max(0, min(wb.x + wb.w, bb["x"] + bb["w"]) - max(wb.x, bb["x"]))
        iy = max(0, min(wb.y + wb.h, bb["y"] + bb["h"]) - max(wb.y, bb["y"]))
        inter = ix * iy
        return inter / (wb.w * wb.h) if wb.w * wb.h > 0 else 0.0

    @staticmethod
    def min_height_for(net_weight_grams: float) -> float:
        return get_min_font_height_mm(net_weight_grams)
