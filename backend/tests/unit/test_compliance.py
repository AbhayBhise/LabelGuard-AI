"""Compliance engine tests covering LM (PC) Rules 2011 scenarios."""
import unittest

from app.services.compliance_engine import (
    ComplianceEngine,
    compute_compliance_score,
    get_min_font_height_mm,
)
from app.services.datatypes import (
    ExtractedFields,
    FontMeasurements,
    ProductMeta,
)


class MRPTest(unittest.TestCase):
    def setUp(self):
        self.engine = ComplianceEngine()

    def test_mrp_missing(self):
        fields = ExtractedFields(mrp=None, all_text="")
        result = self.engine.check(
            fields,
            product_meta=ProductMeta(net_weight_grams=150, is_food=False),
        )
        mrp = [v for v in result.violations if v.rule_id == "R6_1_f"]
        self.assertTrue(any(v.violation_type == "MISSING" for v in mrp))
        self.assertEqual(result.status, "NON_COMPLIANT")

    def test_mrp_without_inclusive_clause(self):
        fields = ExtractedFields(mrp="MRP ₹125", all_text="MRP ₹125")
        result = self.engine.check(
            fields, product_meta=ProductMeta(net_weight_grams=150)
        )
        mrp = [v for v in result.violations if v.rule_id == "R6_1_f"]
        self.assertTrue(any(v.violation_type == "CONTENT" for v in mrp))
        self.assertIn("inclusive of all taxes", mrp[0].finding.lower())

    def test_mrp_compliant(self):
        fields = ExtractedFields(
            mrp="MRP ₹125 (Inclusive of all taxes)",
            all_text="MRP ₹125 (Inclusive of all taxes)",
            manufacturer_name="XYZ Foods",
            manufacturer_address="Plot 1, Mumbai, Maharashtra 400001",
            product_name="Biscuit",
            net_quantity="150g",
            manufacture_date="03/2025",
            consumer_care="1800-123-456",
            batch_number="Batch: B-001",
        )
        result = self.engine.check(
            fields, product_meta=ProductMeta(net_weight_grams=150)
        )
        self.assertEqual(result.status, "COMPLIANT")
        self.assertAlmostEqual(result.score, 1.0)


class ManufactureDateTest(unittest.TestCase):
    def setUp(self):
        self.engine = ComplianceEngine()

    def test_valid_date_format(self):
        fields = ExtractedFields(
            manufacture_date="Mar 2024", all_text="Mar 2024",
            manufacturer_name="A", manufacturer_address="B, C, 123456, Maharashtra",
            net_quantity="200ml", mrp="MRP ₹10 incl of all taxes", product_name="X",
        )
        result = self.engine.check(
            fields, product_meta=ProductMeta(net_weight_grams=100)
        )
        date_v = [v for v in result.violations if v.rule_id == "R6_1_e"]
        self.assertEqual(date_v, [])

    def test_year_only_invalid(self):
        fields = ExtractedFields(manufacture_date="2024", all_text="2024")
        result = self.engine.check(fields)
        date_v = [v for v in result.violations if v.rule_id == "R6_1_e"]
        self.assertTrue(any(v.violation_type == "FORMAT" for v in date_v))


class FontSizeTest(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(get_min_font_height_mm(200), 1.0)
        self.assertEqual(get_min_font_height_mm(999), 2.0)
        self.assertEqual(get_min_font_height_mm(5000), 4.0)
        self.assertEqual(get_min_font_height_mm(5001), 6.0)

    def test_font_violation(self):
        engine = ComplianceEngine()
        fields = ExtractedFields(
            manufacturer_name="A", manufacturer_address="B, C, 123456, Maharashtra",
            product_name="X", net_quantity="150g", mrp="MRP ₹10 (Inclusive of all taxes)",
            manufacture_date="03/2025", consumer_care="1800-123-456", batch_number="B1",
        )
        fm = FontMeasurements(
            field_heights={"net_quantity": 0.7}, px_per_mm=12.0, measured=True
        )
        result = engine.check(
            fields, font_measurements=fm,
            product_meta=ProductMeta(net_weight_grams=150),
        )
        font_v = [v for v in result.violations if v.rule_id == "R6_2"]
        self.assertEqual(len(font_v), 1)
        self.assertEqual(result.status, "PARTIAL")


class MisleadingClaimsTest(unittest.TestCase):
    def setUp(self):
        self.engine = ComplianceEngine()

    def test_flags_unsubstantiated_claim(self):
        fields = ExtractedFields(all_text="Tasty snack. India's No.1 brand!")
        result = self.engine.check(fields)
        r26 = [v for v in result.violations if v.rule_id == "R26"]
        self.assertTrue(r26)
        self.assertEqual(r26[0].severity, "MAJOR")

    def test_uses_raw_text_when_provided(self):
        fields = ExtractedFields(all_text="")
        result = self.engine.check(
            fields, raw_text="100% natural, clinically proven formula"
        )
        labels = {v.found_value.lower() for v in result.violations
                  if v.rule_id == "R26"}
        self.assertTrue(labels)

    def test_clean_label_has_no_r26(self):
        fields = ExtractedFields(all_text="Wheat flour, salt, water.")
        result = self.engine.check(fields)
        self.assertEqual(
            [v for v in result.violations if v.rule_id == "R26"], []
        )


class MRPPositionTest(unittest.TestCase):
    def setUp(self):
        self.engine = ComplianceEngine()

    def test_mrp_near_bottom_is_flagged(self):
        fields = ExtractedFields(mrp="MRP 10 (inclusive of all taxes)")
        result = self.engine.check(
            fields,
            field_bboxes={"mrp": {"x": 5, "y": 950, "w": 40, "h": 10}},
            image_height=1000,
        )
        r65 = [v for v in result.violations if v.rule_id == "R6_5"]
        self.assertEqual(len(r65), 1)
        self.assertIsNotNone(r65[0].evidence_bbox)

    def test_mrp_on_panel_is_ok(self):
        fields = ExtractedFields(mrp="MRP 10 (inclusive of all taxes)")
        result = self.engine.check(
            fields,
            field_bboxes={"mrp": {"x": 5, "y": 200, "w": 40, "h": 10}},
            image_height=1000,
        )
        self.assertEqual(
            [v for v in result.violations if v.rule_id == "R6_5"], []
        )

    def test_no_layout_no_r65(self):
        fields = ExtractedFields(mrp="MRP 10 (inclusive of all taxes)")
        result = self.engine.check(fields)
        self.assertEqual(
            [v for v in result.violations if v.rule_id == "R6_5"], []
        )


class ScoreTest(unittest.TestCase):
    def test_full_score(self):
        self.assertEqual(compute_compliance_score([]), 1.0)

    def test_critical_lowers_score(self):
        from app.services.datatypes import Violation

        v = [Violation(
            rule_id="R", rule_title="", violation_type="MISSING",
            severity="CRITICAL", finding="x",
        )]
        score = compute_compliance_score(v)
        self.assertAlmostEqual(score, round(1 - (2.0 / 16.0), 2))


if __name__ == "__main__":
    unittest.main()
