# Research Papers — SIH 26034 Legal Metrology Compliance Checker

> Curated list of the most relevant, recent, and powerful research papers supporting this solution. All links are verified live sources.

---

## 1. OCR & Text Extraction from Packaging Labels

### 1.1 Evaluating OCR Performance on Food Packaging Labels (2025)
**Authors:** Nagayi et al. (University of Western Cape)  
**Why it matters:** Direct benchmark of Tesseract, EasyOCR, PaddleOCR, and TrOCR on real-world food packaging images captured with handheld mobile devices — same conditions as our enforcement officers. Found EasyOCR (CRAFT + ResNet) superior for multilingual/stylized text.  
**Link:** https://arxiv.org/html/2510.03570v1

---

### 1.2 PaddleOCR 3.0 Technical Report (2025)
**Authors:** PaddleOCR Team, Baidu  
**Why it matters:** State-of-the-art open-source OCR toolkit. PP-OCRv5 for multilingual text, PP-StructureV3 for document layout parsing, PP-ChatOCRv4 for key information extraction. Achieves billion-parameter VLM accuracy with <100M parameter models — deployable on-device.  
**Link:** https://arxiv.org/abs/2507.05595

---

### 1.3 Information Extraction from Product Labels: A Machine Vision Approach (2024)
**Authors:** Seitaj H., Elangovan V. — IJAIA Vol.15, No.2  
**Why it matters:** Combines CNN+RNN (CRNN) with Tesseract OCR and NLP for label field extraction. Directly addresses our core pipeline: detect → recognize → parse → validate.  
**Link:** https://aircconline.com/ijaia/V15N2/15224ijaia04.pdf

---

### 1.4 AI and OCR-Based Label Verification for Food Traceability (2025)
**Authors:** ResearchGate Publication  
**Why it matters:** Reviews how AI-powered label verification (real-time image scanning + automated data extraction) enables regulatory compliance checks at industrial scale. Directly parallels our use case.  
**Link:** https://www.researchgate.net/publication/391255027_The_Role_of_AI_and_OCR-Based_Label_Verification_Systems_in_Enhancing_Food_Traceability_and_Supply_Chain_Transparency

---

### 1.5 HalalBench: Multilingual OCR Benchmark for Food Packaging (2026)
**Authors:** arXiv 2604.22754  
**Why it matters:** Introduces a 1,043-image COCO-format benchmark for food packaging OCR across 14 languages including Arabic, Japanese, Thai. Benchmarks ML Kit, docTR, EasyOCR, RapidOCR. Directly applicable to India's multilingual label challenge (Hindi + English + regional languages).  
**Link:** https://arxiv.org/abs/2604.22754

---

### 1.6 Automating Nutritional Claim Verification via OCR and ML (2024)
**Authors:** Siddique Ibrahim S P et al. — ICICNIS 2024  
**Why it matters:** Directly automates label claim verification using OCR + ML. Validates label text against regulatory standards — mirrors our rule-based compliance engine.  
**Link:** https://www.researchgate.net/publication/387921937_Automating_Nutritional_Claim_Verification_The_Role_of_OCR_and_Machine_Learning_in_Enhancing_Food_Label_Transparency

---

## 2. Document Understanding & Layout-Aware Models

### 2.1 LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking (2022)
**Authors:** Huang, Yupan et al. — ACM Multimedia 2022  
**Why it matters:** The gold standard for layout-aware document understanding. Jointly encodes text, layout (bounding boxes), and image patches. State-of-the-art on key information extraction benchmarks (FUNSD, CORD). Directly applicable to structured label field extraction.  
**Link:** https://arxiv.org/abs/2204.08387

---

### 2.2 Visual Information Extraction via Classification-Guided Large Vision-Language Models (2026)
**Authors:** Scientific Reports (Nature)  
**Why it matters:** Proposes a zero-shot VLM framework for multi-type document information extraction, decoupling classification from extraction. Enables our system to handle diverse label layouts without per-label-type training.  
**Link:** https://www.nature.com/articles/s41598-026-49319-z

---

### 2.3 Deep Learning based Key Information Extraction from Business Documents: Systematic Review (2024)
**Authors:** arXiv 2408.06345  
**Why it matters:** Comprehensive survey of 100+ papers on key information extraction from visually rich documents — covers LayoutLM family, BROS, FormNet, GenKIE. Essential reading for architecting our extraction pipeline.  
**Link:** https://arxiv.org/abs/2408.06345

---

### 2.4 Donut: OCR-Free Document Understanding Transformer (2022)
**Authors:** Kim et al. — ECCV 2022  
**Why it matters:** End-to-end document parser without OCR stage, achieving superior results on receipt/form parsing tasks. Can directly read label images and output structured JSON — ideal for our MVP's field extraction.  
**Reference:** arXiv:2111.15664 — https://arxiv.org/abs/2111.15664

---

## 3. Automated Regulatory Compliance Checking

### 3.1 NLP-Based Automated Compliance Checking of Data Processing Agreements against GDPR (2023)
**Authors:** Cejas et al. — IEEE Transactions on Software Engineering 49 (2023)  
**Why it matters:** Demonstrates NLP-based automated compliance checking achieving 89.1% precision, 82.4% recall against regulatory "shall" requirements. Our rule engine follows the same pattern: extract LM Rules 2011 "shall" requirements → check extracted label fields against them.  
**Link:** https://arxiv.org/abs/2209.09722

---

### 3.2 CODE-ACCORD: A Corpus of Building Regulatory Data for Rule Generation towards Automated Compliance Checking (2024)
**Authors:** arXiv 2403.02231  
**Why it matters:** Establishes methodology for converting regulatory text into machine-checkable rules using NLP. Directly applicable to converting Legal Metrology (PC) Rules 2011 into our compliance rule engine.  
**Link:** https://arxiv.org/abs/2403.02231

---

### 3.3 AI/NLP's Role in Regulatory Compliance (ACL 2025 Findings)
**Authors:** ACL Anthology 2025.findings-acl.1366  
**Why it matters:** State-of-the-art on NLP-powered regulatory compliance, covering multi-regime compliance checking, GDPR, and structured rule extraction from legal text.  
**Link:** https://aclanthology.org/2025.findings-acl.1366

---

## 4. Scene Text Detection

### 4.1 CRAFT: Character Region Awareness for Text Detection (2019 — widely used 2023-25)
**Authors:** Baek et al. — CVPR 2019  
**Why it matters:** The backbone of EasyOCR's text detector; works exceptionally well on curved, dense, and small text — all common on Indian product packaging. Still the top choice for real-world label scanning.  
**Reference:** https://arxiv.org/abs/1904.01941

---

### 4.2 DeepSolo: Let Transformer Decoder with Explicit Points Solo for Text Spotting (2023)
**Authors:** Ye et al. — CVPR 2023  
**Why it matters:** End-to-end text spotting (simultaneous detection + recognition) outperforming two-stage pipelines. Handles arbitrarily shaped text — important for labels with curves and stylized text.  
**Link:** https://arxiv.org/abs/2211.10772

---

### 4.3 License Plate Detection and Character Recognition Using Deep Learning and Font Evaluation (2024)
**Authors:** Ebrahimi et al. — arXiv 2412.12572  
**Why it matters:** Introduces font evaluation as part of character recognition pipeline (Faster R-CNN + CNN-RNN). Demonstrates 92% recall. Directly relevant to our font-size compliance checking requirement.  
**Link:** https://arxiv.org/abs/2412.12572

---

## 5. Document Layout Analysis & Font Detection

### 5.1 Enhancing OCR: Document Layout Analysis and Text Line Detection (2024)
**Authors:** Fateh et al. — Wiley Engineering Reports  
**Why it matters:** Introduces "optimum font size concepts" in document layout analysis pipeline. Directly applicable to our font-size compliance check against LM Rules (1mm minimum height, etc.).  
**Link:** https://onlinelibrary.wiley.com/doi/full/10.1002/eng2.12832

---

### 5.2 Direct Processing of Document Images in Compressed Domain — Font Size Detection (2014, foundational)
**Authors:** arXiv 1410.2959  
**Why it matters:** Foundational paper on automated font-size detection from document images with 99.67% accuracy. Establishes the line-height + ascender-height feature approach — still the most practical for our use case.  
**Link:** https://arxiv.org/abs/1410.2959

---

## 6. Vision-Language Models for Structured Extraction

### 6.1 Qwen2-VL: Enhancing Vision-Language Model's Perception at Any Resolution (2024)
**Authors:** Wang et al. — Alibaba/Qwen Team  
**Why it matters:** State-of-the-art open-weight VLM with exceptional OCR and document understanding. Can read product label images directly and answer structured extraction queries in zero-shot. The backbone of our AI extraction engine.  
**Link:** https://arxiv.org/abs/2409.12191

---

### 6.2 DocLLM: A Layout-Aware Generative Language Model for Multimodal Document Understanding (2024)
**Authors:** Wang et al. — ACL 2024  
**Why it matters:** Layout-aware LLM that integrates spatial position of text with content — directly applicable to understanding label structure (where MRP is placed, font region, etc.).  
**Link:** https://arxiv.org/abs/2401.00908

---

> **Total: 17 high-quality, directly relevant research papers spanning OCR, document understanding, regulatory compliance NLP, and vision-language models.**
