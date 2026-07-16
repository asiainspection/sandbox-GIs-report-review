# Joseph Ribkoff Inspection Report Review – Rules Reference

> Sources: Joseph Ribkoff Golden Report (PSI 1399166, 26-Aug-2025) [Type 2]; Joseph Ribkoff Measurement Guidelines V1.0 July 2019 [Type 4]; Joseph Ribkoff General Instructions (images 1–4, undated) [Type 1]; Joseph Ribkoff Claimed Issues Table (image 3) [Type 3]
> Last compiled: June 2026

---

## Glossary of technical terms

**AQL (Acceptable Quality Level)**
The maximum percentage of defective units that is considered acceptable in a sample. Defined separately for three defect severities: Critical (CRI), Major (MAJ), Minor (MIN).
Example: AQL CRI:0 / MAJ:2.5 / MIN:4.0 means zero critical defects are acceptable, up to 2.5% major defects, and up to 4.0% minor defects.

**Sampling level**
Determines how large the sample size is relative to the total lot size. Common levels used in QIMA inspections:
- General Level I, II, III (II is the most common standard)
- Special levels S1 to S4 (smaller samples, used for measurements or destructive tests)

The sampling level is defined in the client's GIs and must not be changed by the inspector without documented reason.

**GIs (General Instructions)**
The client's inspection rulebook. It defines everything specific to that client: AQL values, defect classification, required documents, photo rules, measurement rules, etc. GIs are provided by the client and are the primary reference for every verification in the report.

**IRF (Inspection Request Form)**
The booking document created by the client that triggers the inspection. It contains the PO number, product details, factory address, shipment date, and quantities ordered. Inspectors must verify that what they find on site matches what is stated in the IRF.

**PO (Purchase Order)**
The commercial document between buyer and supplier. The PO number is a key identifier that must appear consistently across the report, the product labels, hangtags, and cartons.

**POM (Point of Measurement)**
A specific location on a garment or product where a measurement must be taken, following a defined method. POMs are referenced by code (e.g. T1, K44, P6) and are defined in the client's GI measurement template. The inspector must measure exactly the POMs required by the GIs for the product category, no more, no less.

**Tolerance**
The acceptable deviation from the specification measurement. Expressed as +/- a value (e.g. +/- 1/2 inch). Any measurement outside the specified tolerance is "out of tolerance" and must be flagged and highlighted in the measurement chart.

**DAS (Design Approval Sample) / VAS (Visual Approval Sample)**
The approved reference sample against which the bulk production is compared during inspection. The DAS/VAS is provided by the client or factory and must be present on site during the inspection. It is used to verify color, style, construction, labels, and packaging. For Joseph Ribkoff, the approval sample is identified by a green "QIMA SAMPLE" tag.

**COC (Certificate of Conformance)**
A document signed at the end of the inspection confirming that the inspector has completed the inspection according to QIMA procedures. Must be signed by the inspector and, depending on GI requirements, also by a factory representative.

**Factory Disclaimer**
A document signed by both the inspector and the factory representative at the start of the inspection, confirming the factory's agreement to the inspection process.

**Draft Report**
An intermediate version of the inspection report reviewed and signed on site before final submission. Signing requirements (inspector only vs inspector + factory rep) are defined in the GIs.

**BLOCKING issue**
An error severe enough to cause the report to be rejected and returned for correction before it can be submitted to the client. Typically involves incorrect AQL, missing required documents, wrong defect classification, or missing critical information.

**MINOR issue**
An error that requires correction or a remark but does not alone prevent report submission. Typically involves missing captions, incorrect photo types, or incomplete comments.

**Defect severity levels**
- **CRITICAL (CRI):** a defect that could cause harm to the consumer or creates a serious legal/safety issue. Acceptance point is almost always 0.
- **MAJOR (MAJ):** a defect that makes the product unfit for its intended use or significantly affects its appearance.
- **MINOR (MIN):** a defect that is noticeable but does not significantly affect the product's use or appearance.

**Checklist / checkpoint**
A specific verification step within a section of the QIMAone report. Each checkpoint has a result (Pass/Fail/N/A) and may require photos, comments, or attached files.

**Sample size**
The number of units selected from the lot for inspection. Determined by the sampling level and the AQL table (ISO 2859-1 or equivalent). Must match what the GIs specify.

**PSI (Pre-Shipment Inspection)**
An inspection performed when production is 100% finished and at least 80% packed, before the goods leave the factory.

**DUPRO (During Production Inspection)**
An inspection performed mid-production, when at least 20% of goods are finished and packed.

---

## QIMAone report structure

A standard QIMAone inspection report contains these sections in order:

1. **Report header** — inspection reference, type, product, date, overall result
2. **Inspector's remark** — free text field filled by inspector
3. **PO & Product details** — booking information
4. **Workmanship** — defect sampling results
5. **Tests & checkpoints** — checklist results by category
6. **Factory review** — factory conditions and documents
7. **Starting pictures** — photo of inspector at factory
8. **Attachments** — measurement files and other documents
9. **Acknowledgments & signatures** — inspector and factory representative signatures
10. **Summary review** — final remarks

---

## Auto-generated fields (never flag these)

The following fields are populated automatically by the QIMAone platform and cannot be modified by the inspector:

- QIMA inspection ID and reference number
- Inspection date and planned date
- Timestamps on photos and acknowledgments
- GPS/geolocation coordinates (start, complete, site address)
- Workflow completion status ("Has been fully completed")
- Overall result (Pass/Fail) — calculated from section results
- Section results (Pass/Fail) — calculated from checkpoint results
- Defective rate percentage — calculated from counts entered
- Total defects found — summed automatically
- Acceptance point — determined by AQL table
- Inspector name and profile photo
- "Generated on QIMAone" footer
- Page numbers

---

## Manually filled fields (check these)

The following fields are entered by the inspector and are subject to review:

- Starting photo (uploaded by inspector)
- Produced and packed quantities
- AQL values and sampling level (if manually set)
- Reason for sampling parameter change
- All checkpoint results (Pass/Fail/N/A selected by inspector)
- All comments and remarks fields
- All photos uploaded to checkpoints
- Defect names selected and quantities entered
- Defect severity assigned to each defect
- Measurement file attached and screenshot uploaded
- Factory address entered in inspection location
- Tools calibration answer and comment
- QIMA documents signed answer
- Summary review remarks

---

## Mandatory pictures checklist

> Source: Joseph Ribkoff Golden Report (PSI 1399166) and General Instructions

| # | Required photo | Location in report | Status rule |
|---|---|---|---|
| 1 | Inspector standing in front of factory name/logo | Starting pictures | Must be present; factory identifier clearly visible |
| 2 | Cartons stacked on pallets | Outer Packing & Shipping Marks | Must be present |
| 3 | Carton seals | Outer Packing & Shipping Marks | Must be present |
| 4 | Side label of carton (showing lot/style/PO/size) | Outer Packing & Shipping Marks | Must be present |
| 5 | Cartons before random selection | Random carton selection | 1 photo required |
| 6 | Cartons after random selection | Random carton selection | 1 photo required |
| 7 | Inner packing / polybag | Inner Packing & Unit Packing | 1 photo required |
| 8 | Product color (bulk) | Product Color | 1 photo minimum |
| 9 | Product style and construction | Product Style & Construction | 1 photo required |
| 10 | Main label (bulk vs. approval sample side by side) | Product Labels | Required; both samples visible; grouped with all other labels |
| 11 | Care label (bulk vs. approval sample side by side) | Product Labels | Required; grouped with all other labels |
| 12 | All hangtag views | Product Labels | Required; all hangtag faces grouped together |
| 13 | Approval sample comparison — product side by side | Approval Sample Comparison | Bulk and approval sample physically side by side; caption identifying approval sample required |
| 14 | Measurement chart print screen (screenshot of Excel) | Product Dimensions Result | Required; this section only; must be legible, not blurry |
| 15 | 1 photo per test performed | Tests checklist (each test checkpoint) | 1 photo per test; no photos if carton drop test passed |
| 16 | Stitch density — count visible on seam assembly | Stitch density check | From seam assembly only, not from main label; numeric count stated in comment |
| 17 | Ironing check — approval sample | Ironing, washing, treatment check | Side-by-side with bulk; caption required |
| 18 | Ironing check — bulk sample | Ironing, washing, treatment check | Side-by-side with approval; caption required |
| 19 | 1 photo per defect type found | Workmanship — defects checklist | Max 5 photos per defect type; 1 photo per color if multiple colors |
| 20 | Signed Factory Disclaimer | Are the QIMA documents signed? | Must be present |
| 21 | Signed Draft Report | Are the QIMA documents signed? | Must be present |
| 22 | Signed COC | Are the QIMA documents signed? | Must be present |
| 23 | Barcode scan result — 1 photo per barcode type | Barcode scanning test | Upload per barcode type, not just 1 global photo |

Status definitions:
- ✅ **Present** — photo is there and meets basic requirements
- ❌ **Absent** — photo is completely missing
- ⚠️ **Incomplete** — photo exists but does not fully meet requirements (wrong angle, missing caption, wrong count, blurry, etc.)

Any ❌ or ⚠️ row must have a corresponding error entry in the error list.

**Photos explicitly prohibited (do not include unless test/check fails):**
- Carton drop test photos — omit if passed
- Box measuring photos (tape measure on carton sides)
- Weight scale reading photos
- General factory environment photos (exterior, inspector walking)

---

## How to read this document

Each rule entry contains:
- **ID** — unique rule identifier (section.subsection.rule)
- **Field / Location** — where to look in the report
- **What to check** — the exact verification to perform
- **Scope** — `QUESTION` (check only that field), `SECTION` (cross-check within the same checklist section), `FULL REPORT` (cross-check across multiple sections or documents)
- **Error example** — a concrete example of what a wrong value looks like
- **Correct example** — a concrete example of what the correct value looks like
- **Severity** — `BLOCKING`, `MINOR`, or `⚠️ TO CONFIRM` (rule is valid but requires client confirmation before operational use)

---

## Section 1 – General Report Setup

### 1.1 Inspection Location

---

**ID:** 1.1.1
**Field / Location:** Inspection site address — report header / Factory Review checklist
**What to check:** Verify the full factory address is written in English and includes street, building, floor, city, province/state, country, and postal code. Address must not contain Chinese characters.
**Scope:** `QUESTION` — check the address field only
**Error example:** Address shown as "广东省汕头市科技东路11号" with no postal code
**Correct example:** "Floor 5, LongSheng Building, No.11, Keji East Rd., H&N Development, Shantou, GuangDong, China. Zip code: 515041"
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 1.1.2
**Field / Location:** Is the factory/workshop location same as booked? — Factory Review checklist
**What to check:** Confirm the on-site factory address matches the address recorded in the booking. If they differ, a clear remark must be added to the Inspector's Remark / Other Remarks section.
**Scope:** `FULL REPORT` — cross-check factory address against booking details
**Error example:** Inspector marks "Yes" with no remark, but the on-site address differs from the booked address
**Correct example:** Inspector marks "No" and adds: "Factory located at [actual address]; booking recorded [booked address]"
**Severity:** `BLOCKING`


```check
data_source: PO_booking
where: []
when: null
check: null
```

---

### 1.2 Inspector's Remark / Failure Remarks

---

**ID:** 1.2.1
**Field / Location:** Inspector's Remark — report header summary
**What to check:** Verify that a complete list of all defects found is provided, broken down by PO number, with a structured format: "PO xxx: X pcs defect found / Total: X% defect found." If large quantities of defective units are found in the bulk, this must be clearly explained at the beginning of this section.
**Scope:** `FULL REPORT` — cross-check defect list in remarks against defect details in the Workmanship section
**Error example:** Remarks section states only "3 defects found" with no PO breakdown and no percentage
**Correct example:** "PO 081901: 3 defects found (1 MAJ Untrimmed Thread Ends, 2 MIN Untrimmed thread ends <1/4"). Total: 6.00% defect found (3/50)"
**Severity:** `MINOR`


```check
data_source: in_report
where: [report.global_remark]
when: null
check: extract("Does the inspector remark list defects broken down by PO number and include a total defect percentage? Quote the sentence or null if absent.")
```

---

### 1.3 Production Status

---

**ID:** 1.3.1
**Field / Location:** Available Quantity Check — Quantity & Packaging checklist
**What to check:** Verify production status thresholds are met before proceeding with inspection. For PSI: finished quantity must be 100% AND packed quantity must be ≥ 80% to proceed. For DUPRO: both finished and packed quantities must be > 20% to proceed. If thresholds are not met, inform Quality and issue a missing inspection report.

| Service | Finished % required | Packed % required | Action if met | Action if not met |
|---|---|---|---|---|
| PSI | 100% | ≥ 80% | Proceed inspection | Packed < 80%: inform Quality; issue missing inspection report |
| DUPRO | > 20% | > 20% | Proceed inspection | Inform Quality; issue missing inspection report |

**Scope:** `QUESTION` — check the quantity fields in the Available Quantity Check section
**Error example:** PSI inspection proceeded with packed quantity at 65% without any remark or Quality notification
**Correct example:** PSI with 516 pcs packed (103%) out of 500 ordered — threshold met, inspection proceeds
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [product._first.real_packed_quantity, product._first.ordered_quantity]
when: null
check: ratio_at_least(0.8)
```

---

**ID:** 1.3.2
**Field / Location:** Available Quantity Details table — Quantity & Packaging checklist
**What to check:** Verify that any discrepancy between the booking quantity and the on-site quantity (shortage or overage) is clearly noted in the report with an explanation.
**Scope:** `FULL REPORT` — cross-check ordered quantity against produced and packed quantities
**Error example:** 516 pcs on site vs. 500 pcs booked, with no mention of the 16-unit overage anywhere in the report
**Correct example:** "Total 516 pcs / 103% packed in cartons. Overage of 16 pcs vs. booking of 500 pcs."
**Severity:** `MINOR`


```check
data_source: in_report
where: [report.global_remark]
when: product._first.real_packed_quantity != product._first.ordered_quantity
check: extract("Quote the sentence explaining the quantity shortage or overage vs booking, or null if absent.")
```

---

### 1.4 Summary Review

---

**ID:** 1.4.1
**Field / Location:** Summary review — end of report
**What to check:** For any "No" response recorded anywhere in the Inspection Details fields, a corresponding explanation must be present in the Summary Review section.
**Scope:** `FULL REPORT` — cross-check all "No" responses throughout the report against the Summary Review section
**Error example:** Tools calibration answered "No" with no corresponding explanation in the Summary Review
**Correct example:** Summary Review states: "Tools calibration: No — no calibration label on the weight scale provided by factory"
**Severity:** `MINOR`

> ⚠️ TO CONFIRM: The GI states this rule but does not define the exhaustive list of Inspection Details fields it applies to. Confirm the full scope with Joseph Ribkoff.


```check
data_source: in_report
where: [report.global_remark]
when: null
check: extract("For every 'No' answer recorded in inspection details, is there a matching explanation in the summary review or global remark? Answer true only if all are explained.")
```

---

## Section 2 – Documents and Booking Verification

### 2.1 Purchase Order and Style Number

---

**ID:** 2.1.1
**Field / Location:** PO ref and SKU — report header, care label, hangtag, carton marking
**What to check:** Confirm that the style number and PO number on the on-site product identification (care label header, barcode hangtag, shipping carton) exactly match the booking information. If they do not match, the service must be treated as failed, a missed inspection report issued, and the reason clearly stated.
**Scope:** `FULL REPORT` — cross-check booking style number and PO number against care label, hangtag, and carton markings
**Error example:** Booking references style 261938; measurement chart and report header show 261838
**Correct example:** Booking style 261740 matches the SKU on the care label header, the barcode hangtag, and the carton marking
**Severity:** `BLOCKING`


```check
data_source: PO_booking
where: []
when: null
check: null
```

---

**ID:** 2.1.2
**Field / Location:** Color code / description — General Information and product identification labels
**What to check:** If the color code or description on site does not match the booking, proceed with the inspection. Record the actual color(s) and quantity breakdown in the report with a remark identifying the discrepancy.
**Scope:** `FULL REPORT` — cross-check booking color information against on-site labels and hangtags
**Error example:** Booking states "Midnight Blue"; on-site product shows "Navy" with no remark
**Correct example:** Inspector proceeds and notes: "Color description on site is Navy 2166; booking reference is Midnight Blue. Quantities: [breakdown]."
**Severity:** `MINOR`


```check
data_source: PO_booking
where: []
when: null
check: null
```

---

**ID:** 2.1.3
**Field / Location:** Lot number — hangtag vs. carton marking
**What to check:** Verify that the lot number on the hangtag matches the lot number on the shipping carton. If they do not match, mark this as Failed and add a remark.
**Scope:** `SECTION` — cross-check lot number across hangtag and carton within the Specifications section
**Error example:** Hangtag shows Lot 081901; carton marking shows Lot 082001 — no remark provided
**Correct example:** Hangtag and carton both show Lot 081901; result recorded as conforming
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [report.global_remark]
when: null
check: extract("Do the lot numbers on hangtags match the lot numbers on shipping cartons? Answer true only if they match or a clear discrepancy remark is present.")
```

---

### 2.2 QIMA Documents

---

**ID:** 2.2.1
**Field / Location:** Are the QIMA documents signed? — Factory Review checklist
**What to check:** Confirm that the Factory Disclaimer, Draft Report, and COC are all signed by both the inspector and the factory representative. Photos of all signed documents must be included in the report.
**Scope:** `QUESTION` — check the signed documents field and verify photos are present
**Error example:** All 3 documents are listed as signed but no photos of the signed documents are uploaded
**Correct example:** 3 signed document photos uploaded, each captioned (e.g., "Factory Disclaimer — signed by inspector and factory representative")
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.are_the_qima_documents_signed.photo_count]
when: null
check: count_at_least(3)
```

---

## Section 3 – Packaging

### 3.1 Carton Selection and Packing Verification

---

**ID:** 3.1.1
**Field / Location:** Random carton selection — Product Specifications checklist
**What to check:** Confirm that cartons were selected fully randomly. If random selection was not possible, the result must be marked as Failed.
**Scope:** `QUESTION` — check the random carton selection result field
**Error example:** Inspector selects cartons all from the same pallet and marks the result as Pass
**Correct example:** Cartons selected randomly across the warehouse; result marked Pass with selected carton numbers listed
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.random_carton_selection.result]
when: null
check: in_set(PASS, FAIL)
```

---

**ID:** 3.1.2
**Field / Location:** Outer Packing & Shipping Marks — Product Specifications checklist
**What to check:** Verify the carton side reads "Made in China / Fabrique en Chine." If the wording is incorrect (e.g., "Fait en Chine"), record a MINOR defect remark but do not fail this section. Misspellings of color and country of origin on the carton are also MINOR defects requiring a remark but not a failure.
**Scope:** `QUESTION` — check the outer packing field and any associated remarks
**Error example:** Carton reads "Fait en Chine" and the inspector fails the Outer Packing section
**Correct example:** Carton reads "Fait en Chine"; inspector records a MINOR defect remark and passes the section
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.1.3
**Field / Location:** Outer Packing & Shipping Marks — Product Specifications checklist / report photos
**What to check:** Verify that photos of (1) cartons stacked on pallets, (2) carton seals, and (3) labelling on the side of boxes are included in the report under the Specifications section.
**Scope:** `SECTION` — check that the 3 required photo types are present in the Specifications section
**Error example:** Only a photo of the carton front label is provided; no pallet photo or seal photo
**Correct example:** 3 photos provided: cartons on pallet, carton seal visible, side label showing lot/style/PO/size information
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.outer_packing_shipping_marks_front_side.photo_count]
when: null
check: count_at_least(3)
```

---

**ID:** 3.1.4
**Field / Location:** Inner Packing & Unit Packing — Product Specifications checklist
**What to check:** Verify availability of mold prevention unit (anti-mold sheet or desiccant pack) and vent hole as specified in the tech pack. All products must have anti-mold sheets or desiccant packs.
**Scope:** `QUESTION` — check the inner packing checkpoint result and comments
**Error example:** Anti-mold sheet not present; inspector marks result as Pass without remark
**Correct example:** Anti-mold sheet confirmed in each polybag; vent hole confirmed; result marked Pass
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.1.5
**Field / Location:** Match packing info — Product Specifications checklist
**What to check:** Verify that the PO number, item/style number, and product description on the product identification inside the carton match the information on the corresponding export carton marking.
**Scope:** `SECTION` — cross-check inner product ID against outer carton marking
**Error example:** Carton is marked PO 081901, style 261740, but the hangtag inside shows PO 082001
**Correct example:** All products checked confirm matching PO 081901 and style 261740 on both inner and outer identification
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.match_packing_info.result]
when: null
check: equals(PASS)
```

---

**ID:** 3.1.6
**Field / Location:** Carton drop test — Product Specifications checklist / report photos
**What to check:** Photos of the carton drop test must NOT be included in the report unless the test fails. Only a failure requires photos.
**Scope:** `QUESTION` — check the photo content for the carton drop test checkpoint
**Error example:** 4 photos of cartons being dropped are uploaded even though the test passed
**Correct example:** No photos uploaded for the carton drop test; result marked Pass with comment "PASSED"
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.carton_drop_test.photo_count]
when: checklist.carton_drop_test.result equals PASS
check: count_at_most(0)
```

---

**ID:** 3.1.7
**Field / Location:** Outer Packing: Assortment, Dimensions & Weight — Product Specifications checklist / report photos
**What to check:** Photos of measuring the boxes (tape measure applied to carton sides or weight scale reading) must NOT be included in the report. Only the dimensions/weight results table and carton overview photos are required.
**Scope:** `QUESTION` — check the photo content for this checkpoint
**Error example:** 4 photos showing a tape measure placed against carton sides or a scale reading are uploaded
**Correct example:** Only the completed assortment/dimensions/weight table and carton overview photos are present
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.outer_packing_assortment_dimensions_weight.photo_count]
when: null
check: count_at_most(0)
```

---

**ID:** 3.1.8
**Field / Location:** Folding method — Inspector's Remark / Other Remarks
**What to check:** If the folding method on site differs from the tech pack specification, record this in the Other Remarks section. Do not fail the Specifications section for this reason.
**Scope:** `FULL REPORT` — cross-check folding method against tech pack and note in remarks if different
**Error example:** Folding method differs from tech pack; inspector fails the Specifications section
**Correct example:** Folding method differs from tech pack; inspector adds remark and passes the section
**Severity:** `MINOR`


```check
data_source: spec_sheet
where: []
when: null
check: null
```

---

**ID:** 3.1.9
**Field / Location:** Swift attaches — serial tags / Inspector's Remark
**What to check:** Swift attaches for serial tags must be black. If they are clear/transparent, record this as a MINOR defect in the Other Remarks section. Do not fail the Specifications section.
**Scope:** `QUESTION` — check the swift attach color on serial tags
**Error example:** Clear swift attaches found; inspector fails the Product Labels section
**Correct example:** Clear swift attaches found; inspector notes "Swift attaches are clear, not black — MINOR defect" in remarks and passes the section
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.1.10
**Field / Location:** Joker tags — denim pants only / Inspector's Remark
**What to check:** For denim pants, joker tags must be sewn on with thread. If attached with black plastic swift attaches instead, record this as a MINOR defect in the Other Remarks section. Do not fail the Specifications section.
**Scope:** `QUESTION` — check joker tag attachment method on denim pants only
**Error example:** Joker tags attached with black plastic swift attaches; inspector fails the Specifications section
**Correct example:** Joker tags attached with black plastic swift attaches; inspector notes "Joker tags not sewn — MINOR defect" in remarks and passes the section
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

### 3.2 Product Labels and Hangtags

---

**ID:** 3.2.1
**Field / Location:** Product Labels — Product Specifications checklist / report photos
**What to check:** Verify that all hang tags and care labels are photographed together and grouped in the Product Labels section of the report. Do not scatter label photos across different sections.
**Scope:** `SECTION` — check that all label types (main label, care label, hangtags) are present together in the same section
**Error example:** Care labels appear in the Workmanship section; hangtags appear only at the end of the report
**Correct example:** Main label, care labels, and all hangtag views are grouped together under Product Labels in the Specifications section
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.product_labels.photo_count]
when: null
check: count_at_least(1)
```

---

**ID:** 3.2.2
**Field / Location:** Product Labels — style number, PO, color, lot number consistency
**What to check:** Verify that the style number, PO number, color(s), and lot number are visible and consistent across: (1) the care and content label header (style number and PO number only), (2) the serial barcode hangtag (style number, color(s), PO number, lot number), and (3) the shipping carton marking (style number, color(s), sizes, PO number, lot number).
**Scope:** `FULL REPORT` — cross-check booking information against all 3 product identification components
**Error example:** The style number on the barcode hangtag reads 261838 instead of 261740
**Correct example:** Style 261740, PO 081901, and lot number consistently appear on care label, barcode hangtag, and carton marking
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.2.3
**Field / Location:** Product Logo — Product Specifications checklist
**What to check:** Carefully check the physical product for the brand logo, including on sewn-on trims and interior labels. Do not mark as N/A or "no product logo" without a thorough check of all surfaces and trims.
**Scope:** `QUESTION` — check the Product Logo result field and associated photos
**Error example:** Inspector marks "No Product Logo / N/A" when the logo is present on a sewn-on trim piece
**Correct example:** Inspector finds the Joseph Ribkoff logo on a sewn-on trim, marks the field correctly, and provides a photo
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.product_logo.result]
when: null
check: checklist.product_logo.result != NOT_APPLICABLE
```

---

**ID:** 3.2.4
**Field / Location:** Product Labels — brand logo comparison vs. approval sample
**What to check:** If there is any visual variation or damage to the brand logo label between the approval sample and the bulk, the report must be marked FAIL. Brand logo variation is a CRITICAL defect.
**Scope:** `FULL REPORT` — cross-check brand logo label between approval sample and bulk
**Error example:** Logo label font on bulk slightly differs from approval sample; inspector records as Minor and passes
**Correct example:** Logo label visually differs from approval sample; inspector marks Product Labels as Failed — CRITICAL defect
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.product_style_construction.result]
when: null
check: equals(PASS)
```

---

**ID:** 3.2.5
**Field / Location:** Size tab — Product Specifications checklist
**What to check:** If there is any visual variation between the approval sample size tab and the production size tab, the report must be marked FAIL. Size tab variation is a MAJOR defect.
**Scope:** `SECTION` — compare bulk size tab against approval sample within the Specifications section
**Error example:** Size tab color on bulk differs from approval; inspector records as Minor
**Correct example:** Size tab visually differs from approval sample; inspector marks Product Labels as Failed — MAJOR defect
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.2.6
**Field / Location:** Care content label — language sequence
**What to check:** Misprinting or variation in the sequence of languages on care content labels compared to the approval sample is NOT a reason to fail the report.
**Scope:** `QUESTION` — check the care label language sequence against approval sample
**Error example:** Language order on bulk care label differs from approval; inspector fails the Product Labels section
**Correct example:** Language order differs from approval; inspector notes this in remarks but passes the section
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 3.2.7
**Field / Location:** Hangers — Product Specifications checklist (when applicable)
**What to check:** If the lot is to be shipped on hangers, verify that hangers bear the Joseph Ribkoff logo as specified in the tech pack.
**Scope:** `QUESTION` — check hanger specification against tech pack when shipping on hangers is required
**Error example:** Products shipped on unbranded hangers when tech pack specifies Joseph Ribkoff logo hangers; no remark in report
**Correct example:** Joseph Ribkoff logo hangers confirmed on all units; noted as conforming to tech pack
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

## Section 4 – Workmanship

### 4.1 Defect Classification

---

**ID:** 4.1.1
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Classify untrimmed thread ends by length using the photo as evidence.

| Thread length | Severity |
|---|---|
| > 1/4" | MAJOR |
| < 1/4" | MINOR |

**Scope:** `QUESTION` — check the severity assigned to each untrimmed thread defect entry
**Error example:** Photo shows a thread end approximately 1/2" long; inspector classifies it as MINOR
**Correct example:** Photo shows a thread end approximately 1/2" long; inspector classifies it as MAJOR
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [workmanship.found_critical, workmanship.max_defects_critical]
when: null
check: workmanship.found_critical <= workmanship.max_defects_critical
```

---

**ID:** 4.1.2
**Field / Location:** Defects checklist — Workmanship section
**What to check:** All dirt and stain defects must be classified as MAJOR, regardless of size or location.
**Scope:** `QUESTION` — check the severity assigned to any dirt/stain defect entry
**Error example:** A stain on the front panel is classified as MINOR
**Correct example:** A stain on the front panel is classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.3
**Field / Location:** Defects checklist — Workmanship section
**What to check:** All stitching defects must be classified as MAJOR.
**Scope:** `QUESTION` — check the severity assigned to any stitching defect entry
**Error example:** A stitching skip on the side seam is classified as MINOR
**Correct example:** A stitching skip on the side seam is classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.4
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Yarn defects and holes must be classified as MAJOR.
**Scope:** `QUESTION` — check the severity assigned to any yarn defect or hole entry
**Error example:** A small hole in the fabric is classified as MINOR
**Correct example:** A small hole in the fabric is classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.5
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Wrinkles, over-press marks, or creases visible from 1 meter away must be classified as MAJOR.
**Scope:** `QUESTION` — check the severity of any wrinkle or press mark defect entry
**Error example:** A crease visible at 1 m on the front panel is classified as MINOR
**Correct example:** A crease visible at 1 m on the front panel is classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.6
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Any seam with excessive puckering, poor tension, or linking that causes the seam to open must be classified as MAJOR.
**Scope:** `QUESTION` — check the severity assigned to any seam quality defect entry
**Error example:** A puckered seam causing partial opening classified as MINOR
**Correct example:** A puckered seam causing partial opening classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.7
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Any product whose shape or form differs from the specifications or approval sample must be classified as a MAJOR workmanship defect.
**Scope:** `FULL REPORT` — cross-check product form against approval sample and tech pack
**Error example:** Product silhouette differs from approval sample; classified as MINOR
**Correct example:** Product silhouette differs from approval sample; classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 4.1.8
**Field / Location:** Defects checklist — Workmanship section
**What to check:** Any trim that is missing, not installed securely, or falling off must be classified as MAJOR. Trim placement and installation must conform to the tech pack and/or approval sample.
**Scope:** `FULL REPORT` — cross-check trim installation against tech pack and approval sample
**Error example:** A rhinestone is falling off; classified as MINOR
**Correct example:** A rhinestone is falling off; classified as MAJOR
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

### 4.2 Defect Photos

---

**ID:** 4.2.1
**Field / Location:** Defects checklist — Workmanship section / report photos
**What to check:** Include a maximum of 5 photos per defect type. If the same defect is found on more than 5 units, upload only 5 representative photos and document the total count in the report. For multiple references or colors, include only 1 photo per color.
**Scope:** `SECTION` — check the number of photos per defect entry in the Workmanship section
**Error example:** 20 photos of untrimmed threads uploaded for a single defect entry
**Correct example:** 5 photos maximum for "Untrimmed Thread Ends," representing the variety of affected units; report states total count
**Severity:** `MINOR`


```check
data_source: in_report
where: [report.defects_without_photo]
when: null
check: equals(0)
```

---

## Section 5 – Tests and Measurements

### 5.1 Product Dimensions (Measurement Chart)

---

**ID:** 5.1.1
**Field / Location:** Product Dimensions Result — Product Dimensions SL checklist; Attachments section
**What to check:** Verify that the measurement chart uses the correct Joseph Ribkoff mandatory POM template for the product category (see table below), that the style number in the chart matches the report SKU, and that the attached Excel file is named exactly "Measurement Chart - [style number]" (e.g., "Measurement Chart - 261740.xlsx").

| Category | Mandatory POMs | Template file |
|---|---|---|
| Jacket/Coat with closed front | 15 | POM JACKET _ 2022-04-07[1].xlsx |
| Jacket/Coat with open front | 18 | POM JACKET _ 2022-04-07[1].xlsx |
| Denim Jacket | 15 | POM JACKET _ 2022-04-07[1].xlsx |
| Sweater | 11 | POM KNITWEAR- SWEATERS-QIMA 2022-04-07[1].xlsx |
| Cardigan | 12 | POM KNITWEAR- SWEATERS-QIMA 2022-04-07[1].xlsx |
| Alpha Pull-On Pant | 10 | POM DENIM PANT _PULL ON PANT _ QIMA_ 2022-04-07[1].xlsx |
| Denim Pants | 11 | POM DENIM PANT _PULL ON PANT _ QIMA_ 2022-04-07[1].xlsx |
| Skirts 0–24 | 7 | POM SKIRT-QIMA_ 2022-04-07[1].xlsx |
| Skirts Pull-On XS–XXL | 5 | POM SKIRT-QIMA_ 2022-04-07[1].xlsx |
| Dress/Blouse | 17 | POM DRESSES -QIMA _ 2022-04-07[1].xlsx |
| Other products | Per booking attachment | Per booking attachment |

**Scope:** `FULL REPORT` — cross-check SKU in chart against report header; check file name in Attachments
**Error example:** File is named "Measurement chart format-joseph Ribkoff.xlsx"; style number in chart reads 261838 instead of 261740
**Correct example:** File is named "Measurement Chart - 261740.xlsx"; style number in chart reads 261740
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [checklist.product_dimensions_result.attachment_filenames]
when: null
check: filename_matches("Measurement Chart-*.xlsx")
```

---

**ID:** 5.1.2
**Field / Location:** Product Dimensions Result — measurement chart (Excel attachment) / report result field
**What to check:** All out-of-tolerance measurements must be highlighted in yellow in the Excel file. Apply the tolerance rule as follows: if all out-of-tolerance values are within ±1/8", classify as MINOR — add a remark and do not fail the section. If any tolerance exceeds ±1/8", highlight in yellow with red text — the measurement section must be marked FAIL.
**Scope:** `QUESTION` — check highlighting in the attached measurement chart and the result field
**Error example:** A POM in "Front HSP" is 5/8" out of spec; the cell is not highlighted and the measurement section is marked Pass
**Correct example:** The "Front HSP" cell is highlighted in yellow with red text; measurement section is marked Fail
**Severity:** `BLOCKING`


```check
data_source: spec_sheet
where: []
when: null
check: null
```

---

**ID:** 5.1.3
**Field / Location:** Product Dimensions Result — header row and content of measurement chart
**What to check:** Verify that (1) no column is left empty, (2) the style number is written in the chart header, (3) top-row bulk measurements are identified by size and/or color, and (4) no typo errors exist (e.g., letters entered in numeric result cells).
**Scope:** `QUESTION` — check chart structure and content for completeness and accuracy
**Error example:** A result cell in the M size column contains the letter "o" instead of a numeric value; style number field is blank
**Correct example:** All cells contain numeric values; style number reads "261740" in the chart header; columns are labeled by size (XS, S, M, L, XL, XXL)
**Severity:** `BLOCKING`


```check
data_source: spec_sheet
where: []
when: null
check: null
```

---

**ID:** 5.1.4
**Field / Location:** Product Dimensions Result — checklist photos and attachments
**What to check:** Measurement chart screenshots (print screen of POM) and the Excel file must both be uploaded exclusively in the Product Dimensions Result section. Product weight photos must NOT appear in this section. The print screen must be legible and not blurry.
**Scope:** `SECTION` — confirm measurement content is only in the Product Dimensions section, weight photos are absent, and print screen is readable
**Error example:** A photo of a weight scale reading is uploaded under Product Dimensions Result; the chart screenshot is too blurry to read
**Correct example:** Only the measurement chart print screen (sharp and readable) and the Excel attachment appear in the Product Dimensions Result section
**Severity:** `BLOCKING`


```check
data_source: spec_sheet
where: []
when: null
check: null
```

---

**ID:** 5.1.5
**Field / Location:** Product Dimensions — total sample size (denim category only)
**What to check:** For denim products, 20 units must be measured (effective September 10, 2021), using sampling level S4 or Level 1 based on booking quantity.
**Scope:** `QUESTION` — check total units measured for denim products
**Error example:** Denim pant inspection reports 13 units measured
**Correct example:** Denim pant inspection reports 20 units measured at sampling level S4
**Severity:** `BLOCKING`


```check
data_source: spec_sheet
where: []
when: null
check: null
```

---

### 5.2 Tests – Checklist

---

**ID:** 5.2.1
**Field / Location:** Tests checklist — all test checkpoints / report photos
**What to check:** Include only 1 photo per test in the checklist. For failed tests, provide only 1 photo per failure. Do not upload multiple photos for the same test.
**Scope:** `SECTION` — check the number of photos per test checkpoint
**Error example:** 4 photos uploaded for the Adhesive test even though it passed
**Correct example:** 1 photo uploaded for the Adhesive test showing the tape application
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.color_shading_check.photo_count]
when: null
check: count_at_most(1)
```

---

**ID:** 5.2.2
**Field / Location:** Stitch density check — Tests checklist / report photos
**What to check:** The stitch count per inch must be clearly stated as a numeric value in the report, with a supporting photo taken from a seam assembly — not from sewing on the main label.
**Scope:** `QUESTION` — check the stitch density result and photo source
**Error example:** Photo shows stitch density measured on the main label seam; no numeric count is stated in the comment
**Correct example:** Photo shows stitch count on a side seam assembly; report states "42 stitches per inch"
**Severity:** `MINOR`


```check
data_source: in_report
where: [checklist.stitch_density_check.comment]
when: null
check:
  - present
  - has_number
```

---

**ID:** 5.2.3
**Field / Location:** Ironing, washing, treatment check — Tests checklist / report photos
**What to check:** Include clear photos of both the approval sample and the bulk product side by side, each with a caption identifying which is which.
**Scope:** `QUESTION` — check that both approval and bulk sample photos are present and labeled
**Error example:** Only a photo of the bulk garment is provided with no approval sample for comparison
**Correct example:** 2 photos: "Ironing check — Approval Sample Checked" and "Ironing check — Bulk Sample Checked"
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 5.2.4
**Field / Location:** Barcode scanning test — Tests checklist / report photos
**What to check:** The UPC 13 scanner must be used (not UPC 12). Upload 1 photo per barcode type present on the product. If a barcode scan result is missing a leading zero, record this as a remark but do not fail this section.
**Scope:** `QUESTION` — check the barcode type used, the photo count per barcode type, and the interpretation of results
**Error example:** Inspector uses UPC 12 scanner and fails the section because a leading zero is missing; only 1 global photo uploaded despite 2 barcode types on the product
**Correct example:** Inspector uses UPC 13 scanner; 1 photo per barcode type uploaded; missing leading zero noted as remark; section passed
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 5.2.5
**Field / Location:** Symmetry check — Tests checklist / report photos
**What to check:** A verification of the front facing must be done and must be visible in the report. Fold the product on its symmetry axis or use a measurement tool to compare. The result and a supporting photo must be present.
**Scope:** `QUESTION` — check the symmetry check result and supporting photo
**Error example:** Symmetry check marked Pass with no photo showing the front facing verification
**Correct example:** Photo shows product folded on symmetry axis or front facing laid flat; result marked Pass with comment "PASSED"
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 5.2.6
**Field / Location:** Denim pants — leg twisting / fit model
**What to check:** If leg twisting is identified during inspection of denim pants, the pants must be fitted on a fit model to validate the finding. Clear front and back view photos must be taken on the fit model and uploaded.
**Scope:** `QUESTION` — check whether a fit model was used when leg twisting was identified
**Error example:** Leg twisting noted in remarks but no fit model photos are provided
**Correct example:** Leg twisting confirmed; clear front and back fit model photos uploaded and captioned
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 5.2.7
**Field / Location:** Tests checklist — fit model photos (all products)
**What to check:** Samples must be tried on a fit model and photos provided in the report.
**Scope:** `QUESTION` — check that fit model photos are present for the product inspected
**Error example:** No fit model photos anywhere in the report
**Correct example:** At least 1 photo of a sample tried on a fit model, captioned accordingly
**Severity:** `⚠️ TO CONFIRM`

> ⚠️ TO CONFIRM: The GI states this requirement for "all products" but the Golden Report for PSI 1399166 (dress) does not show fit model photos outside of the ironing check. Confirm whether fit model photos are mandatory for all product types or only for denim leg-twisting cases.


```check
data_source: external
where: []
when: null
check: null
```

---

### 5.3 Approval Sample Comparison

---

**ID:** 5.3.1
**Field / Location:** Approval Sample Comparison — Product Specifications checklist / report photos
**What to check:** Each approval sample comparison photo must show the on-site bulk product and the approval sample physically side by side. Each photo must have a caption explicitly identifying which item is the approval sample. The approval sample is identified by a green "QIMA SAMPLE" tag; if the tag is missing, note this in the Other Remarks section.
**Scope:** `SECTION` — check all approval sample comparison photos in the Specifications section
**Error example:** Photo shows only 2 bulk garments hanging together; no approval sample is visible; caption reads "Approval Sample Comparison" with no identification
**Correct example:** Photo shows bulk garment and approval sample (with green QIMA tag) side by side; caption reads "Approval Sample Comparison — left: approval sample, right: bulk"
**Severity:** `BLOCKING`


```check
data_source: external
where: []
when: null
check: null
```

---

## Section 6 – Report Photos

### 6.1 Photo Rules

---

**ID:** 6.1.1
**Field / Location:** Starting pictures — report photo section
**What to check:** Verify that a starting photo is present showing the inspector standing in front of the factory logo or name (factory identifier clearly visible).
**Scope:** `QUESTION` — check the Starting Pictures section
**Error example:** Starting photo shows the inspector in a corridor with no factory name or logo visible
**Correct example:** Starting photo shows inspector in front of a wall displaying the factory name in large characters or a logo sign
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [report.overall_result]
when: null
check: in_set(PASS, FAIL, PENDING)
```

---

**ID:** 6.1.2
**Field / Location:** All checklist sections — report photos throughout
**What to check:** Exactly 1 photo per checkpoint is required. Duplicate photos must not appear in the report. General factory environment photos (exterior, inspector walking around) must not be added.
**Scope:** `FULL REPORT` — review all photo placements and counts throughout the report
**Error example:** 3 identical photos of the same label are uploaded to the same checkpoint; photos of the factory exterior are added at the end
**Correct example:** 1 photo per checkpoint; no duplicate or general environment photos present
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 6.1.3
**Field / Location:** All photos — report-wide
**What to check:** All photos must have captions describing what they show. A photo without a caption is a reportable issue.
**Scope:** `FULL REPORT` — check that every photo in the report is accompanied by a caption
**Error example:** A photo of an open zipper is included with no description; reviewers cannot determine whether this indicates a defect
**Correct example:** Caption reads: "Zipper test — open and close check, PASSED"
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

**ID:** 6.1.4
**Field / Location:** Product Dimensions Result — report photos and attachments
**What to check:** Measurement chart screenshots and the Excel file must be uploaded only in the Product Dimensions Result section. Verify these materials do not appear in any other section of the report.
**Scope:** `FULL REPORT` — confirm measurement chart content appears only in the Product Dimensions Result section
**Error example:** Measurement chart screenshot is uploaded under the General Information section in addition to the Product Dimensions section
**Correct example:** Measurement chart screenshot and Excel file appear exclusively under Product Dimensions Result
**Severity:** `MINOR`


```check
data_source: external
where: []
when: null
check: null
```

---

## Section 7 – AQL / Sampling Summary

---

**ID:** 7.1.1
**Field / Location:** Workmanship sampling standards — Workmanship section header
**What to check:** Verify the workmanship inspection uses the correct sampling level and AQL values.

| Inspection type | Sampling level | Critical AQL | Major AQL | Minor AQL |
|---|---|---|---|---|
| All (PSI and DUPRO) | Level II | 0 | 2.5 | 4.0 |

**Scope:** `FULL REPORT` — cross-check the AQL values displayed in the Workmanship section header against the above
**Error example:** Report shows Major AQL = 4.0 for a PSI inspection
**Correct example:** Report shows Critical AQL = 0, Major AQL = 2.5, Minor AQL = 4.0, Sampling Level II
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [workmanship.aql_level_major]
when: null
check: equals(2.5)
```

---

**ID:** 7.1.2
**Field / Location:** Product Dimensions SL checklist — sampling header
**What to check:** Verify the measurement sampling uses the correct level and AQL.

| Product type | Sampling level | Measurement AQL | Minimum units measured |
|---|---|---|---|
| Non-denim | S3 | 4.0 | Per S3 table |
| Denim | S4 or Level 1 | 4.0 | 20 units |

**Scope:** `FULL REPORT` — cross-check measurement sampling level and unit count against the above requirements
**Error example:** Denim pant inspection reports 13 units measured at sampling level S3
**Correct example:** Denim pant inspection reports 20 units measured at sampling level S4, AQL 4.0
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [workmanship.aql_level_minor]
when: null
check: equals(4.0)
```

---

## Section 8 – Pass / Fail Decision Logic

---

**ID:** 8.1.1
**Field / Location:** Overall result — report header
**What to check:** The overall result must be PASS only if ALL conditions below are met. Any single failing condition must result in a FAIL overall result.

**PASS requires ALL of:**
- Workmanship defects within AQL limits (Critical = 0, Major ≤ acceptance number at AQL 2.5, Minor ≤ acceptance number at AQL 4.0)
- No brand logo variation or damage between approval sample and bulk (CRITICAL)
- No size tab variation between approval sample and bulk (MAJOR)
- Style number, PO number, and lot number on all product identification components match booking
- All measurement out-of-tolerance values are within ±1/8" (if any exceed ±1/8", result is FAIL)
- PSI packed quantity ≥ 80% of ordered quantity (otherwise inform Quality; issue missing inspection report)
- All mandatory tests passed or are N/A with documented justification

**FAIL triggered by ANY of:**
- 1 or more Critical defects found
- Major or Minor defects exceed the AQL acceptance number for the sample size
- Style number or PO number on any product identification component does not match booking
- Lot number on hangtag does not match lot number on carton
- Any mandatory test result is Failed without acceptable justification
- Any measurement out-of-tolerance value exceeds ±1/8"

**Scope:** `FULL REPORT` — cross-check overall result against all section results and defect counts
**Error example:** Report shows overall PASS despite a brand logo variation vs. approval sample (CRITICAL) and Major defects exceeding the AQL acceptance number
**Correct example:** Report shows overall FAIL because 1 Critical defect (brand logo variation) was found, even though all other sections passed
**Severity:** `BLOCKING`


```check
data_source: in_report
where: [product._first.real_packed_quantity, product._first.ordered_quantity]
when: report.overall_result equals PASS
check: ratio_at_least(0.8)
```

---

## Excluded fields (review recommended)

The following elements were found in the source files but excluded from the error list above. Please confirm each exclusion is correct.

- **QIMA inspection ID and reference number (e.g., PSI 1399166):** Auto-generated system field; no reviewer verification possible.
- **Inspection date / Planned date:** Auto-populated timestamp fields; no reviewer verification possible.
- **Inspector name and profile photo (Catherine Catipay):** System-populated identification field; no reviewer action possible.
- **Entity responsible / Production site fields:** Auto-populated from booking data; no reviewer action possible.
- **Inspection coordinates (start/complete/site):** GPS fields auto-recorded by the app; no reviewer action possible.
- **Overall result (Pass/Fail banner):** Calculated automatically from section results by QIMAone; flagged only when it contradicts section-level results (covered under rule 8.1.1).
- **Section results (Pass/Fail per checklist):** Calculated automatically from checkpoint results; flagged only when they contradict checkpoint-level evidence (covered per section rules).
- **Defective rate percentage and total defects found:** Auto-summed from inspector-entered counts; flagged only when the stated total contradicts the individual defect entries.
- **Acceptance point values:** Auto-determined by QIMAone from the AQL table; flagged only if the AQL inputs themselves are wrong (covered under rule 7.1.1).
- **"Generated on QIMAone" footer and page numbers:** Fixed system watermark; no reviewer action possible.
- **Acknowledgments & signatures timestamps:** Auto-recorded system timestamps for electronic signatures; no reviewer action possible.
- **Legal disclaimer text:** Fixed legal boilerplate identical across all reports; no reviewer action possible.
- **Measurement Guidelines POM diagrams (V1.0 July 2019):** Reference illustrations for how to take each measurement; inspector training aids, not report review checkpoints.

---

## Ambiguous or Incomplete Rules

> The following rules were found in the source files but were unclear, contradictory, or missing key information. They have been written as full rule entries above with a `⚠️ TO CONFIRM` severity flag. The items below are rules where not even a partial rule entry was possible.

- **Approval sample — end-of-inspection handling:** The GI states "at the end of inspection, repack or do something" but does not specify the required action. Confirm the correct end-of-inspection procedure for the approval sample with Joseph Ribkoff.
- **Shading check — color reference scope:** The GI states photos with the approval sample are required for shading checks "unless otherwise specified, not for color reference." It is unclear when the exception applies. Confirm with the client.
- **General pictures — exhaustive prohibition list:** The Golden Report commentary prohibits "general pictures" (factory exterior, inspector standing) but does not enumerate all prohibited photo types. Confirm the complete list with the client.

---

## Do not flag — client-specific notes

The following situations were identified in the Golden Report and confirmed as correct per the GIs provided:

- **Approval sample without client signature:** The GI states the approval sample must be identified with a green "QIMA SAMPLE" tag, not a client signature. The inspector's remark noting "approval sample provided by factory without any client's signatures" is a valid observation but does not by itself constitute a report error — provided the green QIMA tag is present.
- **Produced quantity exceeding booking by 3.2% (516 vs. 500 pcs):** The GI requires any overage to be remarked upon, not refused. Inspector correctly noted "516 pcs / 103%" in the Inspector's Remark section. Do not flag this as a fail condition provided the remark is present.
- **Tools calibration answered "No" with explanation:** The GI does not require calibrated tools to be a pass/fail condition — only that the answer and an explanation are provided. Inspector noted "no calibration label on the weight scale provided by factory." This is correctly handled as a remark, not a section failure.
- **Care label language sequence variation vs. approval sample:** Per GI rule 3.2.6, misprinting or variation in the sequence of languages on care content labels is explicitly not a reason to fail the report.
- **Outer Packing marked N/A with comment "No spec for comparison":** The GI does not require a specific outer packing specification to exist; if no spec is available, N/A with a comment is acceptable.
- **All measurements out of spec by ±1/8" only:** Per GI rule 5.1.2, if all out-of-tolerance values are within ±1/8", the measurement section must be marked PASS with a remark. Do not flag this as a fail.
