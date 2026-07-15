# Hallmark Inspection Report Review – Rules Reference v2

> Sources: Hallmark Inspection Manual V2026.04.10 · QIMAone Instructions HMK HK V4 · QIMAone Inspection Type and Workflow Decision Matrix 2025-07-30 · Hallmark Felt Ornament Variation Guide 2020 · QIMA General Instructions – Tests & Specifications checks 2025
> Last compiled: June 2026

---

## How to read this document

Each rule entry contains:
- **ID** — unique rule identifier (section.subsection.rule)
- **Field / Location** — where to look in the report
- **What to check** — the exact verification to perform
- **Scope** — `QUESTION` (check only that field), `SECTION` (cross-check within the same checklist section), `FULL REPORT` (cross-check across multiple sections or documents)
- **Error example** — a concrete example of what a wrong value looks like
- **Correct example** — a concrete example of what the correct value looks like

---

## Section 1 – General Report Setup

### 1.1 Quantity recorded

---

**ID:** 1.1.1
**Field / Location:** Produced quantity / Packed quantity (PO & Product details section)
**What to check:** The quantity recorded must match the Order PO QTY from the "Purchase Order Change" document, not the total order QTY. The IRF filled by the supplier is not a valid source.
**Scope:** `FULL REPORT` — cross-check against the PO document and the IRF
**Error example:** PO states 15,000 EA; IRF states 15,200 EA; report records 15,200 EA → wrong, must use PO qty
**Correct example:** PO states 15,000 EA; report records 15,000 EA

---

**ID:** 1.1.2
**Field / Location:** Produced quantity / Packed quantity unit (PO & Product details section)
**What to check:** The unit (CTN or PCS) must match the unit stated in the IRF. Produced quantity and packed quantity must use the same unit consistently.
**Scope:** `SECTION` — cross-check produced qty unit, packed qty unit, and IRF unit
**Error example:** IRF states unit = CTN; report records produced quantity in PCS
**Correct example:** IRF states unit = CTN; report records produced quantity and packed quantity both in CTN

---

**ID:** 1.1.3
**Field / Location:** Lot size used for sampling (Workmanship section)
**What to check:** For PDQ products, the lot size entered for sampling must be the retail unit quantity (PDQ count × units per PDQ), not the PDQ count itself.
**Scope:** `SECTION` — cross-check lot size against PDQ count and units per PDQ stated in spec
**Error example:** 500 PDQs × 12 units each; report uses lot size = 500
**Correct example:** 500 PDQs × 12 units each; report uses lot size = 6,000

---

### 1.2 SAP Group # consistency

---

**ID:** 1.2.1
**Field / Location:** SAP Group Number field (Document Availability checklist)
**What to check:** The SAP Group # in the report must match the SAP Group # on the purchase order.
**Scope:** `FULL REPORT` — cross-check report SAP Group # against PO document
**Error example:** PO shows HMK9700; report records HMK9725
**Correct example:** PO shows HMK9725; report records HMK9725

---

**ID:** 1.2.2
**Field / Location:** Inspection type / AOQL (report header)
**What to check:** When multiple specifications appear in one report, the inspection type and AOQL must be derived from the spec whose SAP Group # matches the order, not from any other spec present.
**Scope:** `FULL REPORT` — cross-check inspection type against the correct SAP Group # spec
**Error example:** Report contains spec HMK9700 (AOQL 1.5%) and spec HMK9725 (AOQL 3.0%); PO references HMK9725 but report uses AOQL 1.5%
**Correct example:** PO references HMK9725; report correctly uses AOQL 3.0%

---

### 1.3 Inspection reason

---

**ID:** 1.3.1
**Field / Location:** HMK Inspection Reason field (Document Availability checklist)
**What to check:** The value selected must match the reason stated in the supplier's IRF. See valid values below.
**Scope:** `FULL REPORT` — cross-check against the IRF document

| IRF reason field | Expected report value |
|---|---|
| Blank | Non-CQS or Non-SEP supplier |
| CQS audit | CQS – Inspection audit selected lot |
| High attention | CQS/SEP – High attention item |
| New format | CQS/SEP – New format |
| Engineer request | CQS/SEP – Hallmark engineer request (email/specs) |
| Retailer request | CQS/SEP – Retailer/licensor request – Walmart / M&S / Costco / Australia / Walgreens |

**Error example:** IRF reason field is blank; report selects "CQS – Inspection audit selected lot"
**Correct example:** IRF reason field is blank; report selects "Non-CQS or Non-SEP supplier"

---

### 1.4 High Attention (HA) and HCLP

---

**ID:** 1.4.1
**Field / Location:** High Attention Product (HA) field / HCLP field (Document Availability checklist)
**What to check:** If the order ships to USA Kansas City (KC), both HA and HCLP fields must be answered Yes or No per the product specification. If the order does NOT ship to KC, both fields must be N/A.
**Scope:** `FULL REPORT` — cross-check destination (PO & Product details) against HA/HCLP field values
**Error example:** Destination = KC HKBO; HA field = N/A
**Correct example:** Destination = KC HKBO; HA field = No (per spec); HCLP field = No (per spec)

---

**ID:** 1.4.2
**Field / Location:** All photo fields throughout the report
**What to check:** For HCLP products, the report must contain no product photos. Every image field must show a blank image with the remark "HCLP, no photo". This applies to all sections including defect photos.
**Scope:** `FULL REPORT` — scan every photo field in the report
**Error example:** HCLP = Yes; report contains a photo of the retail product in the DAS check section
**Correct example:** HCLP = Yes; all image fields show blank image captioned "HCLP, no photo"

---

**ID:** 1.4.3
**Field / Location:** Inspector's remark / HA-specific checkpoint (Document Availability checklist)
**What to check:** For HA products, the report must include a statement confirming the inspector communicated with the back office / Hallmark PE regarding special requirements.
**Scope:** `QUESTION`
**Error example:** HA = Yes; no mention of PE communication anywhere in the report
**Correct example:** HA = Yes; inspector remark states "Communicated with Hallmark PE [name] re: HA special requirements on [date]"

---

### 1.5 Client / Destination

---

**ID:** 1.5.1
**Field / Location:** Client/Destination field (Document Availability checklist)
**What to check:** For suppliers Lung Cheong (Indonesia), Starlite (Malaysia), PT IGP, and all Hallmark brand orders destined for the USA, destination must be "KC HKBO". For Costco, Walmart, Walgreens, QVC orders, the retailer name must be selected.
**Scope:** `FULL REPORT` — cross-check against PO and production site name
**Error example:** Production site = PT IGP; destination field = "International"
**Correct example:** Production site = PT IGP; destination field = "KC HKBO"

---

### 1.6 Re-inspection reports

---

**ID:** 1.6.1
**Field / Location:** Report header / Inspector's remark
**What to check:** For re-inspection reports, the reason for re-inspection must appear at the head of the report.
**Scope:** `QUESTION`
**Error example:** Report is a re-inspection after a previous FAIL; no re-inspection reason stated at the top
**Correct example:** Report header states "Re-inspection – previous report [ref] failed on workmanship [date]"

---

## Section 2 – Documents Recorded in the Report

### 2.1 SR (Safety & Regulatory) report

---

**ID:** 2.1.1
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** SR checkpoint result must be "Passed". If not passed, the overall report result must be FAIL.
**Scope:** `FULL REPORT` — if SR = not passed, verify overall result is FAIL
**Error example:** SR checkpoint = Failed; overall result = Pass
**Correct example:** SR checkpoint = Failed; overall result = Fail

---

**ID:** 2.1.2
**Field / Location:** SR Test Report Check — report date / validity (Document Availability checklist)
**What to check:** SR report validity: standard products = 1 year; Toys & Children products = 4 weeks; Food-contact products (group HMK9700) = per PO. Check the SR report issue date against the inspection date.
**Scope:** `SECTION` — cross-check SR issue date, product category, and SAP group
**Error example:** Product = toy; SR report dated 6 months ago → expired (must be ≤4 weeks)
**Correct example:** Product = standard gift; SR report dated 8 months ago → valid (within 1 year)

---

**ID:** 2.1.3
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** If the SR report covers product format level (not SKU level), verify the format matches the inspected product and the report is within validity. This must be noted in the report remarks.
**Scope:** `QUESTION`
**Error example:** SR report is format-level; no remark confirming format match in the report
**Correct example:** SR report is format-level; remark states "SR report covers format XYZ, confirmed match with inspected SKU"

---

**ID:** 2.1.4
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** If SR report result shows a failure but the factory provides a Hallmark override email, the checkpoint is acceptable. The override email must be uploaded in the report.
**Scope:** `QUESTION`
**Error example:** SR fails; factory mentions an override email but it is not uploaded in the report
**Correct example:** SR fails; override email from Hallmark uploaded as attachment in the report

---

**ID:** 2.1.5
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** If the SRR shows 3 "No" for the 3 applicable tests, SR report is not required. The checkpoint must NOT be failed in this case; the report must document this.
**Scope:** `QUESTION`
**Error example:** SRR shows 3 "No"; SR checkpoint is marked Failed because no SR report was provided
**Correct example:** SRR shows 3 "No"; SR checkpoint is marked N/A or Pass with remark "SRR 3x No, SR not required"

---

**ID:** 2.1.6
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** For re-run orders reusing an SR from a different PO, the report must confirm the supplier provided a material-change confirmation to the 3rd party lab. Exception: Toys, Children products, Food-contact = always need new SR per PO.
**Scope:** `FULL REPORT` — cross-check PO reference on SR report vs. current PO
**Error example:** Re-run order; SR report references a different PO; no material-change confirmation mentioned
**Correct example:** Re-run order; remark states "Supplier provided material-change confirmation to Intertek on [date]"

---

**ID:** 2.1.7
**Field / Location:** SR Test Report Check (Document Availability checklist)
**What to check:** If SR report is missing, the report must flag it and note that Andrew Chan (andrew.chan@hallmark.com) was notified.
**Scope:** `QUESTION`
**Error example:** SR report missing; checkpoint simply marked Failed with no further remark
**Correct example:** SR report missing; remark states "SR report not provided. Andrew Chan notified by email on [date]"

---

### 2.2 FR (Functional & Reliability) report

---

**ID:** 2.2.1
**Field / Location:** FR Test Report Check (Document Availability checklist)
**What to check:** FR checkpoint must show "Passed". If not passed, overall result must be FAIL.
**Scope:** `FULL REPORT` — if FR = not passed, verify overall result is FAIL
**Error example:** FR checkpoint = Failed; overall result = Pass
**Correct example:** FR checkpoint = Failed; overall result = Fail

---

**ID:** 2.2.2
**Field / Location:** FR Test Report Check — report date / validity (Document Availability checklist)
**What to check:** FR validity: Non-HA items = 1 year; HA items = 1 year but must be tested per PO. If FR is missing, the FR checkpoint must be failed.
**Scope:** `SECTION` — cross-check FR issue date, HA status, and current PO reference
**Error example:** HA = Yes; FR report is 8 months old and references a prior PO → invalid for HA, must be per PO
**Correct example:** HA = Yes; FR report references the current PO and is dated within the same production lot

---

### 2.3 Ship test report

---

**ID:** 2.3.1
**Field / Location:** Documents and Sample Availability checkpoint (Document Availability checklist)
**What to check:** Ship test report must be on file and referenced. It is valid indefinitely unless there are changes in: supplier, production process, product or packaging material, packed quantity, or packing method. From 2024 onwards it is included as an appendix in the FR report. If missing, the Documents checkpoint must be failed.
**Scope:** `SECTION` — cross-check ship test reference against FR report (2024+)
**Error example:** Ship test not referenced; no mention in FR report appendix; Documents checkpoint = Pass
**Correct example:** FR report appendix includes ship test; Documents checkpoint = Pass with remark "Ship test included in FR report appendix"

---

### 2.4 DAS / VAS / Limit sample

---

**ID:** 2.4.1
**Field / Location:** VAS/DAS Check section
**What to check:** The report must document a side-by-side comparison of production sample against the DAS. This section cannot be left blank or skipped. VAS is used for Keepsake (KPS) only. If a limit sample is in use, it must be referenced.
**Scope:** `QUESTION`
**Error example:** VAS/DAS Check section left blank; result = N/A without justification
**Correct example:** VAS/DAS Check completed; remark states "Production sample compared to DAS — color, construction, and labeling conform"

---

### 2.5 Commit sheet (Hallmark Ornaments only)

---

**ID:** 2.5.1
**Field / Location:** VAS/DAS Check / Retail packaging sections (for HO orders)
**What to check:** For HO orders, the report must confirm cross-check of: colorway SKU, colorway UPC vs. production package, package type and retail price, product image vs. spec, unit price consistency across DAS/specs/commit sheet/retail package, and copyright consistency.
**Scope:** `SECTION` — applicable only when BU = HO (Hallmark Ornaments)
**Error example:** BU = HO; no mention of commit sheet cross-check anywhere in the report
**Correct example:** BU = HO; remark states "Commit sheet cross-checked: colorway SKU, UPC, retail price, copyright — all conform"

---

### 2.6 PP report

---

**ID:** 2.6.1
**Field / Location:** Documents and Sample Availability / Workmanship section
**What to check:** For HA and HCLP products, the PP report must be referenced. Defects noted in the PP report must be specifically addressed during the workmanship check. Packaging details must be compared against the PP report.
**Scope:** `SECTION` — cross-check PP report reference against workmanship remarks
**Error example:** HA = Yes; PP report not referenced; workmanship remarks make no mention of PP defects
**Correct example:** PP report referenced; workmanship remark states "PP defects: [list] — confirmed resolved in current lot"

---

### 2.7 Packing list

---

**ID:** 2.7.1
**Field / Location:** Workmanship / Retail packaging section
**What to check:** When a carton contains mixed SKUs, the packing list must be used to verify the assortment and carton range. Any discrepancy must be clearly remarked.
**Scope:** `SECTION` — applicable only when mixed-SKU cartons are present
**Error example:** Carton contains 3 SKUs; no packing list referenced; no assortment verification remark
**Correct example:** Packing list referenced; remark states "Mixed SKU carton verified against packing list — assortment and qty conform"

---

### 2.8 Visual Standard – PT. Camino factory (KPS only)

---

**ID:** 2.8.1
**Field / Location:** Inspector's remark / VAS/DAS Check section
**What to check:** For inspections at PT. Camino Industrial (Indonesia) on KPS items, the report must state that the PT. Camino Visual Standard was applied in addition to general Hallmark visual requirements.
**Scope:** `QUESTION` — applicable only when production site = PT. Camino Industrial
**Error example:** Site = PT. Camino Industrial; BU = KPS; no mention of PT. Camino Visual Standard
**Correct example:** Remark states "PT. Camino Visual Standard applied alongside Hallmark general visual requirements"

---

## Section 3 – Inspection Type & Sample Size

### 3.1 Correct inspection type per product / channel

---

**ID:** 3.1.1
**Field / Location:** Inspection type / AOQL (report header)
**What to check:** The inspection type must match the product category and destination channel per the decision matrix below.

| Product category | Destination | Expected inspection type |
|---|---|---|
| 3D – HMK Ornaments, Gifts (excl. Plush) | KC, UK, HCA, AU, NL, Nihon | AOQL 3.0% Single Sampling |
| 3D – HMK Ornaments, Gifts (excl. Plush) | Dayspring, Mary & Martha | AOQL 3.0% Single Sampling (min. sample 85) |
| 3D – HMK Ornaments, Gifts (excl. Plush) | Walmart FOB | AQL 1.5 / 4.0 Level I |
| 3D – Gifts Plush | KC, UK, HCA, AU, NL, Dayspring, M&M | AOQL 1.5% & 4.0% Single Sampling |
| 3D – Keepsake (KPS) | KC, UK, HCA, AU, NL, Nihon | AOQL 1.5% Single Sampling |
| 3D – Keepsake (KPS) | Walmart FOB | AQL 1.5 / 4.0 Level I |
| 3D – Hengfeng Ceramic | All | AOQL Single Sampling +2 levels vs. standard table |
| 3D – Crayola | KC, UK, NL, AU, Nihon, Mexico, France | AQL 1.5 / 4.0 Level II |
| 3D – Fixtures & Dealer Service | KC, UK, HCA, AU, NL, Nihon | AOQL 2.5% Single Sampling; fixed sample = 15 |
| 2D – HA items | All | Single Sampling Plan |
| 2D – Non-HA, individually packed | Standard HMK | Double Sampling Plan |
| 2D – Non-HA, mixed-packed | Standard HMK | Single Sampling Plan |
| 2D – Dayspring | All | QIMA/HMK: Double Sampling; other: Single Sampling |
| 2D – Dayspring 3D items | All | Single Sampling (min. sample = 85) |
| PDQ products | All | Single Sampling; lot size = retail units |

**Scope:** `FULL REPORT` — cross-check product category (name/description), destination (PO), and inspection type in header
**Error example:** Product = 3D Keepsake; destination = KC HKBO; inspection type = AOQL 3.0% Single Sampling → wrong, must be AOQL 1.5%
**Correct example:** Product = 3D Keepsake; destination = KC HKBO; inspection type = AOQL 1.5% Single Sampling

> Note: "Keepsake Ornament" (KPSK) must use "Keepsake (KPS)" inspection type, not Ornaments/Gifts.

---

### 3.2 Correct sample size per lot

---

**ID:** 3.2.1
**Field / Location:** Sample size field (Workmanship section)
**What to check:** The sample size must match the correct sampling table for the chosen inspection type and lot size. Use the tables below. Lot size must not exceed 50,000 units per lot unless specs specify otherwise.

**AOQL 3.0% single sampling:**

| Lot size | Sample | Accept ≤ |
|---|---|---|
| 0–800 | 30 | 1 |
| 801–3,000 | 65 | 3 |
| 3,001–5,000 | 85 | 4 |
| 5,001–10,000 | 105 | 5 |
| 10,001–20,000 | 125 | 6 |
| 20,001–50,000 | 170 | 8 |
| 50,001+ | 215 | 10 |

**AOQL 1.5% single sampling (Keepsakes):**

| Lot size | Sample | Accept ≤ |
|---|---|---|
| 0–2,000 | 55 | 1 |
| 2,001–7,000 | 90 | 2 |
| 7,001–10,000 | 130 | 3 |
| 10,001–20,000 | 170 | 4 |
| 20,001–50,000 | 295 | 7 |
| 50,001+ | 340 | 8 |

**Plush AOQL 1.5% Maj / 4.0% Min:**

| Lot size | Sample | Major ≤ | Minor ≤ |
|---|---|---|---|
| 0–1,000 | 35 | 0 | 2 |
| 1,001–4,000 | 65 | 1 | 4 |
| 4,001–10,000 | 85 | 2 | 5 |
| 10,001–20,000 | 135 | 3 | 8 |
| 20,001–50,000 | 165 | 4 | 10 |
| 50,001+ | 210 | 5 | 12 |

**AOQL 2.5% (Fixtures & Dealer Service):** fixed sample = 15; accept = 0.

**Double sampling – 3.0% AOQL:** 1st n=30, accept 0, reject ≥5. If 1–4: 2nd n=60, combined accept ≤4 of 90, reject ≥5.
**Double sampling – 1.5% AOQL:** 1st n=60, accept 0, reject ≥6. If 1–5: 2nd n=160, combined accept ≤5 of 220, reject ≥6.
**Double sampling – 1.0% AOQL:** 1st n=90, accept 0, reject ≥6. If 1–5: 2nd n=230, combined accept ≤5 of 320, reject ≥6.

**Scope:** `SECTION` — cross-check lot size, inspection type, and sample size field
**Error example:** Lot = 8,000 pcs; AOQL 3.0% single sampling; sample size = 65 → wrong, must be 105
**Correct example:** Lot = 8,000 pcs; AOQL 3.0% single sampling; sample size = 105; accept ≤ 5

---

**ID:** 3.2.2
**Field / Location:** 2nd sample section (Workmanship section)
**What to check:** A 2nd sample is only valid if the 1st sample defect count fell between the accept and reject numbers (neither accepted nor rejected in round 1). If a 2nd sample appears but the 1st sample result was already accept or reject, it is invalid.
**Scope:** `SECTION` — cross-check 1st sample defect count against accept/reject thresholds before accepting 2nd sample result
**Error example:** Double sampling AOQL 3.0%; 1st sample: 0 defects (→ accepted); report shows a 2nd sample was taken anyway
**Correct example:** Double sampling AOQL 3.0%; 1st sample: 2 defects (between 0 and 5); 2nd sample correctly triggered

---

### 3.3 Acceptance number field

---

**ID:** 3.3.1
**Field / Location:** Acceptance point / C# field (Workmanship section)
**What to check:** The acceptance number field must contain the threshold from the sampling table, NOT the actual count of defects found.
**Scope:** `QUESTION`
**Error example:** Inspector found 0 defects; records C# = 0 (actual count) instead of the table threshold (e.g., 5)
**Correct example:** Lot = 8,000; AOQL 3.0%; C# = 5 (from table), defects found = 0 recorded separately

---

### 3.4 Sampling unit

---

**ID:** 3.4.1
**Field / Location:** Sampling unit / Inspector's remark (Workmanship section)
**What to check:** The sampling unit must always be the retail unit (Market Sale Unit), not the wholesale or shipper unit.
**Scope:** `QUESTION`
**Error example:** Product packed 12 retails per wholesale; inspector sampled 30 wholesale packs instead of 30 retail units
**Correct example:** Inspector sampled 30 individual retail units

---

## Section 4 – Defect Classification & Workmanship

### 4.1 Critical defects

---

**ID:** 4.1.1
**Field / Location:** Critical defects count / Overall result (Workmanship section)
**What to check:** Acceptance number for critical defects is always 0. If any critical defect is found, overall result must be FAIL and escalation to PE must be noted.
**Scope:** `FULL REPORT` — if critical defect count > 0, verify overall result = FAIL and PE escalation noted
**Error example:** Critical defects = 1; overall result = Pass
**Correct example:** Critical defects = 1; overall result = Fail; remark states "Escalated to PE [name] on [date]"

Critical defects (non-exhaustive): animal fur, human hair or body fluid, insects or insect debris, mold on packaging or product, sharp tools inside the product (cutter, needle, scissors).

---

**ID:** 4.1.2
**Field / Location:** Sharp point / sharp edge checkpoint (Workmanship or checklist section)
**What to check:** Sharp point/edge check must be recorded for ALL Hallmark products. All products are considered free of shape hazard by default. If a sharp point or edge is found, it must be reported and escalated to PE — it is not automatically classified as Critical, but PE must evaluate.
**Scope:** `QUESTION`
**Error example:** Sharp edge found on product; report classifies it as Critical defect without PE evaluation note
**Correct example:** Sharp edge found; remark states "Escalated to PE for evaluation — not pre-classified as critical"

---

### 4.2 Functional defects

---

**ID:** 4.2.1
**Field / Location:** Functional defect count / Function Test result (Workmanship + Tests section)
**What to check:** Functional defect count must be recorded separately. Accept if ≤ C#/2. If > C#/2, Function Test must be failed and count remarked. Escalate to PE.
**Scope:** `SECTION` — cross-check functional defect count against C# and Function Test result
**Error example:** C# = 5; functional defects = 4 (> C#/2 = 2.5); Function Test = Pass → wrong, must be Fail
**Correct example:** C# = 5; functional defects = 1 (≤ 2.5); Function Test = Pass

---

### 4.3 Major defects

---

**ID:** 4.3.1
**Field / Location:** Minor defects field / Major defects field (Workmanship section)
**What to check:** For AOQL inspections (all except plush), Minor defects must be reclassified as Major. There is no Minor defect tolerance for AOQL. Exception: Plush items use AOQL 1.5% Major / 4.0% Minor.
**Scope:** `SECTION` — applicable when inspection type = AOQL and product is not plush
**Error example:** AOQL 3.0% inspection; 2 Minor defects recorded in Minor field; not reclassified as Major
**Correct example:** AOQL 3.0% inspection; Minor defects reclassified and counted in Major field

---

**ID:** 4.3.2
**Field / Location:** Defect photos (Photos section)
**What to check:** Every Major defect must have 2 photos: 1 global view and 1 close-up.
**Scope:** `SECTION` — cross-check number of Major defects against number of defect photo pairs
**Error example:** 2 Major defects found; only 1 photo total in the report
**Correct example:** 2 Major defects; 4 photos: 2 global views + 2 close-ups, each with a caption

---

**ID:** 4.3.3
**Field / Location:** Defect description / defect photos (Workmanship section)
**What to check:** For defects longer than 1 cm, the defect description must include a measurement (length/area) and the photo must show a ruler.
**Scope:** `SECTION` — check each Major defect description and its photo
**Error example:** Scratch defect = 3 cm; no measurement in description; ruler not visible in photo
**Correct example:** Description: "Scratch, 3.2 cm length"; photo shows defect with ruler alongside

---

**ID:** 4.3.4
**Field / Location:** Workmanship summary / defect list
**What to check:** If no defect is found, the report must explicitly record "no defect found".
**Scope:** `QUESTION`
**Error example:** 0 defects found; defect section left blank
**Correct example:** 0 defects found; remark states "No defect found"

---

### 4.4 Special defect rules

---

**ID:** 4.4.1
**Field / Location:** Defect count (Workmanship section)
**What to check:** For box cards or set products, only 1 defect is counted per box or set, regardless of how many individual items inside are affected.
**Scope:** `QUESTION` — applicable when product = box card or set
**Error example:** Box of 6 cards; 3 cards have a minor print mark; inspector records 3 defects
**Correct example:** Box of 6 cards; 3 cards affected; inspector records 1 defect (1 box = 1 unit)

---

**ID:** 4.4.2
**Field / Location:** Defect list (Workmanship section)
**What to check:** Minor print defects under 5 mm must not be reported unless they affect sellability. If they affect sellability, they must be classified as Major.
**Scope:** `QUESTION`
**Error example:** 2 mm print smudge on inner page; recorded as Minor defect → should not be recorded at all
**Correct example:** 2 mm print smudge on inner page; not recorded (below 5 mm, no impact on sellability)

---

**ID:** 4.4.3
**Field / Location:** Defect list (Workmanship section)
**What to check:** Dirt marks on kraft recycled paper material (without glue residue penetrating onto the bag surface) are acceptable and must not be recorded as defects.
**Scope:** `QUESTION` — applicable when product uses kraft recycled paper
**Error example:** Kraft paper bag; surface dirt marks (no glue residue); recorded as Minor defects
**Correct example:** Kraft paper bag; surface dirt marks noted but not recorded as defects per acceptance rule

---

### 4.5 Felt ornament / hand-crafted item variation

---

**ID:** 4.5.1
**Field / Location:** Workmanship remarks / DAS comparison section
**What to check:** For felt ornaments and hand-crafted items, the following variations are acceptable and must NOT be recorded as defects: shape/width/thickness variation (if item remains recognizable), facial feature variation (if symmetrical and proportionate), design feature placement variation (if overall appearance is consistent), variation between units within a wholesale.
**Scope:** `QUESTION` — applicable when product type = felt ornament or hand-crafted item
**Error example:** Felt ornament; slight asymmetry in embroidered eye; recorded as Major defect
**Correct example:** Felt ornament; slight asymmetry noted; not recorded as defect — within acceptable variation for hand-crafted items

---

### 4.6 Visual inspection – batch check method

---

**ID:** 4.6.1
**Field / Location:** Workmanship / DAS check section
**What to check:** For card items, boxed cards, and handle bags using the batch check method, at least 1 production sample must be fully compared against the DAS. Remaining samples are checked via batch method. The report must show this was done.
**Scope:** `SECTION`
**Error example:** Handle bag; batch check used; no mention of any individual sample fully compared against DAS
**Correct example:** Remark states "1 unit fully compared against DAS; remaining 29 units checked by batch method"

---

## Section 5 – Measurements & Color

### 5.1 Measurements

---

**ID:** 5.1.1
**Field / Location:** Measurement section / product dimension checkpoint
**What to check:** Measurement data must be recorded for at least 1 retail sample. No AQL applies. If a noticeable difference exists, a failure remark and a measurement photo are required.
**Scope:** `QUESTION`
**Error example:** Measurement section left blank; no dimension data recorded
**Correct example:** "Product dimension: L 14.8 cm × W 9.4 cm × H 4.7 cm (spec: L 15 cm × W 9.5 cm × H 4.8 cm) — within tolerance"

---

**ID:** 5.1.2
**Field / Location:** Measurement remarks (paper bag products)
**What to check:** For paper bags, handle length must be measured and remarked.
**Scope:** `QUESTION` — applicable when product = paper bag
**Error example:** Paper bag inspected; handle length not mentioned in measurements
**Correct example:** "Handle length: 28 cm (spec: 28 cm) — conforms"

---

**ID:** 5.1.3
**Field / Location:** Measurement remarks (products with components)
**What to check:** For products with components, component weight must be recorded in addition to product dimensions.
**Scope:** `QUESTION` — applicable when product has components
**Error example:** Product has a detachable ribbon component; only overall product weight recorded
**Correct example:** "Product weight: 85 g; ribbon component weight: 12 g"

---

### 5.2 Color accuracy

---

**ID:** 5.2.1
**Field / Location:** VAS/DAS Check — color checkpoint
**What to check:** CMYK color result (PressSIGN report) must be ≥90%. If below 90%, the report must include a remark. If neither PressSIGN nor Delta E is available, the check relies on visual comparison and any doubt must be recorded as a failure.
**Scope:** `QUESTION`
**Error example:** PressSIGN result = 84%; no remark in report; checkpoint = Pass
**Correct example:** PressSIGN result = 84%; remark added; checkpoint = Fail with client notification

---

**ID:** 5.2.2
**Field / Location:** VAS/DAS Check — color checkpoint (solid colors)
**What to check:** For PMS / solid colors, Delta E (Delta E 2000) must be ≤2. If >2, the report must flag it and include photos of the color target Lab value and the Delta E reading.
**Scope:** `QUESTION`
**Error example:** Delta E = 2.8; no flag in report; no photos of Lab value or Delta E reading
**Correct example:** Delta E = 2.8; checkpoint flagged as Fail; photos of Lab value and Delta E reading included

---

## Section 6 – Packaging Checks

### 6.1 Packaging inspection sample size

---

**ID:** 6.1.1
**Field / Location:** Packaging checklist (2D & 3D Packaging section)
**What to check:** Packaging check must cover 18 units (shippers / wholesale / retail). If 1–2 defects are found, a 2nd sample of 100 units is required (118 total). The report must reflect which stage was reached.
**Scope:** `QUESTION`
**Error example:** 1 packaging defect found at 18 units; no 2nd sample conducted; checkpoint = Pass
**Correct example:** 1 defect at 18 units; 2nd sample of 100 conducted; combined result recorded

---

### 6.2 Shipper dimensions and weight

---

**ID:** 6.2.1
**Field / Location:** Shipper Dimensions & Weight & Marks checkpoint
**What to check:** Actual shipper dimensions and weight must be within the applicable limits. If exceeded, the shipper check must be failed.

| Channel | Max dimensions (O.D.) | Max weight |
|---|---|---|
| Standard HMK | L22"×W21"×D32" (min L12"×W8"×D5") | 50 lbs (min 5 lbs) |
| Walgreens FOB | L48"×W40"×H46" | 50 lbs (no minimum) |
| Dayspring | 24"H×24"W×14.5"L | 30 lbs |
| HCA (Australia) | Standard dimensions | 12 kg (15 kg for tag-on) |

**Scope:** `QUESTION`
**Error example:** Standard HMK order; carton measured 60×55×90 cm → exceeds max; checkpoint = Pass
**Correct example:** Standard HMK order; carton measured 50×45×70 cm → within limits; checkpoint = Pass

---

### 6.3 Shipper shipmark content

---

**ID:** 6.3.1
**Field / Location:** Shipper Dimensions & Weight & Marks checkpoint / shipmark photos
**What to check:** Shipmark color must be BLACK. Both end panels must include: NET WEIGHT (kg), GROSS WEIGHT (kg), DIMENSIONS (cm), CARTON NUM, HALLMARK MARKETING COMPANY LLC, REUSE #, MADE IN. Font approx. 13 mm bold. Hallmark crown logo on side panel 1; shipping address on side panel 2.
**Scope:** `QUESTION`
**Error example:** End panel missing REUSE # field; checkpoint = Pass
**Correct example:** Both end panels show all required fields; shipmark is black; checkpoint = Pass

---

**ID:** 6.3.2
**Field / Location:** REUSE # value on shipper end panel
**What to check:** REUSE # = 4-digit inner volume in cubic inches. Must fall within the range [(L−0.5)×(W−0.5)×(D−0.5)] to [(L+0.5)×(W+0.5)×(D+0.5)] using inner dimensions in inches.
**Scope:** `QUESTION`
**Error example:** Inner dims = 20"×16"×12" → range = 2907–3393; REUSE # = 2500 → out of range
**Correct example:** Inner dims = 20"×16"×12" → REUSE # = 3072 → within range

---

### 6.4 Corner label content and position

---

**ID:** 6.4.1
**Field / Location:** Carton Labels & UPC Check checkpoint
**What to check:** Corner label required for all finished-product shipments to Hallmark US and Canada warehouses. Not required for: sales samples, component orders, international orders (excluding Canada). Label must be on the right bottom corner of the crown-logo side panel, 1"–3" from the bottom, wrapping around two adjacent panels, within ±15° of parallel with carton bottom.
**Scope:** `QUESTION`
**Error example:** Hallmark US order; corner label placed on top panel of carton
**Correct example:** Corner label on right bottom corner of crown-logo side panel, 2" from bottom, correctly wrapping

---

**ID:** 6.4.2
**Field / Location:** Carton Labels & UPC Check — label content
**What to check:** Mandatory label content: SAP Material Number (top), Material Number/SKU (11-char, no international suffix), material description (exact match to PO/spec), Wholesale QTY (wholesale boxes in shipper, max 4 digits, NOT retail count), Partial quantity (blank or 0), Destination, Date code (MMYY, must not post-date shipping month), Vendor ID (GS preferred), Made In (2-letter ISO), Canada Price (if applicable).
**Scope:** `SECTION` — cross-check each label field against PO and spec
**Error example:** Wholesale QTY field shows retail count (e.g., 120) instead of wholesale box count (e.g., 10)
**Correct example:** Wholesale QTY = 10 (10 wholesale boxes in shipper); retail count not shown on corner label

---

**ID:** 6.4.3
**Field / Location:** Carton Labels & UPC Check — 4-3-4 format
**What to check:** SKU barcode scanning result must follow the 4-3-4 structure. Leading zeros to reach 4 digits in first and last parts; spaces after letter(s) to make middle part total 3 characters.
**Scope:** `QUESTION`
**Error example:** SKU = 99TM2024; report shows scan result = "99TM2024" (no 4-3-4 formatting)
**Correct example:** SKU = 99TM2024 → scan result = "0099TM 2024"

---

**ID:** 6.4.4
**Field / Location:** Carton Labels & UPC Check — label corrections
**What to check:** If corner label has incorrect non-barcode information (destination, date code, vendor ID, COO), an overlay label is acceptable. Barcode data errors require a full reprint; manual amendments to barcodes are not allowed.
**Scope:** `QUESTION`
**Error example:** Barcode on corner label encodes wrong SKU; factory applies handwritten correction → not acceptable
**Correct example:** Barcode encodes wrong SKU; label reprinted; new label applied

---

### 6.5 Extra barcode on retail box

---

**ID:** 6.5.1
**Field / Location:** Carton Labels & UPC Check / Retail Labeling section
**What to check:** If an extra barcode (price info barcode) is present on the retail box, it must be scanned and recorded. Readable metadata → Pass; unreadable → Fail.
**Scope:** `QUESTION` — applicable only when extra barcode is present on retail box
**Error example:** Extra price barcode visible on retail box; not scanned; not mentioned in report
**Correct example:** Extra barcode scanned; remark states "Price barcode readable — Pass"

---

### 6.6 Partially filled carton (PFC)

---

**ID:** 6.6.1
**Field / Location:** Partially Filled Carton checkpoint
**What to check:** Only 1 PFC per PO per shipment; must be the last carton number. PFC must have: 2 orange "PARTIALLY FILLED CARTON" labels on opposite corners, and a printed corner label showing the actual wholesale quantity (no manual amendments accepted). Actual packed quantity must match the corner label.
**Scope:** `QUESTION` — applicable only when a PFC exists
**Error example:** PFC has only 1 orange label; corner label shows handwritten qty correction
**Correct example:** PFC is last carton; 2 orange labels on opposite corners; printed corner label matches actual qty

---

### 6.7 Wholesale label content

---

**ID:** 6.7.1
**Field / Location:** Wholesale Packaging checkpoint
**What to check:** Required fields: USA SKU | Canada SKU | product description | retails per wholesale | production date (MMYY) | Made In | Vendor ID. Canada-only orders show only Canada SKU. Label must not be on the sealing area. For products going through Hallmark DC, updated wholesale labeling guidelines apply.
**Scope:** `QUESTION`
**Error example:** Label missing production date; label placed over sealing area
**Correct example:** All required fields present; label on side panel, away from seal

---

**ID:** 6.7.2
**Field / Location:** Wholesale Packaging checkpoint (film/polybag wholesale)
**What to check:** Wholesale label not required for film/polybag wholesale only if ALL 4 conditions are met: (1) stock number on retail ≥3 mm tall, (2) stock number visible through film, (3) retail count countable through film, (4) retail UPC visible and scannable through film.
**Scope:** `QUESTION` — applicable when wholesale pack = film or polybag
**Error example:** Film wholesale; no label; stock number on retail = 2 mm tall (below 3 mm) → label required but missing
**Correct example:** Film wholesale; no label; all 4 conditions verified and noted in remark

---

### 6.8 Hallmark Australia – wholesale packaging

---

**ID:** 6.8.1
**Field / Location:** Wholesale Packaging checkpoint (HCA orders)
**What to check:** Each wholesale unit must be in a sealed LDPE ≥30% recycled bag (min. 40 micron / 1.5 mil) with visible stock number and scannable barcode. White wholesale label min. 3.25"×1.125" (83×29 mm), black on white, on end or side panel. 1FB inner carton: 420×170×205 mm ±0/−2 mm. Each shipper must contain only 1 stock number. Gross weight ≤12 kg (≤15 kg tag-on).
**Scope:** `QUESTION` — applicable when destination = HCA (Hallmark Australia)
**Error example:** HCA order; wholesale bag is standard PE, not LDPE recycled; gross weight = 13 kg → both fail
**Correct example:** LDPE ≥30% recycled bag confirmed; gross weight = 11.5 kg → Pass

---

### 6.9 Retail packaging

---

**ID:** 6.9.1
**Field / Location:** Retail Packaging checkpoint
**What to check:** Retail packaging must match spec, DAS/VAS, and PO on: quantity, packing components, packing sequence. Materials must be clean, undamaged, free from smears and odors. Standard pass remark: "Conform to Specs, PO and approved ship test report."
**Scope:** `SECTION` — cross-check retail packaging against spec, DAS, and PO
**Error example:** PO specifies 12 retails per wholesale; actual pack = 10; checkpoint = Pass
**Correct example:** Actual pack = 12 retails per wholesale; matches spec; checkpoint = Pass

---

### 6.10 Polybag (US and Canada retail packages)

---

**ID:** 6.10.1
**Field / Location:** Polybag checkpoint
**What to check:** Minimum thickness >1 mil (0.0254 mm). If bag opening width (flat) ≥5 inches, suffocation warning mandatory in English + French + Spanish (not required for wholesale polybags). Warning repeats every 18 inches. "WARNING" in ALL CAPS, min. 4 mm height. Font size by bag perimeter: ≥60 in → 24 pt | 40–59 in → 18 pt | 25–39 in → 14 pt | <25 in → 10 pt.
**Scope:** `QUESTION` — applicable when product is in retail polybag shipping to US or Canada
**Error example:** Retail polybag width = 6 inches; no suffocation warning on bag
**Correct example:** Retail polybag width = 6 inches; suffocation warning present in EN/FR/ES; font meets size requirement

---

### 6.11 Fragile label

---

**ID:** 6.11.1
**Field / Location:** Shipper Dimensions & Weight & Marks / photo section
**What to check:** If a fragile label or marking is present on the shipper, the report must include a photo of it. Symbol standard: 75 mm tall, 31 mm from top flap score and 31 mm from corner score.
**Scope:** `QUESTION` — applicable when fragile label is present on shipper
**Error example:** Fragile icon on shipper carton; no photo of it in the report
**Correct example:** Fragile label photo included; caption references position and dimensions

---

### 6.12 Packing method

---

**ID:** 6.12.1
**Field / Location:** Shipper Packaging checkpoint
**What to check:** Packing method recorded in the report must conform to the ship test report, COP, and/or packaging specification.
**Scope:** `FULL REPORT` — cross-check packing method against ship test report reference
**Error example:** Ship test specifies 3-layer carton; inspector records 2-layer carton; checkpoint = Pass
**Correct example:** 3-layer carton confirmed; matches ship test; checkpoint = Pass

---

### 6.13 Dayspring carton mark

---

**ID:** 6.13.1
**Field / Location:** Shipper Dimensions & Weight & Marks (Dayspring orders)
**What to check:** As of April 2025, "Case Count: xx of xxx" must NOT appear on the Dayspring carton mark. Dayspring corner label: 4"×4", top right corner of long carton side, 1 per carton. Must include: DaySpring item number (1" font, scannable barcode), prime item number, carton quantity, merchandise description, date of manufacture. Item number = UPC code with first and last digits removed (10-digit result).
**Scope:** `QUESTION` — applicable when channel = Dayspring
**Error example:** Dayspring carton mark includes "Case Count: 3 of 24" line → must be removed
**Correct example:** Dayspring carton mark contains all required fields; no "Case Count" line

---

### 6.14 International orders – carton end panels

---

**ID:** 6.14.1
**Field / Location:** Shipper Dimensions & Weight & Marks (international non-Canada orders)
**What to check:** End panels must include: PO Number, Stock No., Description, Qty, Net weight (kg), Gross weight (kg), Dimensions (cm), Vendor ID, Production Date (MMYY), Made In, REUSE #. Font: 19 mm for PO# and SKU; 13 mm for other fields.
**Scope:** `QUESTION` — applicable when destination = international (non-Canada)
**Error example:** End panel missing Vendor ID; Production Date in DD/MM/YYYY format instead of MMYY
**Correct example:** All fields present; PO# in 19 mm font; other fields in 13 mm font; Production Date = 0526

---

## Section 7 – Product / Visual Checks

### 7.1 DAS comparison

---

**ID:** 7.1.1
**Field / Location:** VAS/DAS Check section
**What to check:** Report must document a side-by-side comparison of the production sample against the DAS. Result cannot be left blank.
**Scope:** `QUESTION`
**Error example:** VAS/DAS Check section shows result = Pass but no comparison remark or photos
**Correct example:** Remark states "Production sample compared to DAS: color, construction, labeling — all conform"; comparison photos included

---

### 7.2 Spell check

---

**ID:** 7.2.1
**Field / Location:** Spell Check checkpoint
**What to check:** Spell check must be performed on logos, text, event numbers, and all characteristics on packaging, verified against DAS and spec. Checkpoint recorded as "Yes" (match) or flagged if discrepancy found.
**Scope:** `QUESTION`
**Error example:** Spell Check = Yes; retail package contains "BIRTHAY" instead of "BIRTHDAY" — should have been caught
**Correct example:** Spell Check performed; "BIRTHDAY" confirmed correct; checkpoint = Yes

---

### 7.3 Logo check

---

**ID:** 7.3.1
**Field / Location:** Retail Labeling, UPC & COO checkpoint / DAS comparison
**What to check:** The Hallmark crown logo must be present and correctly applied to retail packaging where required by spec.
**Scope:** `SECTION` — cross-check logo presence against spec requirement
**Error example:** Spec requires Hallmark crown logo on front panel; logo missing on production sample; checkpoint = Pass
**Correct example:** Crown logo present and correctly positioned per spec; noted in DAS comparison remark

---

### 7.4 Warning statement and license / copyright

---

**ID:** 7.4.1
**Field / Location:** Warning Statement and License checkpoint
**What to check:** Copyright and licensing information on the retail product must match spec and DAS. Any discrepancy must be failed and remarked.
**Scope:** `SECTION` — cross-check copyright text on product/package against spec and DAS
**Error example:** Copyright year on retail package = 2023; spec and DAS show 2025 → discrepancy; checkpoint = Pass
**Correct example:** Copyright year matches spec and DAS; checkpoint = Pass

---

### 7.5 Reese's Law (button cell battery)

---

**ID:** 7.5.1
**Field / Location:** Reece's Law Check checkpoint
**What to check:** Applicable only to items with button cell batteries shipping to US/Canada. Both product and retail packaging must show compliant warning statements. Exception: heavily embossed/textured products — product marking not required. Not applicable to Keepsake 2024 products or toy products for children under 14 complying with applicable Toy Standard. Items without button cell batteries or non-US/Canada shipments → N/A.
**Scope:** `SECTION` — cross-check battery type, destination, and warning statement presence
**Error example:** Product has button cell battery; ships to US; retail packaging has no Reese's Law warning → must fail
**Correct example:** Product has button cell battery; ships to US; warning on both product and packaging; checkpoint = Pass

---

### 7.6 PID number (2D products only)

---

**ID:** 7.6.1
**Field / Location:** PID Number checkpoint
**What to check:** PID number on display boards must be checked and recorded for 2D products. If no display board → N/A.
**Scope:** `QUESTION` — applicable when product = 2D and display board is present
**Error example:** 2D product with display board; PID Number checkpoint = N/A with no justification
**Correct example:** PID number verified against spec; checkpoint = Pass; or "No display board — N/A"

---

### 7.7 Sharp point / sharp edge check

---

**ID:** 7.7.1
**Field / Location:** Workmanship remarks / sharp point checkpoint
**What to check:** Must be recorded for ALL Hallmark products. All products are free of shape hazard by default. If a sharp point or edge is found (including areas not designed to be sharp), report and escalate to PE.
**Scope:** `QUESTION`
**Error example:** Sharp edge found on decorative product (not intended to be sharp); recorded as Minor defect; no PE escalation
**Correct example:** Sharp edge found; remark states "Escalated to PE [name] on [date] for evaluation"

---

## Section 8 – Test Results

### 8.1 General test recording rules

---

**ID:** 8.1.1
**Field / Location:** Additional Tests section / all test checkpoints
**What to check:** All applicable tests must appear in the report with their result. Any test listed in the "Additional Tests" section of the booking or spec must be documented with supporting photos. If a test fails, number of failed pieces must be stated in remarks. If a test is not required, supporting evidence must be provided (reference to PP report, spec page, or email).
**Scope:** `FULL REPORT` — scan all test checkpoints; flag any applicable test missing from the report
**Error example:** Spec requires a Shake Test; no Shake Test section or result anywhere in the report
**Correct example:** Shake Test documented in Additional Tests section with result and 1 photo

---

**ID:** 8.1.2
**Field / Location:** Workmanship sample / abuse test remarks
**What to check:** Abuse test samples (pull test, glue joint test) must be drawn from bulk separately and noted as such — not from the visual inspection sample pool.
**Scope:** `SECTION`
**Error example:** Pull test performed but no remark clarifying whether samples came from visual pool or separate bulk draw
**Correct example:** Remark states "Pull test samples drawn separately from bulk, not from visual inspection sample"

---

### 8.2 Function check vs. formal function test

---

**ID:** 8.2.1
**Field / Location:** Visual inspection section + Function Test (Tests section)
**What to check:** A function check (1–2 cycles per sample) must appear in the visual inspection section. The formal function test (25 cycles per spec) must appear separately in the test section. These are two distinct checkpoints and cannot be merged. Sample size for FR KPS, Greeting Cards, Houseware formal function test = 1 unit.
**Scope:** `SECTION` — verify both checkpoints are present and distinct
**Error example:** Only 1 function result recorded for the entire report; no distinction between function check and formal function test
**Correct example:** Visual section: "Function check — 1 cycle per sample — Pass"; Test section: "Function test — 25 cycles — 1 unit — Pass"

---

### 8.3 UPC scanning test

---

**ID:** 8.3.1
**Field / Location:** Carton Labels & UPC Check / Retail Labeling checkpoint
**What to check:** Every barcode on the carton and retail package must be scanned, with a photo in the report. Sample sizes: shipper carton = 1 carton (all barcodes on corner label); retail Greetings/Print Specialty/Gift/Ornament = 1 pc; retail International/Crayola/M&S = 10 pcs.

Acceptance criteria:
| Metric | Pass | Acceptable | Fail |
|---|---|---|---|
| 1st scan rate | ≥90% | 75–89% | <75% |
| Decodability | A (>0.62) | C (≥0.25) | D (<0.25) |
| Magnification | 100% | >80% | <80% |
| Quiet zone | 1/4" | 1/8" | QZ/SS warn |

Minimum grade: C (standard); B for HCA. Consistency rule: same label alternating C/D over 10 scans — ≥7/10 pass = overall pass; <7/10 = fail.

**Scope:** `SECTION` — cross-check sample size, scan results, and grade against channel and product type
**Error example:** M&S order; only 1 retail unit scanned instead of 10
**Correct example:** M&S order; 10 retail units scanned; all grades ≥C; checkpoint = Pass

---

### 8.4 Hanger test

---

**ID:** 8.4.1
**Field / Location:** Do-it/Euro Hook/Hang Tab checkpoint (or Hanger Check)
**What to check:** Applies to 2D products with a hook or Do-it, and 3D Keepsakes with a hook. Test: 3× product weight held for 1 minute. Result must be recorded as Pass or Fail; if failed, pull-off force data must appear in remarks.
**Scope:** `QUESTION` — applicable when product has a hook, Do-it, or hanger
**Error example:** 2D product with Do-it hook; no hanger test result recorded; checkpoint = N/A
**Correct example:** Do-it hook tested at 3× product weight for 1 min; result = Pass; recorded in report

---

### 8.5 Pull test

---

**ID:** 8.5.1
**Field / Location:** Pull test / Additional Tests section
**What to check:** Result must be recorded. If failed, pull-off force data must appear in remarks. No photo required unless failed. If a DIY weight pull tester was used, the report must state this.
**Scope:** `QUESTION`
**Error example:** Pull test failed; no pull-off force data in remarks; no photo
**Correct example:** Pull test failed; remark states "Pull-off force: 1.2 N (spec: ≥3 N)"; close-up photo of failure point included

---

### 8.6 Adhesive tape test (paint/coating adhesion)

---

**ID:** 8.6.1
**Field / Location:** Additional Tests section
**What to check:** Result must be recorded. No photo required unless failed. Not required for Gift Presentation & Package Expressions BU products, nor for fabric/plush items. For glass or ceramic décor not handled in the coated area: up to 25% coating removal is acceptable.
**Scope:** `QUESTION` — not applicable for Gift Presentation & Package Expressions or fabric/plush
**Error example:** Ceramic décor; coating removal = 20% in non-handled area; checkpoint = Fail → should be Pass (≤25% acceptable)
**Correct example:** Ceramic décor; coating removal = 20% in non-handled area; checkpoint = Pass with remark "20% removal, within 25% tolerance for non-handled area"

---

### 8.7 Grammage / paper weight test

---

**ID:** 8.7.1
**Field / Location:** Grammage of Paper and Paperboard checkpoint
**What to check:** Result must be recorded for 5 samples. Acceptable tolerance: ±5% vs. label claim. A photo and the actual measurement data must appear in the report.
**Scope:** `QUESTION`
**Error example:** Only 3 samples measured; no photo; measurements listed in remark but no data in structured field
**Correct example:** 5 samples measured: 347, 352, 355, 349, 351 GSM; standard = 350 GSM; all within ±5%; photo included

---

### 8.8 Glue joint test

---

**ID:** 8.8.1
**Field / Location:** Additional Tests section
**What to check:** Result must be recorded per FR report instructions.
**Scope:** `QUESTION`
**Error example:** FR report requires glue joint test; no result recorded in report; checkpoint absent
**Correct example:** Glue joint test recorded in Additional Tests; result = Pass; per FR report instruction

---

### 8.9 FHSA test (electrical products only)

---

**ID:** 8.9.1
**Field / Location:** Techno Function / Additional Tests section
**What to check:** Results for 5 samples must be recorded: working current <200 mA, standby current <10 µA, voltage per supplier batteries, dB 75–85 dB (Keepsake). "Battery Powered Product Evaluation Report" from factory must be referenced. A photo of the recorded test values must be included.
**Scope:** `QUESTION` — applicable when product is electrical/has sound or light function
**Error example:** Electrical ornament; FHSA test results not recorded; no photo of test values
**Correct example:** 5 samples tested; working current avg 45 mA; standby 2 µA; dB avg 78 dB; photo of meter readings included

---

### 8.10 Envelope seal test

---

**ID:** 8.10.1
**Field / Location:** Envelope Seal Test checkpoint
**What to check:** Applicable to Hallmark UK, Hallmark UK Own Brand, Hallmark Australia, and M&S only. 10 envelope samples. Pass = fiber pull detected after 20 min. Fail = flap opens before 20 min, or no fiber pull after 20 min. 1 photo of tested sample showing tearing area required.
**Scope:** `QUESTION` — applicable when channel = HMK UK, HMK UK Own Brand, HCA, or M&S
**Error example:** M&S order; envelope seal test conducted on only 5 samples; no photo of tearing
**Correct example:** M&S order; 10 samples tested; fiber pull detected on all 10; photo of tearing area included; checkpoint = Pass

---

### 8.11 Carton drop test

---

**ID:** 8.11.1
**Field / Location:** Additional Tests section
**What to check:** Carton drop test is mandatory when ANY of the following apply: (1) Hallmark engineering requested it in spec or email, (2) product is ceramic or glass, (3) any product dimension >16", (4) item previously failed ship test even once, (5) any fragile note/icon/sign on packaging. If 1st lot passed, subsequent lots do not require it (unless a new trigger applies). Any breakage must be escalated to Hallmark responsible Engineer.
**Scope:** `FULL REPORT` — cross-check product type, spec/email requests, packaging, and prior ship test history
**Error example:** Product is ceramic; no carton drop test in report; not flagged as missing
**Correct example:** Product is ceramic; carton drop test documented in Additional Tests; result = Pass; no breakage

---

## Section 9 – Report Photos

### 9.1 General photo rules

---

**ID:** 9.1.1
**Field / Location:** All photos throughout the report
**What to check:** All photos must be in landscape orientation and have a description caption. Date format in reports must be DD-Month-YYYY (e.g., 17-July-2020).
**Scope:** `FULL REPORT` — scan all photos for orientation, captions, and date format
**Error example:** 3 photos in portrait orientation; 2 photos have no caption; date shown as "2026/05/11"
**Correct example:** All photos landscape; all captioned; date = "11-May-2026"

---

### 9.2 Required photos per section

---

**ID:** 9.2.1
**Field / Location:** Carton / Shipper photo section
**What to check:** Minimum 3 photos required: (1) 45° view showing corner label position and shipping mark, (2) close-up of corner label (both sides in one photo if possible), (3) photo allowing easy count of wholesale quantity (rows/columns/layers visible).
**Scope:** `SECTION`
**Error example:** Only 1 carton photo; corner label not visible; no quantity count photo
**Correct example:** 3 carton photos meeting all 3 requirements above

---

**ID:** 9.2.2
**Field / Location:** Wholesale package photo section
**What to check:** Minimum 2 photos: (1) side view showing wholesale label/marking, (2) view showing number of retails inside one wholesale.
**Scope:** `SECTION`
**Error example:** 1 wholesale photo showing only the outside; retails inside not shown
**Correct example:** 2 photos: wholesale label visible; open wholesale showing 12 retail units inside

---

**ID:** 9.2.3
**Field / Location:** Retail package photo section
**What to check:** Minimum 3 photos: front view, back view, close-up of retail labeling. If already present in DAS check section, no duplication needed.
**Scope:** `SECTION`
**Error example:** Only front view present; no back view; no label close-up
**Correct example:** Front, back, and label close-up photos present; or noted as already covered in DAS section

---

**ID:** 9.2.4
**Field / Location:** DAS check photo section
**What to check:** 8–10 photos required, DAS and production sample in the same photo: front/back/bottom of retail package, front/back of product, additional side views if applicable, 1 group photo showing DAS alongside 4–6 production units.
**Scope:** `SECTION`
**Error example:** DAS photos show only the production sample; DAS not visible in any photo
**Correct example:** Each photo shows DAS and production sample side by side; group photo with 5 production units + DAS included

---

**ID:** 9.2.5
**Field / Location:** UPC scan photos
**What to check:** UPC scan on corner label = 4 photos. UPC scan on retail package = 1 photo. Each barcode must have a corresponding photo.
**Scope:** `SECTION`
**Error example:** Corner label has 2 barcodes; only 2 scan photos provided instead of 4
**Correct example:** 4 scan photos for corner label barcodes + 1 for retail package barcode

---

**ID:** 9.2.6
**Field / Location:** Defect photos (Workmanship section)
**What to check:** Every Major defect: 1 global view + 1 close-up. Defects >1 cm: ruler visible in photo; length/area in caption.
**Scope:** `SECTION` — cross-check number of Major defects against defect photo count
**Error example:** 1 Major defect; only 1 photo (close-up only); no global view
**Correct example:** 1 Major defect; 2 photos: global view of product + close-up of defect area with ruler

---

## Section 10 – Channel-Specific AQL/AOQL Summary

---

**ID:** 10.1.1
**Field / Location:** Inspection type / AOQL field (report header)
**What to check:** Verify the inspection type used matches the channel-specific requirement below.

| Channel | Standard | Critical | Major | Minor | Total |
|---|---|---|---|---|---|
| Marks & Spencer | AQL Level II | 0 | 1.5 | 4.0 | 4.0 |
| Crayola | AQL Level II | 0 | Functional 0.4 / Visual 1.5 | 4.0 | — |
| Dayspring | AOQL 3.0% | — | — | — | — |
| Nihon JP orders | AOQL 1.5% | — | — | — | — |
| Nihon non-JP orders | AOQL 3.0% | — | — | — | — |
| 2D Walmart FOB | AQL Level I | 0 | 1.5 | 4.0 | — |
| Cracker Component | AQL Level II | 0 | 1.0 | 2.5 | — |
| Cracker (assembled) | AQL Level II | 0 | 1.5 | 4.0 | 4.0 |
| UK / HCA / Netherlands | AOQL 3.0% | — | — | — | — |

**Scope:** `FULL REPORT` — cross-check destination/channel against inspection type and AQL values in report header
**Error example:** Channel = M&S; report uses AOQL 3.0% → wrong, must use AQL Level II
**Correct example:** Channel = M&S; report uses AQL Level II with Critical 0 / Major 1.5 / Minor 4.0

---

## Section 11 – Pass / Fail Decision Logic

---

**ID:** 11.1.1
**Field / Location:** Overall result (report header)
**What to check:** Overall result must be PASS only if ALL conditions below are met. If any single condition fails, overall result must be FAIL.

**PASS requires ALL of:**
- SR test: Passed (or documented exemption)
- FR test: Passed (or documented exemption)
- Visual defect count ≤ C#
- Critical defects: 0
- Functional defect count ≤ C#/2

**FAIL triggered by ANY of:**
- SR not passed, invalid, or missing without exemption
- FR not passed, invalid, or missing without exemption
- Visual defect count > C#
- Any critical defect found
- Functional defect count > C#/2
- Barcode grade below C (or below B for HCA)
- Required test result missing from report

**Scope:** `FULL REPORT` — cross-check overall result against all conditions above
**Error example:** FR checkpoint = Failed; overall result = Pass → inconsistent
**Correct example:** FR checkpoint = Failed; overall result = Fail

---

**ID:** 11.1.2
**Field / Location:** Inspector's remark / escalation note
**What to check:** PE escalation is required and must be noted in the report for: all FAIL results, functional defect count > C#/2, any finding of sharp point/edge/small part, carton drop test breakage.
**Scope:** `FULL REPORT`
**Error example:** Overall result = Fail; no mention of PE escalation in any remark
**Correct example:** Overall result = Fail; remark states "Escalated to PE [name] on [date]"
