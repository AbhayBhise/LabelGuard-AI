# System Architecture — LabelGuard AI

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Web App     │  │  Mobile App      │  │  API (3rd Party)     │  │
│  │  (Next.js)   │  │  (React Native)  │  │  E-commerce Partners │  │
│  └──────┬───────┘  └────────┬─────────┘  └──────────┬───────────┘  │
└─────────┼───────────────────┼────────────────────────┼─────────────┘
          │                   │                        │
          └───────────────────┴────────────────────────┘
                              │ HTTPS / REST
┌─────────────────────────────▼───────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                       │
│   Auth (JWT/OAuth2) │ Rate Limiting │ Request Routing │ Logging     │
└────────┬──────────────────────┬──────────────────────┬──────────────┘
         │                      │                      │
┌────────▼────────┐  ┌──────────▼──────────┐  ┌───────▼────────────┐
│  Image          │  │  Compliance         │  │  Report            │
│  Processing     │  │  Engine             │  │  Generator         │
│  Service        │  │  Service            │  │  Service           │
└────────┬────────┘  └──────────┬──────────┘  └───────┬────────────┘
         │                      │                      │
┌────────▼──────────────────────▼──────────────────────▼────────────┐
│                         MESSAGE QUEUE (Redis/Bull)                 │
│              Async job processing for heavy ML inference           │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────┐
│                         ML INFERENCE LAYER                         │
│                                                                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  OCR Engine     │  │  VLM Engine      │  │  Layout Engine   │  │
│  │  PP-OCRv5       │  │  Qwen2-VL        │  │  LayoutLMv3      │  │
│  │  (primary)      │  │  (semantic)      │  │  (spatial)       │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                    │
│  ┌─────────────────┐  ┌──────────────────┐                        │
│  │  Font Size      │  │  Label Region    │                        │
│  │  Detector       │  │  Segmentor       │                        │
│  │  (custom)       │  │  (YOLOv8)        │                        │
│  └─────────────────┘  └──────────────────┘                        │
└────────────────────────────────────────────────────────────────────┘
         │
┌────────▼───────────────────────────────────────────────────────────┐
│                         DATA LAYER                                 │
│  ┌────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  PostgreSQL    │  │  Redis Cache    │  │  S3 / MinIO         │ │
│  │  (products,    │  │  (session,      │  │  (images, reports,  │ │
│  │   violations,  │  │   scan cache)   │  │   annotated PDFs)   │ │
│  │   users)       │  │                 │  │                     │ │
│  └────────────────┘  └─────────────────┘  └─────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Service Breakdown

### 1. Image Processing Service

**Responsibilities:**
- Accept image upload (JPEG/PNG/HEIC/WebP), URL, or base64
- Image preprocessing: deskew, denoise, enhance contrast, correct perspective
- Multi-angle image stitching (for mobile panorama scans)
- Label region detection (isolate label from product background using YOLOv8)
- Image quality assessment (blur detection, glare detection)
- Store processed images in S3/MinIO

**Tech:** Python, FastAPI, OpenCV, Pillow, YOLOv8 (Ultralytics), boto3

**Key Algorithm — Label Region Segmentation:**
```
Input: Raw product image
Step 1: YOLOv8 (custom fine-tuned) → detect "label" regions (bounding boxes)
Step 2: Perspective correction (homography transform if label is at angle)
Step 3: CLAHE (Contrast Limited Adaptive Histogram Equalization) for readability
Step 4: Adaptive thresholding for text enhancement
Output: Cleaned label image + confidence score
```

---

### 2. ML Inference Layer

#### 2a. OCR Engine (Primary — PP-OCRv5)
- Multilingual: English + Hindi + regional scripts
- Outputs: Text + bounding boxes + confidence scores per word
- Handles: Small fonts, curved text, dense layouts

#### 2b. VLM Engine (Semantic Fallback — Qwen2-VL)
- Structured extraction via prompt engineering:
  ```
  "From this product label image, extract the following fields as JSON:
   manufacturer_name, manufacturer_address, net_quantity, mrp, 
   manufacture_date, expiry_date, consumer_care_contact, 
   country_of_origin, batch_number, fssai_license"
  ```
- Zero-shot capable — no per-product-category training needed
- Acts as validator for OCR output + extracts fields OCR may structurally miss

#### 2c. Layout Engine (LayoutLMv3 fine-tuned)
- Takes OCR word positions + label image → predicts semantic role of each text region
- Identifies: "this text block is MRP", "this is manufacturer address", etc.
- Enables spatial compliance checks (e.g., MRP must be on principal display panel)

#### 2d. Font Size Detector
- **Input:** Bounding boxes of extracted text (from OCR), product net weight
- **Algorithm:**
  1. Identify barcode in image (known standard width = reference calibration)
  2. Compute px/mm ratio using barcode module width (ISO 15416 standard = 0.33mm module)
  3. If no barcode: use standard A4/letter proportion heuristic or manual calibration
  4. For each text bounding box: height_px / px_per_mm = character_height_mm
  5. Compare vs Rule 6(2): ≥1mm for packs ≤200g/ml, ≥2mm for packs 200g-1kg, ≥4mm for >1kg
- **Output:** Per-field font compliance status + actual measured height

---

### 3. Compliance Engine Service

The core rule-based checker. Takes structured field data from ML layer and validates against LM (PC) Rules 2011.

#### Rule Registry (fully configurable via DB)

```python
COMPLIANCE_RULES = {
    "R6_1_a": {
        "field": "manufacturer_name_address",
        "description": "Name and address of manufacturer/packer/importer",
        "check": "presence + address_completeness",
        "severity": "CRITICAL"
    },
    "R6_1_c": {
        "field": "net_quantity",
        "description": "Net quantity in standard units",
        "check": "presence + format_validation + unit_check",
        "severity": "CRITICAL"
    },
    "R6_1_f": {
        "field": "mrp",
        "description": "Maximum Retail Price inclusive of all taxes",
        "check": "presence + 'inclusive of all taxes' substring + numeric_format",
        "severity": "CRITICAL"
    },
    "R6_1_e": {
        "field": "manufacture_date",
        "description": "Month and year of manufacture/packing",
        "check": "presence + date_format_MM_YYYY",
        "severity": "CRITICAL"
    },
    "R6_1_k": {
        "field": "consumer_care",
        "description": "Consumer care address/phone/email",
        "check": "presence + contact_info_pattern",
        "severity": "MAJOR"
    },
    "R6_2": {
        "field": "all_text",
        "description": "Font size requirements",
        "check": "font_size_compliance_by_pack_weight",
        "severity": "MAJOR"
    },
    "R6_5": {
        "field": "mrp",
        "description": "MRP on principal display panel",
        "check": "mrp_panel_position",
        "severity": "MAJOR"
    },
    "R6_6": {
        "field": "country_of_origin",
        "description": "Country of origin for imported goods",
        "check": "presence_if_imported",
        "severity": "CRITICAL (if imported)"
    },
}
```

#### Compliance Decision Tree
```
For each rule:
  → PASS: Field present, format correct, value valid
  → FAIL_MISSING: Field not found in extracted data
  → FAIL_FORMAT: Field present but format non-compliant
  → FAIL_CONTENT: Field present, format ok, content invalid
  → WARN_PARTIAL: Partially compliant (e.g., address present but incomplete)
  → NOT_APPLICABLE: Rule doesn't apply to this product category
```

---

### 4. Report Generator Service

**Output formats:**
- PDF (annotated images + violation table + officer signature section)
- DOCX (editable for officer amendments)
- JSON (for API consumers / dashboards)

**PDF Report Sections:**
1. Header: Inspection date, officer name, location, scan ID
2. Product Identity: Name, barcode, image thumbnail
3. Compliance Summary: PASS / FAIL / PARTIAL with % score
4. Violation Table: Rule ID | Field | Finding | Evidence
5. Annotated Images: Original label with colored bounding boxes (green=pass, red=fail)
6. Recommendations: Required corrections per violation
7. Audit Trail: Scan metadata, model confidence scores, processing timestamps

---

### 5. E-Commerce Scraper Module

**Supported platforms:** Amazon India, Flipkart, Meesho, BigBasket, Blinkit  
**Method:**
- URL input → Playwright headless browser → capture product gallery images
- Computer vision classifier: "is this a label/packaging image or lifestyle/hero image?"
- Feed label images into standard compliance pipeline
- **Rate-limited and robots.txt respecting** (for production; demo uses cached data)

---

## Database Schema (PostgreSQL)

```sql
-- Products
CREATE TABLE products (
    id UUID PRIMARY KEY,
    barcode VARCHAR(50),
    product_name TEXT,
    brand TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Scans
CREATE TABLE scans (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    officer_id UUID REFERENCES users(id),
    scanned_at TIMESTAMP,
    location_lat DECIMAL,
    location_lng DECIMAL,
    source VARCHAR(50), -- 'mobile', 'web', 'api', 'ecommerce'
    raw_image_url TEXT,
    processed_image_url TEXT,
    overall_status VARCHAR(20) -- 'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL'
);

-- Extracted Fields
CREATE TABLE extracted_fields (
    id UUID PRIMARY KEY,
    scan_id UUID REFERENCES scans(id),
    field_name VARCHAR(100),
    extracted_value TEXT,
    confidence DECIMAL,
    bounding_box JSONB, -- {x, y, w, h}
    extraction_method VARCHAR(50) -- 'ocr', 'vlm', 'layout'
);

-- Violations
CREATE TABLE violations (
    id UUID PRIMARY KEY,
    scan_id UUID REFERENCES scans(id),
    rule_id VARCHAR(20), -- e.g., 'R6_1_f'
    rule_description TEXT,
    violation_type VARCHAR(30), -- MISSING, FORMAT, CONTENT, FONT_SIZE
    severity VARCHAR(20), -- CRITICAL, MAJOR, MINOR
    finding TEXT,
    evidence_image_url TEXT,
    created_at TIMESTAMP
);

-- Users (Role-based)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    role VARCHAR(30), -- 'OFFICER', 'SUPERVISOR', 'ADMIN', 'VIEWER'
    state VARCHAR(50),
    district VARCHAR(50),
    department TEXT,
    created_at TIMESTAMP
);

-- Compliance Rules Registry
CREATE TABLE compliance_rules (
    rule_id VARCHAR(20) PRIMARY KEY,
    rule_title TEXT,
    description TEXT,
    severity VARCHAR(20),
    check_type VARCHAR(50),
    is_active BOOLEAN,
    applies_to_categories TEXT[] -- null = all
);
```

---

## Tech Stack Summary

| Layer | Technology | Reason |
|---|---|---|
| Frontend (Web) | Next.js 14 (App Router) | SSR, file uploads, dashboard |
| Frontend (Mobile) | React Native + Expo | Cross-platform, offline support |
| API Gateway | FastAPI (Python) | ML ecosystem native, async |
| OCR Primary | PP-OCRv5 (PaddleOCR 3.0) | Best multilingual + Hindi support |
| VLM Extraction | Qwen2-VL-7B (quantized) | Open-weight, structured output |
| Layout Model | LayoutLMv3 fine-tuned | Layout-aware field classification |
| Object Detection | YOLOv8 (Ultralytics) | Label region segmentation |
| Database | PostgreSQL + pgvector | Relational + vector search |
| Cache | Redis | Session, job queue, scan cache |
| Object Storage | MinIO (S3-compatible) | Images, PDFs, reports |
| Job Queue | Bull (Redis-backed) | Async ML inference jobs |
| PDF Generation | ReportLab + WeasyPrint | Rich annotated PDF reports |
| Auth | JWT + OAuth2 (Google SSO) | Role-based access |
| Deployment | Docker + docker-compose | Portable, easy demo |
| CI/CD | GitHub Actions | Automated testing + deploy |

---

## Deployment Architecture (MVP)

```
Single VPS / Cloud VM:
├── nginx (reverse proxy + SSL)
├── Next.js (web frontend, port 3000)
├── FastAPI (API server, port 8000)
├── PostgreSQL (port 5432)
├── Redis (port 6379)
├── MinIO (port 9000)
└── ML inference workers (port 8001-8003)
    ├── Worker 1: OCR (PP-OCRv5)
    ├── Worker 2: VLM (Qwen2-VL)
    └── Worker 3: Layout + Font Size
```

**Minimum server spec:** 16 vCPU, 32GB RAM, 1x A10/T4 GPU (for VLM)  
**Without GPU:** Use Qwen2-VL via Groq API / Together AI for VLM; OCR and layout run on CPU fine.
