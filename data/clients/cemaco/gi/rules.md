# Cemaco Inspection Report Review – Rules Reference

> Sources: Cemaco GI text (client requirements); Annotated Golden Report example images (C1–C7); Cemaco claims e-mail — "Improve in future inspection - textile" (claim ref: R-Cloud-2321196); Cemaco measurements template (reference only); Sample PSI report Q2529052878_1 / PSI 1994067, 15-Jun-2026 (used for report structure and field-location reference only)
> Last compiled: July 2026

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

### 1.1 Pre-inspection document check

---

**ID:** 1.1.1
**Field / Location:** Inspection product list (client-uploaded files)
**What to check:** Verify that all client-uploaded inspection files (artwork, specifications, etc.) have been reviewed before starting the inspection. If the supplier offers any conversation record relevant to the inspection, a dated screenshot must be included in the report.
**Scope:** `QUESTION` — check only that the uploaded files were reviewed and any supplier conversation record is captured
**Error example:** Inspector starts the inspection without reviewing the uploaded artwork and later misses a color specification requirement.
**Correct example:** Inspector reviews all uploaded files beforehand and attaches a dated screenshot of the supplier's message confirming a specification point.


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

**ID:** 1.1.2
**Field / Location:** Specification sheets
**What to check:** Confirm the report references the client's product specification (artwork, color, label, barcode, shipping mark) for each SKU inspected.
**Scope:** `SECTION` — cross-check that each SKU's findings reference the corresponding specification sheet
**Error example:** Report has no reference to the client's artwork/specification for the SKU inspected.
**Correct example:** Report states which specification sheet was used for each SKU inspected.


```check
where:
  - kind: checklist
    match: [specification]
    field: comment
when: null
check: null
```

---

### 1.2 Report front page — mandatory information

---

**ID:** 1.2.1
**Field / Location:** Report front page — inspection date fields
**What to check:** The number of days the inspection was postponed or advanced versus the originally planned date must always be stated. "N/A" is not accepted, even for a missing report.
**Scope:** `QUESTION`
**Error example:** Front page field left as "N/A" although the inspection was performed 3 days after the planned date.
**Correct example:** Front page states "Inspection performed 3 days after the planned date of [date]."


```check
where: [report.days_postponed]
when: null
check: present
```

---

**ID:** 1.2.2
**Field / Location:** Report front page — Factory / Vendor details
**What to check:** Factory name, address, and site representative must be recorded in English, even if the factory only confirmed them in Chinese. Vendor details must also be completed.
**Scope:** `QUESTION`
**Error example:** Factory address recorded only in Chinese characters.
**Correct example:** Factory address recorded in English (Chinese characters removed/translated), e.g. "Yedi Eylül Mah. Ümit Tunçağ Cad. No:3, Torbalı/İzmir, Turkey."


```check
where: [report.factory_address]
when: null
check:
  - present
  - no_language(chinese)
```

---

**ID:** 1.2.3
**Field / Location:** Report — production line photo
**What to check:** A picture of the factory's production line must be included in the report.
**Scope:** `QUESTION`
**Error example:** Report contains no photo of the production line.
**Correct example:** Report includes at least one dated photo of the production line in operation.


```check
where:
  - kind: checklist
    match: [production, line]
    field: photo_count
when: null
check: count_at_least(1)
```

---

**ID:** 1.2.4
**Field / Location:** Final PDF file
**What to check:** The PDF report sent to the client must be under 15MB. If it exceeds this, pictures must be compressed and the PDF regenerated; if still over 15MB, the QIMA quality team must be notified.
**Scope:** `FULL REPORT` — check final file size against all embedded images
**Error example:** A 22MB PDF is sent to the client without any compression.
**Correct example:** Pictures are compressed, the PDF is regenerated at 12MB, and then sent to the client.


```check
where: [report.attachment_filenames]
when: null
check: null
```

---

### 1.3 Production status / site conditions

---

**ID:** 1.3.1
**Field / Location:** Inspection site / availability remark
**What to check:** If goods belonging to the supplier are at another location no more than a 5–15 minute walk away, the inspection may proceed; the location must be reflected in the report and the back office notified. For new suppliers in China, the inspection address must be reconfirmed by e-mail beforehand.
**Scope:** `SECTION`
**Error example:** Inspector proceeds at a second site 20 minutes away without notifying the back office or reflecting the location in the report.
**Correct example:** Inspector confirms the second site is a 10-minute walk, notifies the back office, and records the site address in the report.


```check
where: [out_of_report:sop]
when: null
check: null
```

---

**ID:** 1.3.2
**Field / Location:** Available Quantity Check
**What to check:** If products are not ready for inspection, the inspector must check available/semi-finished product, request packing material from the factory if available, and mark the inspection FAILED. If nothing is available at all, a MISSED REPORT must be issued instead.
**Scope:** `FULL REPORT` — cross-check quantity available on-site against the pass/fail/missed decision
**Error example:** No product is available on-site, yet the inspector marks the inspection "Pass" with a remark "product not ready."
**Correct example:** No product available on-site → inspector issues a MISSED REPORT.


```check
where:
  - kind: checklist
    match: [available, quantity, details]
    field: comment
when: null
check: null
```

---

**ID:** 1.3.3
**Field / Location:** Inspection coordination note
**What to check:** If the inspection takes place in a warehouse that does not belong to the factory or the supplier, the inspector must contact the QIMA quality team before proceeding.
**Scope:** `QUESTION`
**Error example:** Inspection proceeds in a third-party logistics warehouse with no contact made to the quality team.
**Correct example:** Inspector identifies that the warehouse doesn't belong to the factory/supplier, contacts the quality team, and documents the confirmation before proceeding.


```check
where: [out_of_report:sop]
when: null
check: null
```

---

**ID:** 1.3.4
**Field / Location:** Inspection start time / remark
**What to check:** If goods are not ready when the inspector arrives, the inspector must wait until at least part of the goods are available, notify the back office and SIC, and wait until 2:00 PM local time before issuing a missing inspection report if goods remain unavailable.
**Scope:** `QUESTION`
**Error example:** Inspector leaves at 11:00 AM and issues a missing report without waiting until 2:00 PM or notifying SIC.
**Correct example:** Inspector waits until 2:00 PM, keeps SIC/back office informed throughout, and only then issues the missing report.


```check
where: [out_of_report:sop]
when: null
check: null
```

---

### 1.4 Carton & product selection

---

**ID:** 1.4.1
**Field / Location:** Random carton selection / Selected cartons
**What to check:** Carton and product selection must follow QIMA's Standard Operating Process (SOP) for random sampling.
**Scope:** `SECTION`
> ⚠️ TO CONFIRM: The GI text only states "See QIMA's SOP" / "Follow QIMA Standard procedure" without specifying concrete sampling steps for Cemaco; confirm whether Cemaco requires anything beyond the generic QIMA SOP.
**Error example:** Cartons are selected by the factory rather than randomly by the inspector.
**Correct example:** Inspector personally selects cartons at random from multiple pallet locations, documented with before/after photos.


```check
where: [out_of_report:sop]
when: null
check: null
```

---

## Section 2 – Documents Recorded in the Report

### 2.1 Approval sample

---

**ID:** 2.1.1
**Field / Location:** Approval Sample Comparison
**What to check:** When no approval sample is provided by the factory (standard for Cemaco), the inspector must verify that all on-site findings (product, plug type, packaging) are fully aligned with the specification file, with no assumptions or interpretation.
**Scope:** `FULL REPORT` — cross-check product/plug/packaging findings against the booking specification file
**Error example:** No approval sample on-site; inspector writes "Checked and found the same as expected" for a plug type that does not actually match the booking spec's UL requirement.
**Correct example:** No approval sample on-site; inspector compares plug type, markings, and packaging directly against the booking specification file, and reports any deviation found.


```check
where:
  - kind: checklist
    match: [approval, sample, comparison]
    field: comment
when: null
check: null
```

---

### 2.2 Hangtag / label / barcode verification

---

**ID:** 2.2.1
**Field / Location:** Product Style & Construction — hangtag
**What to check:** The hangtag physically attached to each product must match that exact product's SKU, description, and specification exactly — hangtags must never be mixed between products or SKUs.
**Scope:** `FULL REPORT` — cross-check hangtag content against product SKU and specification file
**Error example:** A chair is found wearing the hangtag intended for a different chair model/color; the report result still shows PASS.
**Correct example:** The hangtag text matches the product's SKU and specification exactly; any mismatch is reported as a defect and the checkpoint result is FAIL.


```check
where:
  - kind: checklist
    match: [product, style, construction]
    field: comment
when: null
check: null
```

---

**ID:** 2.2.2
**Field / Location:** Product Style & Construction — barcode
**What to check:** The barcode printed on the product must be verified against both the hangtag barcode and the packing list/file; any discrepancy between the three must be reported.
**Scope:** `FULL REPORT` — cross-check barcode on product, hangtag, and packing file
**Error example:** The barcode on the product's hangtag differs from the barcode listed in the packing file, and the mismatch is not reported.
**Correct example:** Barcode on product, hangtag, and packing file are compared side by side; any mismatch, even a single digit, is flagged and reported.


```check
where:
  - kind: checklist
    match: [product, style, construction]
    field: comment
when: null
check: null
```

---

**ID:** 2.2.3
**Field / Location:** Product Labels / Product Details – Barcode
**What to check:** Barcode scanning result must be recorded for each SKU, with a photo of both the barcode label and the scan result.
**Scope:** `SECTION`
**Error example:** Report states "Barcodes are scannable" with no scan-result photo or per-SKU detail.
**Correct example:** Report includes, for each SKU, a photo of the barcode label plus a photo/screenshot of a successful scan result.


```check
where:
  - kind: checklist
    match: [barcode]
    field: photo_count
when: null
check: count_at_least(2)
```

---

### 2.3 Report photo organization

---

**ID:** 2.3.1
**Field / Location:** Photo captions / TAG feature (QIMAone)
**What to check:** Photos must be organized and captioned by SKU using the TAG feature in QIMAone; photo captions must always reflect the correct SKU.
**Scope:** `SECTION`
**Error example:** Photos for two different SKUs are mixed under a single generic caption with no SKU reference.
**Correct example:** Each photo is tagged with its SKU number using the QIMAone TAG feature.


```check
where: [report.all_captions]
when: null
check: present
```

---

## Section 3 – Packaging

### 3.1 Outer packing & shipping marks

---

**ID:** 3.1.1
**Field / Location:** Outer Packing & Shipping Marks: Front & Side — carton quantity marking
**What to check:** The quantity marked on the outer carton must match the quantity specified in the client's order file for that SKU exactly.
**Scope:** `FULL REPORT` — cross-check carton marking against order file quantity
**Error example:** Carton for a given SKU is marked "400" while the order file specifies 136; the inspector's remark states "if no mention, we consider there is no problem" and does not report the discrepancy.
**Correct example:** Carton marking matches the order file quantity exactly for the SKU inspected; any different marking is reported as a discrepancy regardless of whether the client commented on it.


```check
where:
  - kind: checklist
    match: [outer, packing, shipping, marks, front, side]
    field: comment
when: null
check: null
```

---

**ID:** 3.1.2
**Field / Location:** Outer Packing & Shipping Marks — plug type / certification (E&E products)
**What to check:** Plug type and certification markings on the product/adaptor must match the certification required in the booking specification (e.g., UL vs. EU plug).
**Scope:** `FULL REPORT` — cross-check plug type/certification against booking specification
**Error example:** A product is fitted with a 2-pin EU-type plug while the booking specification requires a UL-certified plug; the issue is not mentioned and the report shows PASS.
**Correct example:** Plug fitted matches the UL certification and pin type required by the booking specification; the certification marking is photographed and confirmed.


```check
where: [out_of_report:booking]
when: null
check: null
```

---

**ID:** 3.1.3
**Field / Location:** Outer Packing & Shipping Marks — market-specific labels
**What to check:** Labels not required for the client's destination market (e.g., a yellow ENERGYGUIDE sticker for a market that doesn't require it) must not be present on the product/packaging; if found, it must be reported as a deviation from the approved artwork.
**Scope:** `FULL REPORT` — cross-check labels present against market requirements in the booking specification
**Error example:** A yellow ENERGYGUIDE sticker is visibly present on units for a market that does not require it; not reported by the inspector.
**Correct example:** No ENERGYGUIDE sticker is present, consistent with the market requirement; if present, it is reported as a deviation.


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

**ID:** 3.1.4
**Field / Location:** Outer Packing & Shipping Marks — printed component/feature count
**What to check:** Any printed specification on the product packaging (e.g., LED light count, piece count) must match the booking specification exactly.
**Scope:** `FULL REPORT` — cross-check printed packaging text against booking specification
**Error example:** Packaging states "6 PCS LED LIGHT" while the booking specification requires "10PCS LED LIGHT"; the discrepancy is not mentioned in the report.
**Correct example:** Packaging states "10PCS LED LIGHT," matching the booking specification; any different count is reported.


```check
where: [out_of_report:booking]
when: null
check: null
```

---

### 3.2 Inner packing & unit packing

---

**ID:** 3.2.1
**Field / Location:** Inner Packing & Unit Packing — warning sticker
**What to check:** Warning/advisory stickers on inner or unit packaging must be firmly adhered with no lifting edges, positioned as specified in the packing manual, and match the required dimensions.
**Scope:** `SECTION`
**Error example:** Warning sticker on inner packaging is loose with visibly lifted edges; not reported.
**Correct example:** Warning sticker is firmly adhered with no lifting edges, positioned per the packing manual, at the specified dimensions.


```check
where:
  - kind: checklist
    match: [inner, packing, unit, packing]
    field: comment
when: null
check: null
```

---

### 3.3 Color boxes / insert cards

---

**ID:** 3.3.1
**Field / Location:** Product Color Specification Check / insert card
**What to check:** The color of any insert card, color box, or gift box must be compared against the Pantone reference stated in the client's artwork, with a photo of the comparison. If TCX/TPG Pantone references are unavailable, use the STD Pantone.
**Scope:** `FULL REPORT` — cross-check insert card/color box color against the artwork's Pantone reference
**Error example:** The factory produces the insert card in at least 3 different background color shades; none is compared against the Pantone number stated in the artwork.
**Correct example:** The insert card color is compared against the Pantone reference stated in the artwork, with a comparison photo; any color variation found is reported.


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

**ID:** 3.3.2
**Field / Location:** Color boxes — photography
**What to check:** For color/gift boxes, one picture must be taken per surface (e.g., 6 pictures for a 6-sided box); the client's artwork should be enlarged for detailed comparison.
**Scope:** `QUESTION`
**Error example:** Only 2 of 6 surfaces of a color box are photographed.
**Correct example:** All 6 surfaces of the color box are individually photographed and compared against the enlarged artwork.


```check
where:
  - kind: checklist
    match: [color, box]
    field: photo_count
when: null
check: null
```

---

## Section 4 – Workmanship

### 4.1 Defect recording

---

**ID:** 4.1.1
**Field / Location:** Defects checklist
**What to check:** Every defect must be recorded by SKU, with a supporting photo for each defect found; factory and vendor information must be completed.
**Scope:** `SECTION`
**Error example:** A major defect is recorded without a corresponding photo or SKU reference.
**Correct example:** Each defect entry includes the SKU, a description, a classification (critical/major/minor), and a supporting photo.


```check
where: [report.defects_without_photo]
when: null
check: equals(0)
```

---

### 4.2 Color shade consistency

---

**ID:** 4.2.1
**Field / Location:** Product Color Specification Check
**What to check:** Color shade must be checked and compared across all inspected items/colors selected for the inspection — not only one representative color per SKU or series.
**Scope:** `FULL REPORT` — cross-check color consistency across all units/colors of the same item inspected
**Error example:** An item is inspected in 2 colors, but the color-shade test is only performed and reported for one color; the other color later shows a wide shade variation (e.g., from white to green-blue) once on the shelf, undetected by the report.
**Correct example:** Color shade is tested and reported for every color of the item selected for inspection, so shade variation within the same color is caught before shipment.


```check
where:
  - kind: checklist
    match: [product, color, specification, check]
    field: comment
when: null
check: null
```

---

### 4.3 Material-specific checks

---

**ID:** 4.3.1
**Field / Location:** Workmanship — metal items
**What to check:** For all-metal items, moisture level must be checked to assess the potential for rust or mildew; screws (if assembled) or loose parts/components (if not assembled) must be checked for rust.
**Scope:** `QUESTION`
**Error example:** Rusted screws found on a metal product frame are not mentioned in the report.
**Correct example:** Moisture level is measured and recorded, and screws/parts are confirmed free of rust, with supporting photos.


```check
where:
  - kind: checklist
    match: [workmanship]
    field: comment
when: null
check: null
```

---

### 4.4 General dimension / weight check

---

**ID:** 4.4.1
**Field / Location:** Product Dimensions Result / Product Weights Result
**What to check:** When the client provides no specific dimension specification, the general dimension and weight of the product must still be checked, on 5 pieces per item.
**Scope:** `QUESTION`
**Error example:** No dimension check is performed because "there is no client specification," and the checkpoint is left blank.
**Correct example:** General dimensions and weight are measured and recorded on 5 pieces per item even without a client specification.


```check
where:
  - kind: checklist
    match: [product, dimensions, result]
    field: comment
when: null
check: null
```

---

## Section 5 – Tests and Measurements

### 5.1 Sampling method

---

**ID:** 5.1.1
**Field / Location:** Inspection standards — Workmanship / Measurement sampling
**What to check:** Workmanship and measurement sampling must follow the Inspection Profile (IP) defined for the order; no separate Cemaco-specific AQL table exists beyond the IP.
**Scope:** `FULL REPORT` — cross-check sample size/AQL applied in the report against the IP
**Error example:** Report applies a General Level II sampling plan when the IP specifies General Level III.
**Correct example:** Report applies the sampling level and AQL exactly as defined in the IP for the order.


```check
where: [out_of_report:ip]
when: null
check: null
```

---

### 5.2 Product measurements / POM reference

---

**ID:** 5.2.1
**Field / Location:** Product Dimensions Result — measurement chart
**What to check:** All measurements taken during inspection must be recorded in the client's official measurement chart ([Cemaco Nuevos Almacenes] [Measurements Template]).
**Scope:** `SECTION`
**Error example:** Measurements are recorded only as photos of a tape measure with no corresponding entry in the client's measurement template.
**Correct example:** Every measurement taken is entered into the Cemaco measurement template (by item/sample) and attached to the report.


```check
where:
  - kind: checklist
    match: [product, dimensions, result]
    field: attachment_filenames
when: null
check: present
```

---

### 5.3 Specific test requirements

---

**ID:** 5.3.1
**Field / Location:** Tests checklist — memory foam pillow
**What to check:** For memory foam pillow products, both the filling and the assembled pillow must be weighed separately.
**Scope:** `QUESTION`
**Error example:** Only the assembled pillow weight is recorded; the filling weight is missing.
**Correct example:** Both the filling weight and the total pillow weight are recorded and reported separately.


```check
where:
  - kind: checklist
    match: [memory, foam, pillow]
    field: comment
when: null
check: null
```

---

**ID:** 5.3.2
**Field / Location:** Tests checklist — Container Load Check (CLC)
**What to check:** For CLC inspections, no product quality checks are required; the inspector should instead focus on the container's condition and confirm pallets are loaded horizontally.
**Scope:** `QUESTION`
**Error example:** Inspector spends time re-checking product workmanship during a CLC instead of focusing on container/loading condition.
**Correct example:** Inspector focuses on container condition and confirms horizontal pallet loading, contacting SIC with any loading questions.


```check
where:
  - kind: checklist
    match: [container, load, check]
    field: comment
when: null
check: null
```

---

**ID:** 5.3.3
**Field / Location:** Tests checklist — Metal Detection Test
**What to check:** The Metal Detection Test is mandatory for all tablecloth and cushion product inspections.
**Scope:** `QUESTION`
**Error example:** A cushion inspection report has no metal detection test result.
**Correct example:** Metal detection test is performed and its result (pass/fail) is recorded for the cushion inspection.


```check
where:
  - kind: checklist
    match: [metal, detection, test]
    field: result
when: null
check: present
```

---

## Section 6 – Report Photos

### 6.1 SKU photo requirements

---

**ID:** 6.1.1
**Field / Location:** Product Style & Construction (main page)
**What to check:** One product photo per SKU is required; if an SKU has multiple colors, a separate photo is required for each color, with all SKUs combined into a single photo on the first page of the report.
**Scope:** `SECTION`
**Error example:** A report covering 20 SKUs shows only 5 SKUs combined in the main photo; the rest are missing.
**Correct example:** All 20 SKUs inspected appear together in a single photo on the first page, plus one dedicated photo per SKU/color further in the report.


```check
where:
  - kind: checklist
    match: [product, style, construction]
    field: photo_count
when: null
check: count_at_least(1)
```

---

**ID:** 6.1.2
**Field / Location:** General photo requirement
**What to check:** The front view of the product must always be included and placed on the main page for each SKU.
**Scope:** `QUESTION`
**Error example:** Only a side/angled view of the product is shown on the main page.
**Correct example:** A clear front view of the product is shown on the main page.


```check
where:
  - kind: checklist
    match: [product, style, construction]
    field: photo_count
when: null
check: count_at_least(1)
```

---

### 6.2 Supporting photos per checkpoint

---

**ID:** 6.2.1
**Field / Location:** General cosmetics — measurement/carton/packing photos
**What to check:** Each SKU section must include: product measurement photos, carton box size/weight photos (with a carton photo even when no SKU marking appears on the carton), packing photos, and shipping mark photos.
**Scope:** `SECTION`
**Error example:** Carton weight is stated in text but no photo of the scale reading is included.
**Correct example:** Each measurement (dimension, weight) has a corresponding photo (e.g., tape measure or scale reading) alongside the text result.


```check
where:
  - kind: section
    match: [product, packing, packaging]
    field: photo_count
when: null
check: null
```

---

## Section 7 – AQL / AOQL Summary

---

**ID:** 7.1.1
**Field / Location:** Inspection type / sampling level field (report header)
**What to check:** Verify the sampling level and AQL used in the report match the Inspection Profile (IP) defined for the order.

| Channel | Standard | Critical | Major | Minor | Total |
|---|---|---|---|---|---|
| All channels | Follow IP (no Cemaco-specific channel/AQL table provided) | Per IP | Per IP | Per IP | Per IP |

**Scope:** `FULL REPORT` — cross-check applied AQL/sample size against the order's IP
> ⚠️ TO CONFIRM: The GI text only states "Follow IP" for both Workmanship and Measurement; no channel-specific AQL/AOQL table (by market/destination) was provided for Cemaco. Confirm with the client whether channel-specific AQL tables exist.
**Error example:** Report uses AQL 4.0/2.5/0 for Minor/Major/Critical without confirming this matches the order's IP.
**Correct example:** Report's AQL and sample size are confirmed to match the IP configured for that specific order.


```check
where: [out_of_report:ip]
when: null
check: null
```

---

## Section 8 – Pass / Fail Decision Logic

---

**ID:** 8.1.1
**Field / Location:** Overall result (report header)
**What to check:** Overall result must be PASS only if ALL conditions below are met. If any single condition fails, overall result must be FAIL.

**PASS requires ALL of:**
- Critical/major/minor defect counts are within the AQL acceptance point.
- All on-site findings (product, plug type, packaging, labels, printed specs, hangtags, barcodes) are fully aligned with the specification file, with no unresolved deviation.
- All mandatory documents, photos, and measurements are present in the report.

**FAIL triggered by ANY of:**
- Critical/major/minor defect count exceeds the AQL acceptance point.
- A plug type, label, printed spec, hangtag, or barcode mismatch versus the specification file is found, even if defect sampling otherwise passes.
- Carton marking/quantity does not match the order file.

**Scope:** `FULL REPORT` — cross-check overall result against all checkpoint findings in the report
**Error example:** A wrong (non-UL) plug type is found on-site for an SKU, yet the report's overall result and first-page summary show "Pass" with no mention of the issue.
**Correct example:** The plug mismatch is reported on the relevant checkpoint AND reflected in the overall result as FAIL, clearly visible on the report's first page.


```check
where: [report.overall_result]
when: null
check: in_set(PASS, FAIL, PENDING)
```

---

## Ambiguous or Incomplete Rules

> This section lists rules found in the source files that were unclear, contradictory, or missing key information. Review and resolve before using this document operationally.

- **Carton & Product selection (1.4.1):** The GI text only refers to "QIMA SOP" / "QIMA Standard procedure" without describing the specific steps; the concrete sampling procedure itself was not included in the source material provided.
- **AQL/AOQL channel table (7.1.1):** No client-specific AQL/AOQL breakdown by market/channel was provided; only "Follow IP" is stated in the source material.
