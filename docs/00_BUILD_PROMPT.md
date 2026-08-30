# ANTIGRAVITY BUILD PROMPT — LabelGuard AI
## SIH 2025 Problem Statement 26034

---

> **HOW TO USE THIS FILE:**  
> Read this entire file before writing a single line of code. This is the complete context document. Use your MCP tools, coding skills, and file system access as described below. Build one module at a time, in the order specified.

---

## Who You Are Building For

**Developer:** Abhay (full-stack + AI/ML, targeting fresher SIH win)  
**Competition:** Smart India Hackathon 2025  
**PS:** Ministry of Consumer Affairs — PS ID 26034  
**Goal:** Build a production-quality MVP that wins SIH by being technically superior to all competing teams.

---

## What You Are Building

**LabelGuard AI** — An AI-powered compliance checking system for packaged commodities under Legal Metrology (Packaged Commodities) Rules, 2011.

**Core Value Proposition:** An enforcement officer takes a photo of any packaged product → AI reads the label → system checks every required declaration against LM Rules 2011 → generates a legally defensible PDF compliance report in <10 seconds.

**This is not just an OCR tool.** It is:
1. A multimodal AI pipeline (OCR + VLM + Layout model)
2. A regulatory rule engine (15+ rules from LM PC Rules 2011)
3. An enforcement intelligence platform (dashboard, analytics, e-commerce scanning)
4. An offline-capable mobile inspection tool

---

## Files You Have Been Given

Read all of these before starting:

| File | Contents |
|---|---|
| `01_research_papers.md` | 17 research papers with working links — understand the tech choices |
| `02_problem_and_solution.md` | Full PS, mandatory declarations, our differentiators |
| `03_architecture.md` | Complete system architecture with DB schema and ML pipeline |
| `04_frontend_spec.md` | All pages, components, layouts for web + mobile |
| `05_backend_spec.md` | All API endpoints, service code stubs, compliance rules |
| `06_legal_rules.md` | Full LM (PC) Rules 2011 mapped to machine-checkable rules |

---

## Your MCP Tools and When to Use Them

```
MCP: Google Drive
→ Use for: Storing generated reports, reading any uploaded reference docs
→ When: After generating PDF reports, save to Drive for sharing

MCP: (check your connected MCPs)
→ For file system, terminal access, code execution
→ Use bash extensively for: pip installs, running tests, starting servers
```

**Available Skills to Invoke:**
- `frontend-design` skill → invoke before building ANY UI component for design tokens
- `pdf` skill → invoke before building the report generator (PDF generation)
- `docx` skill → invoke before building DOCX report export

---

## Build Order (Strict — Follow This)

### Phase 1: Foundation (Day 1 morning)

**Step 1.1 — Project Scaffolding**
```bash
# Backend
mkdir labelguard && cd labelguard
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary redis pillow opencv-python paddleocr paddlepaddle reportlab python-jose pydantic-settings

# Frontend  
npx create-next-app@latest web --typescript --tailwind --app
cd web && npx shadcn-ui@latest init
```

**Step 1.2 — Database + Migrations**
- Create all tables from `03_architecture.md` → Database Schema section
- Use Alembic for migrations
- Seed: 5 compliance rules, 1 admin user, 2 test products

**Step 1.3 — Auth System**
- JWT login/refresh endpoints
- RBAC middleware (4 roles: OFFICER, SUPERVISOR, ADMIN, VIEWER)
- Google OAuth integration

---

### Phase 2: Core ML Pipeline (Day 1 afternoon)

**Step 2.1 — Image Preprocessor**
Build `services/image_processor.py`:
- OpenCV-based deskew + denoise + CLAHE
- Label region detection using YOLOv8 (`pip install ultralytics`)
- Use the `yolov8n.pt` pretrained model first; we'll fine-tune later

**Step 2.2 — OCR Engine**
Build `services/ocr_engine.py`:
- PaddleOCR wrapper (PP-OCRv5)
- Returns: List of `{text, bbox_xywh, confidence}`
- Test with sample Indian product label images (download 5 from OpenFoodFacts or similar)

**Step 2.3 — VLM Engine**
Build `services/vlm_engine.py`:
- Primary: Groq API with `llama-3.2-90b-vision-preview` (fastest free VLM)
- Fallback: Together AI `meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo`
- Use the exact prompt from `05_backend_spec.md → vlm_engine.py`
- Parse JSON response with error handling

**Step 2.4 — Font Size Detector**
Build `services/font_detector.py`:
- Barcode detection using `pip install pyzbar`
- px/mm computation from barcode module width
- Text height measurement from OCR bounding boxes
- Test with a known-size image

---

### Phase 3: Compliance Engine (Day 1 evening)

**Step 3.1 — Rule Registry**
Populate `compliance_rules` table with all rules from `06_legal_rules.md`

**Step 3.2 — Compliance Checker**
Build `services/compliance_engine.py`:
- Implement every rule from `05_backend_spec.md`
- Start with: MRP (R6_1_f), Manufacturer (R6_1_a), Net Qty (R6_1_c), Date (R6_1_e)
- Add font size (R6_2) after font detector works

**Step 3.3 — Integration Test**
```python
# Test with 3 known labels:
# 1. A fully compliant label → expect COMPLIANT
# 2. A label missing MRP clause → expect NON_COMPLIANT, R6_1_f violation
# 3. A label with small font → expect PARTIAL, R6_2 violation
```

---

### Phase 4: API + Report Generator (Day 2 morning)

**Step 4.1 — Scan API**
Build `routers/scans.py`:
- POST /scans (multipart upload)
- GET /scans/{id} (with full result)
- GET /scans/{id}/status (polling endpoint)

**Step 4.2 — Async Processing**
- Use FastAPI BackgroundTasks for MVP (upgrade to Celery/Bull later)
- Flow: Accept image → return scan_id immediately → process in background → update DB

**Step 4.3 — Report Generator**
Build `services/report_generator.py`:
- **Read the `pdf` skill first** before writing any code here
- PDF with: header, product info, annotated image, violation table, recommendations
- DOCX version (simpler, no image annotation)
- Store in MinIO, return presigned URL

---

### Phase 5: Frontend (Day 2 afternoon)

**Before writing any UI: Read the `frontend-design` skill**

**Step 5.1 — Layout Shell**
- `app/(dashboard)/layout.tsx`: Sidebar + topbar
- Sidebar: Logo, nav links (Dashboard, New Scan, Products, Violations, Analytics, Settings)
- Topbar: Search, notifications, user avatar

**Step 5.2 — Dashboard Page**
- 4 stat cards (total scans, compliant, non-compliant, pending)
- Compliance donut chart (use Recharts)
- Recent scans table with status badges

**Step 5.3 — New Scan Page (Most Important)**
- ImageDropzone (react-dropzone)
- Processing steps indicator (animated)
- Redirect to scan result on completion

**Step 5.4 — Scan Result Page (Most Important)**
- Two-column layout
- ViolationAccordion — expandable per-rule results
- AnnotatedImageViewer — label image with bounding boxes overlay (use Konva.js or fabric.js)
- ExtractedFieldsTable
- Download PDF/DOCX buttons

**Step 5.5 — Analytics Dashboard**
- Line chart: violations over time
- Bar chart: violations by rule (most common violations)
- Simple table: top non-compliant brands

---

### Phase 6: Polish for Demo (Day 3)

**Step 6.1 — Demo Data**
Create seed script with:
- 20 realistic scanned products (mix of compliant and non-compliant)
- 3 officer accounts, 1 supervisor, 1 admin
- 50+ violations across different rules

**Step 6.2 — E-Commerce Scraper (Demo Mode)**
- Build the URL input UI
- For demo: use pre-cached images (don't actually scrape during demo)
- Show the concept working with 5-10 pre-processed e-commerce products

**Step 6.3 — Mobile App (if time permits)**
- Use Expo with React Native
- Just: Camera screen → Processing screen → Result screen
- Use the web API (same backend)

---

## Key Technical Decisions to Defend in Demo

### "Why PP-OCRv5 and not Tesseract?"
→ PaddleOCR 3.0 (arXiv 2507.05595) supports multilingual including Hindi/Devanagari script natively, is 5x faster than Tesseract on dense text, and has an integrated layout analysis module. Tesseract fails on stylized packaging fonts.

### "Why a VLM as second-pass instead of just OCR?"
→ OCR gives raw text; VLM gives semantic understanding. If OCR extracts "₹ 125 incl taxes" in 3 separate word bounding boxes, a rule engine checking for "inclusive of all taxes" substring would fail. The VLM understands the semantic meaning and correctly identifies MRP compliance. Backed by Scientific Reports paper on VLM-based document extraction (2026).

### "How do you measure font size from an image?"
→ Barcode-based px/mm calibration. ISO 15416 defines barcode module width standards. We detect the barcode, measure its module width in pixels, compute px/mm ratio, then measure text bounding box heights. This is novel — no other team will do this. Reference: Fateh et al. 2024 document layout analysis paper.

### "What makes your compliance check legally defensible?"
→ Every violation report includes: (a) the exact bounding box in the image where the violation was detected, (b) the extracted text value, (c) the specific rule sub-section violated with its text, (d) model confidence scores, (e) officer identity + timestamp + GPS. This creates a complete chain of evidence.

### "How does e-commerce compliance work?"
→ We scrape the product listing page using Playwright, extract all gallery images, run a binary classifier (fine-tuned MobileNet) to identify which images show the actual label vs lifestyle/hero shots, then run the standard compliance pipeline. DoCA's biggest enforcement gap is e-commerce — no physical inspector can visit Amazon's virtual catalog.

---

## Demo Script (5-minute SIH presentation)

```
0:00 — Problem statement + why manual inspection fails (1M+ SKUs)
0:45 — Open the web app as "Officer Sharma"
1:00 — Upload image of a common product (Maggi noodles packet)
1:10 — Watch the processing steps animate
1:30 — Show compliance result: 2 violations found
       → MRP missing "inclusive of all taxes"
       → Consumer care contact missing
1:50 — Show annotated image with red bounding boxes
2:10 — Download PDF report (show its structure)
2:30 — Switch to Analytics dashboard
       → "5,234 products scanned this month across Maharashtra"
       → "Most violated rule: R6(1)(f) — MRP declaration (67% of violations)"
2:50 — Show e-commerce URL input, paste Amazon link, show pre-processed result
3:20 — Show mobile app (or screen recording)
3:40 — Technical architecture diagram (from 03_architecture.md)
4:00 — "We solve the manual inspection bottleneck: from 100 products/officer/day to 5,000+"
4:20 — Q&A / judge questions
```

---

## SIH Evaluation Criteria Mapping

| Criterion | How We Win |
|---|---|
| **Innovation** | Font size measurement via barcode calibration; VLM+OCR hybrid; e-commerce scanning |
| **Feasibility** | All tech is open-source; deployable on ₹8,000/mo cloud server; offline mobile app |
| **Impact** | Direct DoCA use case; measurable: X violations caught per day |
| **Completeness** | All 8 functional requirements from PS addressed |
| **Technical Depth** | 17 research papers; 3 ML models; custom compliance engine |
| **User Experience** | Clean government UI; PDF reports; role-based access |

---

## Repo Structure to Create

```
labelguard/
├── backend/               ← FastAPI + ML pipeline
├── web/                   ← Next.js frontend
├── mobile/                ← React Native (optional)
├── ml_models/             ← Model weights + configs
├── docs/
│   ├── 00_BUILD_PROMPT.md
│   ├── 01_research_papers.md
│   ├── 02_problem_and_solution.md
│   ├── 03_architecture.md
│   ├── 04_frontend_spec.md
│   ├── 05_backend_spec.md
│   └── 06_legal_rules.md
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## START HERE

1. Read all 6 markdown files completely
2. Set up the monorepo structure
3. Start with Phase 1 (scaffolding + database)
4. At each phase: build → test → commit → move to next
5. Use the research papers to justify every technical choice when asked

**Build it. Win it. Ship it.**
