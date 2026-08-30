"""End-to-end pipeline test using a generated label image (no external ML deps).

OCR/VLM gracefully return empty without the heavy deps, so this asserts the
pipeline shape and that compliance still produces a deterministic result.
"""
import io
import unittest

from PIL import Image, ImageDraw

from app.services.datatypes import ProductMeta
from app.services.scan_service import ScanService


def make_label_image(text="MRP Rs 125 (Inclusive of all taxes) Net wt 150g"):
    img = Image.new("RGB", (400, 300), "white")
    d = ImageDraw.Draw(img)
    d.text((20, 30), text, fill="black")
    d.text((20, 120), "Mfg: 03/2025", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class ScanServiceShapeTest(unittest.TestCase):
    def test_process_returns_expected_keys(self):
        import asyncio

        service = ScanService()
        image = make_label_image()
        meta = ProductMeta(net_weight_grams=150, is_food=False)
        result = asyncio.run(service.process(image, meta))
        self.assertIn("fields", result)
        self.assertIn("ocr_text", result)
        self.assertIn("result", result)
        self.assertIn("result", result)
        self.assertTrue(hasattr(result["result"], "status"))
        self.assertIn(result["result"].status, ["COMPLIANT", "NON_COMPLIANT", "PARTIAL"])


if __name__ == "__main__":
    unittest.main()
