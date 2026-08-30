# Legal Metrology (Packaged Commodities) Rules 2011
## Machine-Checkable Rule Reference

> This document translates every relevant rule into a format the compliance engine can implement.  
> Source: https://consumeraffairs.gov.in/pages/legal-metrology-act

---

## Part 1: Mandatory Declarations (Rule 6)

### Rule 6(1)(a) — Manufacturer / Packer / Importer Identity

**Legal Text:** Every package shall carry a declaration of the name and address of the manufacturer, or where the manufacturer is not the packer, of the packer, and in the case of imported packages, of the importer.

**Machine Check:**
```
REQUIRED: manufacturer_name (non-empty string)
REQUIRED: manufacturer_address (non-empty, must contain city/state/pincode pattern)

CHECK_TYPE: presence + completeness
SEVERITY: CRITICAL

address_completeness_score:
  - contains digits (building/plot number): +1
  - contains comma-separated parts: +1  
  - contains 6-digit pincode: +1
  - contains state name: +1
  MIN_SCORE: 2 out of 4 to pass
```

**Common Violations:**
- Name present but address missing
- Only city mentioned (no pincode/state)
- PO Box only (not acceptable for manufacturer)
- For imports: Indian importer address missing

---

### Rule 6(1)(b) — Common / Generic Name

**Legal Text:** Common or generic name of the commodity.

**Machine Check:**
```
REQUIRED: product_name (non-empty)
CHECK_TYPE: presence
SEVERITY: MAJOR
NOTE: The product name on label should describe the commodity clearly.
```

---

### Rule 6(1)(c) — Net Quantity

**Legal Text:** Net quantity in terms of standard unit of weights and measures. For packages containing an article sold by number, the number of articles.

**Machine Check:**
```
REQUIRED: net_quantity (non-empty)

VALID_FORMATS:
  weight: r'\d+\.?\d*\s*(g|kg|mg|gm|gram|kilogram)'
  volume: r'\d+\.?\d*\s*(ml|l|litre|liter|cc)'
  count:  r'\d+\s*(pcs|pieces|units|tablets|capsules|nos)'
  
CHECK_TYPE: presence + unit_validation + numeric_value
SEVERITY: CRITICAL

ADDITIONAL_CHECKS:
  - Unit must be standard SI unit (g, kg, ml, l, etc.)
  - No ambiguous units (cups, spoonfuls, handfuls — INVALID)
  - Numeric value must be > 0
```

---

### Rule 6(1)(d) — Retail Sale Price

*(Same as MRP — see Rule 6(1)(f))*

---

### Rule 6(1)(e) — Month and Year of Manufacture

**Legal Text:** Month and year in which the commodity is manufactured, or pre-packed, or imported.

**Machine Check:**
```
REQUIRED: manufacture_date (non-empty)

VALID_FORMATS:
  - "MM/YYYY" or "MM-YYYY"
  - "Mon YYYY" (e.g., "Mar 2024")
  - "YYYY-MM" 
  - "Mfg: MM/YYYY"
  
INVALID: Only year without month
INVALID: Only day (dd/mm/yyyy acceptable but unusual)

CHECK_TYPE: presence + format_validation
SEVERITY: CRITICAL

regex: r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\s/\-]?20\d{2}|'
       r'(0[1-9]|1[0-2])[\s/\-]20\d{2}|'
       r'mfg\.?\s*(date\s*)?:?\s*\d{2}/\d{4}'
       (case-insensitive)
```

---

### Rule 6(1)(f) — Maximum Retail Price

**Legal Text:** The retail sale price shall be declared in the form "Maximum Retail Price ₹ ...(inclusive of all taxes)" or "MRP ₹ ...(Incl. of all taxes)".

**Machine Check:**
```
REQUIRED: mrp (non-empty)

VALIDATION_1: Numeric value present
  regex: r'₹?\s*\d+\.?\d*' or r'Rs\.?\s*\d+\.?\d*'

VALIDATION_2: "inclusive of all taxes" clause
  regex: r'incl(usive)?\.?\s*of\s*all\s*tax'  (case-insensitive)
  ALIASES: "incl. all taxes", "incl of all taxes", "inclusive of taxes"
  
FAIL if VALIDATION_1 passes but VALIDATION_2 fails:
  → violation_type: FAIL_CONTENT
  → finding: "MRP present but missing 'inclusive of all taxes' clause"

VALIDATION_3: MRP prefix
  Should have "MRP" or "Maximum Retail Price" or "M.R.P" before value

CHECK_TYPE: presence + content_validation
SEVERITY: CRITICAL
```

---

### Rule 6(1)(g) — Consumer Care Details

**Legal Text:** Consumer care details (name, address, consumer care number, email).

**Machine Check:**
```
REQUIRED: consumer_care (non-empty)

MUST HAVE AT LEAST ONE OF:
  - Phone number: r'[\+91]?\s?[6-9]\d{9}' or r'1800[\s-]?\d{3,}'
  - Email: r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
  - Website: r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

LABEL: Should have "Consumer Care:" or "Helpline:" or "For complaints:" prefix

CHECK_TYPE: presence + contact_info_validation
SEVERITY: MAJOR
```

---

### Rule 6(1)(h) — FSSAI License (Food Products Only)

**Legal Text:** For food articles: FSSAI License/Registration number.

**Machine Check:**
```
APPLIES_TO: category == "food"
REQUIRED: fssai_license (non-empty)

FORMAT: r'FSSAI\s*(Lic\.?\s*No\.?\s*:?\s*)?\d{14}'
  (14-digit license number, may be preceded by "FSSAI Lic. No.")
  
CHECK_TYPE: presence + format_validation (if food)
SEVERITY: CRITICAL (for food products)
NOT_APPLICABLE: for non-food products
```

---

### Rule 6(1)(i) — Country of Origin (Imports Only)

**Legal Text:** In the case of imported packages, the name and address of the importer in India, and country of origin of the commodity.

**Machine Check:**
```
APPLIES_TO: is_imported == True
REQUIRED: country_of_origin (non-empty)

VALID_VALUES: Any recognized country name or ISO 3166-1 alpha-2 code
COMMON: "Made in China", "Product of USA", "Country of Origin: Germany"

regex: r'(made\s*in|country\s*of\s*origin\s*:?|product\s*of)\s+[A-Za-z\s]+'

CHECK_TYPE: presence (if imported)
SEVERITY: CRITICAL (if imported)
NOT_APPLICABLE: if is_imported == False
```

---

### Rule 6(1)(j) — Batch / Lot Number

**Legal Text:** The batch number or lot number.

**Machine Check:**
```
REQUIRED: batch_number (non-empty)

PATTERNS:
  r'(batch|lot|b\.no|b/n|lot\s*no\.?)\s*:?\s*[A-Z0-9\-]+'  (case-insensitive)

CHECK_TYPE: presence
SEVERITY: MAJOR
```

---

## Part 2: Font Size Requirements (Rule 6(2))

### Rule 6(2) — Minimum Font/Lettering Size

**Legal Text:** All declarations required under these rules shall be legible and prominent and shall be printed in distinct contrasting colour.

**Minimum Lettering Height by Package Size:**

| Net Quantity of Package | Minimum Height of Numerals & Letters |
|---|---|
| Up to 200g or 200ml | 1mm |
| More than 200g/ml up to 1kg or 1 litre | 2mm |
| More than 1kg/litre up to 5kg or 5 litres | 4mm |
| Above 5kg or 5 litres | 6mm |

**Machine Check:**
```python
def get_min_font_height_mm(net_quantity_grams: float) -> float:
    if net_quantity_grams <= 200:
        return 1.0
    elif net_quantity_grams <= 1000:
        return 2.0
    elif net_quantity_grams <= 5000:
        return 4.0
    else:
        return 6.0

APPLY TO: All mandatory declaration fields
MEASUREMENT: Via barcode-calibrated px/mm ratio
SEVERITY: MAJOR
```

---

## Part 3: Principal Display Panel (Rule 6(5))

### Rule 6(5) — MRP on Principal Display Panel

**Legal Text:** The MRP shall be declared on the principal display panel of the package.

**Machine Check:**
```
CHECK: MRP bounding box must be in the principal display panel region
HEURISTIC: 
  - Principal display panel = largest face of the package visible to consumer
  - If multiple images, MRP must appear on at least the main/front image
  - MRP should NOT be buried under text or near the bottom/edge in isolation

SEVERITY: MAJOR
IMPLEMENTATION: Detect if MRP is within the top 80% of the label area 
  (bottom-of-pack hidden MRP is a violation)
```

---

## Part 4: Special Product Categories

### Packaged Drinking Water — Additional Requirements
```
REQUIRED: ISI mark (BIS certification)
REQUIRED: Source of water
REQUIRED: Expiry date (within 6 months of manufacture)
regex: r'(best before|use before|expiry)\s*:?\s*\d+\s*(months?|days?|years?)?'
```

### Jewellery / Precious Metals
```
REQUIRED: Purity/fineness marking
REQUIRED: Weight in grams (net)
NOT_REQUIRED: Manufacture date
```

### Electronic Products
```
REQUIRED: Country of origin
REQUIRED: Importer address (if imported)
REQUIRED: BIS/ISI certification where applicable
NOT_REQUIRED: Manufacture month (year sufficient for electronics)
```

---

## Part 5: Prohibited Declarations (Rule 26)

**Machine Check — False/Misleading Claims:**
```
PROHIBITED PATTERNS:
  - "100% natural" or "100% organic" without certification
  - "Best in India" / "No. 1" without basis
  - "Free" claims without clear eligibility criteria
  - Quantity claims that mismatch the actual net quantity

SEVERITY: MAJOR to CRITICAL (case-dependent)
NOTE: These require NLP understanding — use VLM for detection
VLM_PROMPT_ADDITION: "Are there any potentially misleading or unsubstantiated 
  marketing claims on this label? List them."
```

---

## Compliance Score Formula

```python
def compute_compliance_score(violations: List[Violation]) -> float:
    RULE_WEIGHTS = {
        "CRITICAL": 2.0,
        "MAJOR": 1.0,
        "MINOR": 0.5
    }
    
    total_rules = 8  # Core rules always checked
    weighted_violations = sum(
        RULE_WEIGHTS[v.severity] for v in violations
    )
    
    max_weight = total_rules * 2.0  # All critical
    score = max(0, 1 - (weighted_violations / max_weight))
    return round(score, 2)
    
# Score interpretation:
# 1.0 = Fully compliant
# 0.75-0.99 = Minor violations (PARTIAL)
# 0.50-0.74 = Major violations (NON-COMPLIANT)
# <0.50 = Multiple critical violations (SEVERELY NON-COMPLIANT)
```

---

## Rule ID Reference Table

| Rule ID | Description | Severity | Applies To |
|---|---|---|---|
| R6_1_a | Manufacturer name + address | CRITICAL | All |
| R6_1_b | Common/generic name | MAJOR | All |
| R6_1_c | Net quantity with standard unit | CRITICAL | All |
| R6_1_e | Month and year of manufacture | CRITICAL | All |
| R6_1_f | MRP inclusive of all taxes | CRITICAL | All |
| R6_1_g | Consumer care details | MAJOR | All |
| R6_1_h | FSSAI license number | CRITICAL | Food only |
| R6_1_i | Country of origin | CRITICAL | Imports only |
| R6_1_j | Batch/lot number | MAJOR | All |
| R6_2 | Font size (min height by pack weight) | MAJOR | All |
| R6_5 | MRP on principal display panel | MAJOR | All |
| R26 | No misleading declarations | MAJOR | All |
| R6_DW | Additional requirements (drinking water) | CRITICAL | Packaged water |

---

## References

- **Legal Metrology Act, 2009:** https://consumeraffairs.gov.in/pages/legal-metrology-act
- **LM (PC) Rules 2011 Full Text:** https://consumeraffairs.gov.in/sites/default/files/LM_PC_Rules_2011.pdf
- **DoCA Enforcement Guidelines:** https://consumeraffairs.gov.in
- **FSSAI Regulations (for food):** https://www.fssai.gov.in
