# LabelGuard AI

**The AI Enforcement Officer for Every Package in India**

An AI-powered compliance checking system for packaged commodities under the
**Legal Metrology (Packaged Commodities) Rules, 2011** — built for the Smart
India Hackathon 2025 (PS 26034, Ministry of Consumer Affairs / DoCA).

An enforcement officer takes a photo of any packaged product → AI reads the
label → the system checks every required declaration against LM (PC) Rules
2011 → generates a legally defensible PDF compliance report in <10 seconds.

---

## Why LabelGuard Is Different

1. **Multimodal AI pipeline** — PP-OCRv5 (OCR) + Qwen2-VL (VLM semantic
   extraction) + LayoutLMv3 (layout) cross-validated to eliminate
   single-point OCR failure.
2. **Font-size compliance** — pixel-per-mm calibration using barcode module
   width (ISO 15416 reference) to measure text heights against Rule 6(2)
   minimums (1mm / 2mm / 4mm / 6mm).
3. **E-commerce scraping** — URL ingestion for Amazon/Flipkart/etc. to check
   online listings (DoCA's biggest enforcement gap).
4. **Legal evidence generation** — annotated bounding boxes, model confidence,
   officer identity + timestamp + GPS form a complete chain of evidence in
   every PDF report.
5. **Compliance intelligence** — dashboard/analytics for violation trends,
   brand leaderboards, and enforcement priority scoring.

---

## Repository Structure

```
labelguard/
├── backend/               ← FastAPI + ML pipeline
│   ├── app/
│   │   ├── main.py        # FastAPI app factory
│   │   ├── config.py      # Settings (env vars)
│   │   ├── deps.py        # Dependency injection (db, auth)
│   │   ├── routers/       # auth, scans, products, reports, etc.
│   │   ├── services/      # image_processor, ocr, vlm, compliance, etc.
│   │   ├── models/        # Pydantic schemas
│   │   ├── db/            # SQLAlchemy session/base + migrations
│   │   ├── tasks/         # async inference tasks
│   │   └── utils/
│   ├── ml_workers/        # ocr, vlm, layout micro-services
│   ├── tests/
│   └── requirements.txt
├── web/                   ← Next.js 14 frontend
├── mobile/                ← React Native + Expo (optional)
├── ml_models/             ← Model weights + configs
├── docs/                  ← All 7 spec documents
├── scripts/               ← Seed + demo data scripts
├── docker-compose.yml
└── .env.example
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend (Web) | Next.js 14 (App Router), Tailwind, shadcn/ui, Recharts |
| Frontend (Mobile) | React Native + Expo |
| API | FastAPI (Python 3.11+) |
| OCR | PP-OCRv5 (PaddleOCR 3.0) |
| VLM | Qwen2-VL (or Groq `llama-3.2-90b-vision-preview`) |
| Layout | LayoutLMv3 |
| Object Detection | YOLOv8 (label region segmentation) |
| Database | PostgreSQL |
| Cache / Queue | Redis / Bull |
| Object Storage | MinIO (S3-compatible) |
| Reports | ReportLab / python-docx |
| Auth | JWT + OAuth2 (Google SSO), RBAC |
| Deployment | Docker + docker-compose |

---

## Quick Start

The backend defaults to **SQLite** (`sqlite:///./labelguard.db`) for a zero-install demo
with no Docker/Postgres required. Set `DATABASE_URL` to a Postgres URL (and run
`docker compose up -d db redis minio`) for the full production path.

### Option A — SQLite (default, zero-install)

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   Linux/mac: source venv/bin/activate
pip install -r requirements.txt
python ..\scripts\seed.py         # creates tables + seeds rules/users/demo data
uvicorn app.main:app --reload --port 8000
```

> Note: OCR/VLM/LLM services are not installed by default and degrade gracefully
> (fields come up empty, results report MISSING violations). Install the heavy ML
> deps from `backend/requirements.txt` (commented out) or run the `ml_workers`
> via Docker for real extraction + LLM verification.

### Option B — Full stack (Docker: Postgres, Redis, MinIO)

```bash
docker compose up -d db redis minio
```

```bash
cd backend
python -m venv venv
pip install -r requirements.txt
cp ../.env.example .env          # then fill in real values
alembic upgrade head             # run migrations
python ..\scripts\seed.py        # seed demo data
uvicorn app.main:app --reload --port 8000
```

### Demo accounts (from seed)

| Email | Password | Role |
|---|---|---|
| `officer@labelguard.in` | `officer123` | OFFICER |
| `supervisor@labelguard.in` | `super123` | SUPERVISOR |
| `admin@labelguard.in` | `admin123` | ADMIN |

API docs at http://localhost:8000/docs

### 3. Frontend

```bash
cd web
npm install
npm run dev
```

---

## Legal Metrology Compliance Rules Implemented

| Rule ID | Description | Severity |
|---|---|---|
| R6_1_a | Manufacturer / packer / importer name + address | CRITICAL |
| R6_1_b | Common / generic name | MAJOR |
| R6_1_c | Net quantity (standard unit) | CRITICAL |
| R6_1_e | Month + year of manufacture | CRITICAL |
| R6_1_f | MRP inclusive of all taxes | CRITICAL |
| R6_1_g | Consumer care details | MAJOR |
| R6_1_h | FSSAI license (food only) | CRITICAL |
| R6_1_i | Country of origin (imports only) | CRITICAL |
| R6_1_j | Batch / lot number | MAJOR |
| R6_2 | Font size by pack weight | MAJOR |
| R6_5 | MRP on principal display panel | MAJOR |
| R26 | No misleading declarations | MAJOR |

---

## Documentation

Each spec document is in `docs/`:

- `00_BUILD_PROMPT.md` — build plan & phases
- `01_research_papers.md` — 17 research papers justifying tech choices
- `02_problem_and_solution.md` — full problem statement & differentiators
- `03_architecture.md` — system architecture + DB schema
- `04_frontend_spec.md` — frontend pages/components
- `05_backend_spec.md` — API endpoints + service stubs
- `06_legal_rules.md` — machine-checkable compliance rules

---

## SIH 2025 · PS 26034 · Ministry of Consumer Affairs (DoCA)
