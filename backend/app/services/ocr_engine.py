"""OCR engine — PP-OCRv5 (PaddleOCR 3.0) primary, with graceful fallback.

The heavy PaddleOCR dependency is optional at runtime; when unavailable the
engine returns an empty result so the API still responds (worker containers
provide the real OCR).
"""
from typing import List, Optional

import numpy as np

from app.services.datatypes import BoundingBox, OCRResult, Word


class OCREngine:
    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR  # type: ignore

                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="en",
                    use_gpu=False,
                    show_log=False,
                )
            except Exception:
                self._ocr = None
        return self._ocr

    @property
    def available(self) -> bool:
        return self.ocr is not None

    def extract(self, image: np.ndarray) -> OCRResult:
        """Return OCR result as list of Word(text, bbox, confidence)."""
        if not self.available:
            return OCRResult(words=[])
        result = self.ocr.ocr(image, cls=True)
        return self._parse_result(result)

    def _parse_result(self, raw) -> OCRResult:
        words: List[Word] = []
        if not raw:
            return OCRResult(words=[])
        for line in raw[0] or []:
            bbox, (text, confidence) = line
            words.append(
                Word(
                    text=text,
                    bbox=BoundingBox.from_quad(bbox),
                    confidence=float(confidence),
                )
            )
        return OCRResult(words=words)

    def to_text(self, result: OCRResult) -> str:
        return "\n".join(w.text for w in result.words)
