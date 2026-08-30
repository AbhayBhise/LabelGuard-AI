# Frontend Specification — LabelGuard AI

---

## Design Language

**Theme:** Government-grade trust + modern SaaS usability  
**Colors:**
- Primary: `#1B4FD8` (government blue)
- Danger/Violation: `#DC2626` (red)
- Compliant: `#16A34A` (green)
- Warning/Partial: `#D97706` (amber)
- Background: `#F8FAFC`
- Surface: `#FFFFFF`
- Text primary: `#0F172A`

**Font:** Inter (body) + JetBrains Mono (codes, extracted values)  
**Framework:** Next.js 14 (App Router) + Tailwind CSS + shadcn/ui

---

## Application Structure

```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── signup/page.tsx
│
├── (dashboard)/
│   ├── layout.tsx              ← Sidebar + topbar shell
│   ├── page.tsx                ← Dashboard home
│   ├── scan/
│   │   ├── page.tsx            ← New scan (upload/camera/URL)
│   │   └── [scanId]/page.tsx   ← Scan result & report
│   ├── products/
│   │   ├── page.tsx            ← Product repository
│   │   └── [productId]/page.tsx← Product detail + history
│   ├── violations/
│   │   └── page.tsx            ← Violations list + filter
│   ├── reports/
│   │   └── page.tsx            ← Report management
│   ├── analytics/
│   │   └── page.tsx            ← Enforcement analytics
│   └── settings/
│       └── page.tsx            ← User/org settings
│
├── api/                        ← Next.js API routes (thin proxy to FastAPI)
└── layout.tsx                  ← Root layout
```

---

## Pages

### Page 1: Login (`/login`)

**Layout:** Centered card, full-screen split (branding left, form right)  
**Components:**
- `GovernmentBrandingPanel` — DoCA + Ministry logo, tagline, decorative
- `LoginForm` — Email + Password + "Login with Google" OAuth
- `RoleBadgePreview` — Shows the 4 roles: Officer, Supervisor, Admin, Viewer

---

### Page 2: Dashboard Home (`/`)

**Layout:** Sidebar + main content  
**Purpose:** At-a-glance compliance enforcement overview

**Components:**

#### `StatsRow` (4 cards)
- Total Scans Today
- Compliant Products
- Non-Compliant Products  
- Pending Reports

#### `ComplianceDonutChart`
- Pie: COMPLIANT / PARTIAL / NON-COMPLIANT breakdown for current period

#### `RecentScansTable`
- Columns: Product | Scanned At | Officer | Location | Status | Action
- Status badge: green/amber/red pill
- Quick action: "View Report" button

#### `ViolationsByRuleBarChart`
- Horizontal bar: which Rule is violated most often (R6_1_f MRP is always #1)

#### `GeographicHeatMap` (India map)
- Districts colored by violation density
- Click → drill down to district-level scans

#### `QuickScanButton`
- Floating CTA: "Start New Scan" → `/scan`

---

### Page 3: New Scan (`/scan`)

**Layout:** Step-by-step wizard (3 steps)  
**Purpose:** The core product action — submit a product for compliance checking

#### Step 1: Input Method Selection
```
┌─────────────────────────────────────────────────────┐
│  How are you scanning?                              │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ 📷 Upload │  │ 🔗 URL   │  │ 📱 Use Camera    │  │
│  │ Image(s)  │  │ E-comm.  │  │ (Mobile only)    │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Upload sub-component:** `ImageDropzone`
- Drag & drop or click
- Multi-image support (front label, back, sides)
- Preview thumbnails with remove option
- Max: 10 images, 10MB each
- Accepted: JPEG, PNG, HEIC, WebP

**URL sub-component:** `EcommerceURLInput`
- Paste Amazon/Flipkart/etc. product URL
- "Fetch Label Images" button
- Preview fetched images with "is this a label?" confidence indicator

#### Step 2: Product Metadata (optional but recommended)
```
Product Name (optional)  │  Net Weight / Volume
Brand                    │  Category (dropdown: Food / Pharma / Cosmetics / Electronics / Other)
Barcode / EAN            │  Import? (Yes/No toggle → enables country of origin check)
```

#### Step 3: Processing & Results
- **Processing State:** Animated progress with step indicators:
  ```
  [✓] Image preprocessing
  [✓] Label region detection  
  [⟳] Text extraction (OCR)
  [ ] Semantic field extraction (AI)
  [ ] Compliance rule checking
  [ ] Report generation
  ```
- **Result State:** → redirects to `/scan/[scanId]`

---

### Page 4: Scan Result (`/scan/[scanId]`)

**The most important page — where the compliance report lives**

**Layout:** Two-column (60% result / 40% annotated image)

#### Left Column:

##### `ComplianceScoreBadge`
```
┌─────────────────────────┐
│  ⚠ NON-COMPLIANT        │
│  Score: 4 / 8 rules     │
│  4 violations found     │
└─────────────────────────┘
```

##### `ViolationAccordion`
Each rule displayed as an expandable card:
```
┌──────────────────────────────────────────────────────┐
│ 🔴 [CRITICAL] Rule 6(1)(f) — MRP Declaration        │
│ ▼                                                    │
│ Finding: MRP present but missing "inclusive of all   │
│ taxes" clause. Found: "MRP ₹125" (incomplete)        │
│ Required: "MRP ₹125 (Inclusive of all taxes)"        │
│                                                      │
│ Evidence: [highlighted region in image →]            │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 🔴 [CRITICAL] Rule 6(1)(a) — Manufacturer Address   │
│ ▼                                                    │
│ Finding: Manufacturer name present, address missing  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 🟡 [MAJOR] Rule 6(2) — Font Size Compliance          │
│ ▼                                                    │
│ Finding: Net quantity text height: 0.7mm             │
│ Required: ≥1.0mm (pack weight 150g)                  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ ✅ [PASS] Rule 6(1)(c) — Net Quantity               │
│ Extracted: "150g" — Format: PASS                     │
└──────────────────────────────────────────────────────┘
```

##### `ExtractedDataTable`
All extracted fields in a clean table:
| Field | Extracted Value | Confidence | Status |
|---|---|---|---|
| Manufacturer Name | XYZ Foods Pvt Ltd | 96% | ✅ |
| Manufacturer Address | *(not found)* | — | 🔴 |
| MRP | ₹125 | 98% | 🟡 Partial |
| Net Quantity | 150g | 94% | ✅ |
| Manufacture Date | 03/2025 | 91% | ✅ |
| Consumer Care | *(not found)* | — | 🔴 |

##### `ReportActions`
- `[📥 Download PDF Report]`
- `[📝 Download DOCX Report]`
- `[📤 Share / Send to Supervisor]`
- `[🔗 Copy Report Link]`

#### Right Column:

##### `AnnotatedImageViewer`
- Label image with color-coded bounding boxes overlay
- Legend: 🟢 Compliant field | 🔴 Violation | 🟡 Partial | ⬜ Not found
- Click any box → highlights corresponding violation in left column
- Zoom + pan support
- Thumbnail strip if multiple images

---

### Page 5: Product Repository (`/products`)

**Purpose:** Browse all previously scanned products, compliance history

**Components:**
- `ProductSearchBar` — search by name, barcode, brand
- `FilterPanel` — Category, Status, Date range, Officer, Region
- `ProductGrid` — Card grid:
  ```
  ┌──────────────────┐
  │ [product image]  │
  │ Lay's Classic    │
  │ PepsiCo India    │
  │ Last scan: Today │
  │ ⚠ NON-COMPLIANT  │
  │ [View History]   │
  └──────────────────┘
  ```
- `ProductDetailModal` → clicking a product shows full scan history timeline

---

### Page 6: Analytics Dashboard (`/analytics`)

**Purpose:** Policy intelligence for supervisors and admins

**Components:**
- `ViolationTrendLineChart` — violations over time (daily/weekly/monthly)
- `TopViolatorsLeaderboard` — brands with most violations
- `RuleViolationHeatmap` — which rules are violated most, by category
- `RegionalComplianceMap` — state-level compliance score choropleth
- `EnforcementEfficiencyMetrics` — scans per officer per day, resolution rate
- `CategoryComplianceRadar` — food vs pharma vs cosmetics vs others

---

### Page 7: Settings (`/settings`)

**Tabs:**
- **Profile** — Name, role, department, contact
- **Organization** — State, district, officers list (admin only)
- **Rules** — Toggle which LM (PC) Rules to enforce (configurable per jurisdiction)
- **Notifications** — Email/push for new violations, daily digest
- **API Keys** — For integration partners (e-commerce platforms)

---

## Component Library

### Shared Components

```typescript
// Core
<ComplianceBadge status="COMPLIANT" | "NON_COMPLIANT" | "PARTIAL" />
<RuleBadge ruleId="R6_1_f" severity="CRITICAL" | "MAJOR" | "MINOR" />
<ConfidenceBar value={0.94} />
<ScanIdTag id="SCAN-2025-08291234" />

// Layout
<DashboardShell>       // Sidebar + topbar + main
<PageHeader title="" subtitle="" actions={[]} />
<SectionCard title="" className="">

// Data Display
<ViolationAccordion violations={[]} />
<ExtractedFieldsTable fields={[]} />
<AnnotatedImageViewer imageUrl="" annotations={[]} />
<ComplianceDonut compliant={n} partial={n} nonCompliant={n} />
<ViolationByRuleChart data={[]} />

// Input
<ImageDropzone onUpload={fn} multiple maxFiles={10} />
<EcommerceURLInput onFetch={fn} />
<ProductMetadataForm onSubmit={fn} />

// Feedback
<ProcessingStepsIndicator steps={[]} currentStep={n} />
<EmptyState icon="" title="" description="" action={} />
<ErrorBoundary fallback={} />
```

---

## Mobile App (React Native + Expo)

**Screens:**
1. **Login** — Biometric + PIN fallback
2. **Home** — Today's scan count, quick-scan button
3. **Camera Scan** — Camera with label-detection overlay (green frame when label detected)
4. **Scan Result** — Simplified compliance result (PASS/FAIL + violation list)
5. **Offline Queue** — Pending syncs when offline
6. **My Reports** — Downloaded PDF reports for reference

**Key Mobile Feature — Smart Camera:**
```
Camera feed → real-time YOLOv8 (TFLite) → label detection overlay
When confidence > 0.85: auto-capture + GPS tag + queue for processing
Offline: queue in local SQLite, sync when online
```

**Offline Capability:**
- On-device: MobileNet + quantized PP-OCR (ONNX) for basic field detection
- Full ML inference happens server-side when online
- All scan results cached locally (SQLite + MMKV storage)
