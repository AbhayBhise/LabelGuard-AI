# Backend Specification — LabelGuard AI

---

## API Overview

**Base URL:** `https://api.labelguard.in/v1`  
**Framework:** FastAPI (Python 3.11+)  
**Auth:** JWT Bearer tokens + OAuth2 Google SSO  
**Documentation:** Auto-generated OpenAPI at `/docs`

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory
│   ├── config.py                  # Settings (env vars)
│   ├── deps.py                    # Dependency injection (db, auth)
│   │
│   ├── routers/
│   │   ├── auth.py                # Login, OAuth, token refresh
│   │   ├── scans.py               # Core scan endpoints
│   │   ├── products.py            # Product repository
│   │   ├── reports.py             # Report generation + download
│   │   ├── violations.py          # Violation queries
│   │   ├── analytics.py           # Dashboard data
│   │   └── admin.py               # User + rule management
│   │
│   ├── services/
│   │   ├── image_processor.py     # Preprocessing pipeline
│   │   ├── ocr_engine.py          # PP-OCRv5 wrapper
│   │   ├── vlm_engine.py          # Qwen2-VL wrapper
│   │   ├── layout_engine.py       # LayoutLMv3 wrapper
│   │   ├── font_detector.py       # Font size measurement
│   │   ├── compliance_engine.py   # Rule checker
│   │   ├── report_generator.py    # PDF/DOCX generation
│   │   └── ecommerce_scraper.py   # URL scraper
│   │
│   ├── models/
│   │   ├── scan.py                # Pydantic models
│   │   ├── product.py
│   │   ├── violation.py
│   │   └── user.py
│   │
│   ├── db/
│   │   ├── session.py             # SQLAlchemy session
│   │   ├── base.py                # ORM base
│   │   └── migrations/            # Alembic migrations
│   │
│   ├── tasks/
│   │   └── inference_tasks.py     # Bull/Celery async tasks
│   │
│   └── utils/
│       ├── image_utils.py
│       ├── pdf_utils.py
│       └── validation_utils.py
│
├── ml_workers/
│   ├── ocr_worker/
│   │   ├── Dockerfile
│   │   └── server.py              # FastAPI micro-service
│   ├── vlm_worker/
│   │   ├── Dockerfile
│   │   └── server.py
│   └── layout_worker/
│       ├── Dockerfile
│       └── server.py
│
├── tests/
│   ├── test_ocr.py
│   ├── test_compliance.py
│   └── test_api.py
│
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API Endpoints

### Auth

```
POST /auth/login
Body: { email, password }
Returns: { access_token, refresh_token, user }

POST /auth/google
Body: { google_id_token }
Returns: { access_token, refresh_token, user }

POST /auth/refresh
Body: { refresh_token }
Returns: { access_token }

POST /auth/logout
(Invalidates token in Redis)
```

---

### Scans

```
POST /scans
Content-Type: multipart/form-data
Body:
  - images[]: File[]          (1-10 images)
  - product_name?: string
  - net_weight?: number
  - category?: string
  - is_imported?: boolean
  - source?: string           (web | api)
Returns:
  { scan_id, status: "processing", estimated_seconds: 8 }

POST /scans/url
Body: { url: string, source_platform?: string }
Returns: { scan_id, status: "processing" }

GET /scans/{scan_id}
Returns: Full scan result with fields + violations + images

GET /scans/{scan_id}/status
Returns: { status: "processing" | "complete" | "failed", progress: 0-100 }

GET /scans
Query: page, limit, status, officer_id, date_from, date_to
Returns: Paginated scan list

DELETE /scans/{scan_id}
(Soft delete — admin only)
```

**Scan Result Schema:**
```json
{
  "scan_id": "uuid",
  "scanned_at": "ISO timestamp",
  "overall_status": "NON_COMPLIANT",
  "compliance_score": 0.5,
  "product": {
    "name": "Lay's Classic Salted",
    "barcode": "8901491503573",
    "category": "food"
  },
  "extracted_fields": [
    {
      "field": "mrp",
      "value": "MRP ₹20",
      "confidence": 0.97,
      "bounding_box": { "x": 120, "y": 340, "w": 80, "h": 18 },
      "extraction_method": "ocr"
    }
  ],
  "violations": [
    {
      "rule_id": "R6_1_f",
      "rule_title": "MRP Declaration",
      "violation_type": "FAIL_CONTENT",
      "severity": "CRITICAL",
      "finding": "Missing 'inclusive of all taxes' clause",
      "found_value": "MRP ₹20",
      "expected_format": "MRP ₹20 (Inclusive of all taxes)",
      "evidence_bbox": { "x": 120, "y": 340, "w": 80, "h": 18 }
    }
  ],
  "annotated_image_url": "https://..."
}
```

---

### Products

```
GET /products
Query: search, category, status, page, limit
Returns: Paginated product list

GET /products/{product_id}
Returns: Product + all scan history

GET /products/{product_id}/compliance-history
Returns: Timeline of compliance status changes

POST /products/{product_id}/flag
Body: { reason, notes }
(Flag for priority re-inspection)
```

---

### Reports

```
GET /reports/{scan_id}/pdf
Returns: Binary PDF stream
Headers: Content-Disposition: attachment; filename="report-{scan_id}.pdf"

GET /reports/{scan_id}/docx
Returns: Binary DOCX stream

POST /reports/{scan_id}/share
Body: { recipient_email, message? }
Returns: { share_link, expires_at }

GET /reports
Query: officer_id, date_from, date_to, status
Returns: Paginated report list
```

---

### Analytics

```
GET /analytics/summary
Query: from, to, state?, district?
Returns: { total_scans, compliant, non_compliant, partial, top_violations[] }

GET /analytics/violations-by-rule
Query: from, to, category?
Returns: [{ rule_id, rule_title, count, percentage }]

GET /analytics/violations-by-region
Returns: [{ state, district, violation_count, compliance_rate }]

GET /analytics/brand-compliance
Query: from, to
Returns: [{ brand, total_scans, violation_rate, most_common_violation }]

GET /analytics/category-compliance
Returns: [{ category, compliance_rate, avg_score }]
```

---

## ML Pipeline (Service Layer)

### `image_processor.py`

```python
class ImageProcessor:
    async def preprocess(self, image_bytes: bytes) -> ProcessedImage:
        """
        Steps:
        1. Load with PIL / OpenCV
        2. Deskew (Hough transform)
        3. Denoise (fastNlMeansDenoisingColored)
        4. Enhance contrast (CLAHE)
        5. Perspective correction (findContours → homography)
        6. Return cleaned image + quality metrics
        """
    
    async def detect_label_regions(self, image: ProcessedImage) -> List[LabelRegion]:
        """
        YOLOv8 inference → bounding boxes of label regions
        Returns sorted by area (largest = main label)
        """
    
    async def stitch_panorama(self, images: List[bytes]) -> bytes:
        """
        Multi-image stitching for full label coverage
        Uses OpenCV Stitcher API
        """
```

### `ocr_engine.py`

```python
class OCREngine:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            use_gpu=torch.cuda.is_available(),
            show_log=False
        )
    
    async def extract(self, image: np.ndarray) -> OCRResult:
        """
        Returns: List of { text, bbox, confidence }
        bbox format: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        """
        result = self.ocr.ocr(image, cls=True)
        return self._parse_result(result)
    
    def _parse_result(self, raw) -> OCRResult:
        words = []
        for line in raw[0]:
            bbox, (text, confidence) = line
            words.append(Word(
                text=text,
                bbox=BoundingBox.from_quad(bbox),
                confidence=confidence
            ))
        return OCRResult(words=words)
```

### `vlm_engine.py`

```python
class VLMEngine:
    EXTRACTION_PROMPT = """
    You are a compliance checker for Indian packaged commodities.
    Extract the following fields from this product label image.
    Return ONLY a valid JSON object with these exact keys.
    If a field is not present, use null.
    
    Fields to extract:
    - manufacturer_name: string
    - manufacturer_address: string  
    - net_quantity: string (include unit, e.g., "150g", "500ml")
    - mrp: string (full declaration as seen)
    - manufacture_date: string (as printed)
    - expiry_date: string (as printed, null if not required)
    - consumer_care_contact: string
    - country_of_origin: string (null if not imported)
    - fssai_license: string (for food products)
    - batch_lot_number: string
    - any_other_declarations: string
    """
    
    async def extract_fields(self, image_bytes: bytes) -> dict:
        # Call Qwen2-VL via local inference or API
        response = await self._call_vlm(image_bytes, self.EXTRACTION_PROMPT)
        return self._parse_json_response(response)
```

### `compliance_engine.py`

```python
class ComplianceEngine:
    def check(
        self, 
        extracted_fields: ExtractedFields,
        font_measurements: FontMeasurements,
        product_meta: ProductMeta
    ) -> ComplianceResult:
        
        violations = []
        
        # Rule 6(1)(a) — Manufacturer name + address
        violations += self._check_manufacturer(extracted_fields)
        
        # Rule 6(1)(c) — Net quantity
        violations += self._check_net_quantity(extracted_fields)
        
        # Rule 6(1)(f) — MRP
        violations += self._check_mrp(extracted_fields)
        
        # Rule 6(1)(e) — Manufacture date
        violations += self._check_manufacture_date(extracted_fields)
        
        # Rule 6(1)(k) — Consumer care
        violations += self._check_consumer_care(extracted_fields)
        
        # Rule 6(2) — Font size
        violations += self._check_font_sizes(
            font_measurements, product_meta.net_weight
        )
        
        # Rule 6(6) — Country of origin (imports only)
        if product_meta.is_imported:
            violations += self._check_country_of_origin(extracted_fields)
        
        # Compute score
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
            score=self._compute_score(violations)
        )
    
    def _check_mrp(self, fields: ExtractedFields) -> List[Violation]:
        violations = []
        if not fields.mrp:
            violations.append(Violation(
                rule_id="R6_1_f",
                violation_type="FAIL_MISSING",
                severity="CRITICAL",
                finding="MRP declaration not found on label"
            ))
        elif not re.search(
            r'inclusive\s+of\s+all\s+tax', 
            fields.mrp.lower()
        ):
            violations.append(Violation(
                rule_id="R6_1_f",
                violation_type="FAIL_CONTENT",
                severity="CRITICAL",
                finding=f"MRP found as '{fields.mrp}' but missing 'inclusive of all taxes' clause",
                found_value=fields.mrp,
                expected_format="MRP ₹X.XX (Inclusive of all taxes)"
            ))
        return violations
    
    def _check_font_sizes(
        self, 
        measurements: FontMeasurements, 
        net_weight_grams: float
    ) -> List[Violation]:
        # LM Rules 2011, Rule 6(2) requirements
        if net_weight_grams <= 200:
            min_height_mm = 1.0
        elif net_weight_grams <= 1000:
            min_height_mm = 2.0
        elif net_weight_grams <= 5000:
            min_height_mm = 4.0
        else:
            min_height_mm = 6.0
        
        violations = []
        for field, height_mm in measurements.field_heights.items():
            if height_mm < min_height_mm:
                violations.append(Violation(
                    rule_id="R6_2",
                    violation_type="FAIL_FORMAT",
                    severity="MAJOR",
                    finding=f"{field} font height {height_mm:.2f}mm < required {min_height_mm}mm"
                ))
        return violations
```

### `font_detector.py`

```python
class FontSizeDetector:
    BARCODE_MODULE_WIDTH_MM = 0.33  # ISO 15416 standard minimum
    
    def compute_px_per_mm(self, image: np.ndarray) -> Optional[float]:
        """
        Strategy 1: Detect barcode → use known module width as reference
        Strategy 2: Detect standard dimensions (credit-card-sized label)
        Strategy 3: Fallback — return None (report as "unable to measure")
        """
        barcode = self._detect_barcode(image)
        if barcode:
            module_width_px = self._measure_barcode_module_width(barcode)
            return module_width_px / self.BARCODE_MODULE_WIDTH_MM
        return None
    
    def measure_text_height(
        self, 
        word: Word, 
        px_per_mm: float
    ) -> float:
        """
        Uses bounding box height as character height proxy.
        height_px / px_per_mm = height_mm
        """
        return word.bbox.height / px_per_mm
```

---

## Report Generator

```python
class ReportGenerator:
    def generate_pdf(self, scan_result: ScanResult) -> bytes:
        """
        Sections:
        1. Header (logo, scan metadata, officer info)
        2. Product identification (name, barcode, image)
        3. Compliance summary (status badge, score, violation count)
        4. Annotated label image (color-coded bounding boxes)
        5. Violation table (rule | finding | severity | evidence)
        6. Extracted fields table (all detected values)
        7. Recommendations (what manufacturer needs to fix)
        8. Officer declaration section (signature block)
        9. Audit metadata (model versions, confidence scores, timestamps)
        """
        doc = ReportLabDocument(...)
        # Build with ReportLab platypus
        return doc.build()
    
    def annotate_image(
        self, 
        image: np.ndarray, 
        violations: List[Violation],
        extracted_fields: List[ExtractedField]
    ) -> np.ndarray:
        """
        Draw colored bounding boxes:
        - GREEN: compliant field
        - RED: violation field  
        - AMBER: partial/warning
        - WHITE dashed: not found (expected location)
        """
```

---

## E-Commerce Scraper

```python
class EcommerceScraper:
    SUPPORTED_PLATFORMS = {
        'amazon.in': AmazonIndiaScraper,
        'flipkart.com': FlipkartScraper,
        'bigbasket.com': BigBasketScraper,
    }
    
    async def fetch_label_images(self, url: str) -> List[ImageResult]:
        """
        1. Detect platform from URL
        2. Playwright headless browser → load product page
        3. Extract all product gallery images
        4. Run label classifier (MobileNet fine-tuned) on each image
        5. Return images with is_label_confidence > 0.7
        """
        platform = self._detect_platform(url)
        scraper = self.SUPPORTED_PLATFORMS[platform]()
        images = await scraper.fetch_all_images(url)
        return await self._filter_label_images(images)
```

---

## Authentication & RBAC

```python
ROLE_PERMISSIONS = {
    "OFFICER": [
        "scan:create", "scan:read_own", "report:read_own", 
        "report:download_own", "product:read"
    ],
    "SUPERVISOR": [
        "scan:create", "scan:read_all", "report:read_all",
        "report:download_all", "product:read", "analytics:read",
        "violation:assign"
    ],
    "ADMIN": [
        "*",  # Full access
        "user:manage", "rule:configure", "analytics:export"
    ],
    "VIEWER": [
        "scan:read_all", "report:read_all", "analytics:read"
    ]
}
```

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/labelguard

# Redis
REDIS_URL=redis://localhost:6379

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=labelguard-media

# ML Workers
OCR_WORKER_URL=http://localhost:8001
VLM_WORKER_URL=http://localhost:8002
LAYOUT_WORKER_URL=http://localhost:8003

# External VLM (if not self-hosting)
GROQ_API_KEY=...
TOGETHER_API_KEY=...

# Auth
JWT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# App
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000
```

---

## Testing Strategy

```
tests/
├── unit/
│   ├── test_compliance_engine.py    # Test every rule with mock data
│   ├── test_font_detector.py        # Test px/mm computation
│   └── test_report_generator.py    # Test PDF generation
│
├── integration/
│   ├── test_scan_pipeline.py        # End-to-end scan with real images
│   └── test_api_endpoints.py        # API contract tests
│
└── fixtures/
    ├── compliant_label.jpg           # Known-good label
    ├── missing_mrp_label.jpg        # Known violation
    └── small_font_label.jpg         # Font size violation
```

**Key Unit Tests:**
- MRP with/without "inclusive of all taxes" — 8 test cases
- Net quantity format validation — 12 test cases  
- Manufacture date format validation — 10 test cases
- Font size threshold at 200g/1kg/5kg boundaries
- Manufacturer address completeness scoring
