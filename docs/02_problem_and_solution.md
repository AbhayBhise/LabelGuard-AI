# Problem Statement & Solution — SIH 26034

---

## Problem Statement

**ID:** 26034  
**Title:** Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011  
**Organization:** Ministry of Consumer Affairs, Food & Public Distribution  
**Department:** Department of Consumer Affairs (DoCA)  
**Category:** Software | Theme: Miscellaneous  
**Dataset:** https://consumeraffairs.gov.in/pages/legal-metrology-act

---

## Background

Every packaged commodity sold in India must carry mandatory declarations under:
- **Legal Metrology Act, 2009**
- **Legal Metrology (Packaged Commodities) Rules, 2011**

### Mandatory Declarations Required

| Declaration | Rule Reference |
|---|---|
| Name & address of manufacturer/packer/importer | Rule 6(1)(a) |
| Net quantity (weight/volume/count) | Rule 6(1)(c) |
| MRP (inclusive of all taxes) | Rule 6(1)(f) |
| Month & Year of manufacture/packing/import | Rule 6(1)(e) |
| Consumer care details | Rule 6(1)(k) |
| Country of origin (for imports) | Rule 6(1)(l) |
| FSSAI License number (for food) | Rule 6A |
| Nutritional info (for food items) | FSSAI linked |

### Key Compliance Issues

- Missing declarations
- Incorrect or non-standard font sizes (below 1mm height for small packs, below 2mm for others)
- Improper MRP declaration format
- Missing "inclusive of all taxes" clause
- Misleading net quantity declarations
- Absence of manufacturer address
- No consumer care contact

### Why Manual Inspection Fails

- India has **15M+ registered packaged commodity SKUs** across retail + e-commerce
- Enforcement officers inspect manually — subjective, inconsistent, slow
- E-commerce platforms add another dimension: product listing images often differ from physical labels
- Current process: 1 officer can inspect ~50-100 products/day
- **Our system target: 1 officer can validate 5,000+ products/day**

---

## Our Solution: LabelGuard AI

**"The AI Enforcement Officer for Every Package in India"**

### One-Line Pitch
An intelligent compliance system that scans any packaged commodity image — from retail shelves, e-commerce listings, or physical inspection — and instantly generates a legally defensible compliance report under LM (PC) Rules 2011.

---

## What Makes Us Different From Every Other Team

Most teams will build: Upload image → OCR → Check field presence → Show result.

**We build:**

### Differentiator 1: Multimodal AI Pipeline (Not Just OCR)
We combine **three complementary extraction engines** and cross-validate:
1. **PP-OCRv5** (fast, multilingual, lightweight) — primary OCR
2. **Qwen2-VL / Donut** (vision-language model) — semantic field understanding
3. **LayoutLMv3** fine-tuned — spatial layout compliance (field placement rules)

Cross-validation means if OCR misses something, VLM catches it. This eliminates single-point failure that all OCR-only teams will have.

### Differentiator 2: Font Size Compliance (No One Else Will Do This)
Rules explicitly require minimum font heights (1mm for <200g packs, 2mm for larger). We compute:
- Pixel-per-mm ratio from package context (barcode width as reference)
- Character ascender height from OCR bounding boxes
- **Automated font-size violation flagging** — the most technically complex and legally important check

### Differentiator 3: E-commerce Label Scraping
Beyond image upload, we provide a **URL-based ingestion pipeline** that:
- Scrapes product images from Amazon, Flipkart, Myntra listing pages
- Detects label images among product gallery images
- Runs compliance checks on live e-commerce listings
- **DoCA's biggest compliance gap is e-commerce — we solve it**

### Differentiator 4: Legal Evidence Generation
Every violation report includes:
- Annotated image (bounding box highlighting violation area)
- Pixel-level evidence embedded in PDF
- Legally structured report format matching DoCA's enforcement workflow
- Chain-of-custody audit trail (who scanned, when, GPS coordinates if mobile)

### Differentiator 5: Offline-First Mobile App
Enforcement officers work in markets, not offices. We build a **React Native mobile app** that:
- Works completely offline (on-device MobileNet + lightweight OCR)
- Syncs reports when online
- Takes multi-angle photos and auto-stitches label panorama
- GPS-tags inspections to create heat maps of violation clusters

### Differentiator 6: Compliance Intelligence Dashboard
Not just a scan tool — a **policy intelligence platform**:
- Violation trend analysis by product category / brand / region
- Most non-compliant product categories ranking
- Enforcement priority scoring (which products to inspect next)
- Integration hook for FSSAI and BIS databases

---

## How Our Research Grounds the Solution

| Our Feature | Research Backing |
|---|---|
| PP-OCRv5 multilingual OCR | PaddleOCR 3.0 (arXiv 2507.05595) |
| CRAFT-based text detection | Baek et al. CVPR 2019 |
| Layout-aware field extraction | LayoutLMv3 (arXiv 2204.08387) |
| VLM zero-shot extraction | Qwen2-VL (arXiv 2409.12191) |
| Font size detection | Fateh et al. 2024, compressed domain paper |
| Rule-based compliance engine | NLP Compliance (arXiv 2209.09722) |
| Regulatory rule parsing | CODE-ACCORD (arXiv 2403.02231) |
| Multilingual packaging OCR | HalalBench (arXiv 2604.22754) |
| E-commerce label extraction | CRNN+NLP paper (IJAIA 2024) |

---

## Metrics of Success

| Metric | Target |
|---|---|
| Declaration detection recall | >92% |
| Font size compliance accuracy | >88% |
| False positive rate (claiming violation when none) | <5% |
| End-to-end scan time per product | <8 seconds |
| Products scannable per officer per day | 5,000+ |
| Report generation time | <15 seconds |
| Offline mobile scan success rate | >85% |
