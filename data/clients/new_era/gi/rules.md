# New Era Cap Inspection Report Review – Rules Reference

> Sources: New Era Cap LLC – Golden Report (annotated, Jul-2025); Quality Assurance Manual –
> Revision 9.1; New Era Cap LLC_Measurement Defect AQL Table_29 Sep 2025.xls; New Era –
> Inspection Training for 3rd Party – 27-Feb-2025; NEC Defect Classification List – Apparel;
> NEC Defect to pay attention_20260413.pptx; Cap & Visor Shape Defect Guide – Appendix 9
> (Headwear Manual, v1.1, 25-Jul-2025); client-provided rule summary.
> Last compiled: July 2026

---

## How to read this document

Each rule entry contains:
- **ID** — unique rule identifier (section.subsection.rule)
- **Field / Location** — where to look in the report
- **What to check** — the exact verification to perform
- **Scope** — `QUESTION` (check only that field), `SECTION` (cross-check within the same
  checklist section), `FULL REPORT` (cross-check across multiple sections or documents)
- **Error example** — a concrete example of what a wrong value looks like
- **Correct example** — a concrete example of what the correct value looks like

Where sources conflicted, the **Golden Report** (the real annotated report) was treated as
the most authoritative source, as it reflects what QIMAone actually requires in practice.

---

## Section 1 – General Report Setup

### 1.1 Production Status & Inspection Type Handling

---

**ID:** 1.1.1
**Field / Location:** Production status (Finished % / Packed %) — report header / PO & Product details
**What to check:** Verify the inspection was handled per the finished/packed thresholds: 100% finished & ≥80% packed → proceed as standard PSI; 60–80% packed → proceed but remark it as a DUPRO inspection and state packed qty/ratio; ≤59% packed → escalate to the quality team before proceeding.
**Scope:** `FULL REPORT` — cross-check the inspection type/remark against the actual packed quantity and the overall result
**Error example:** Goods are 65% packed but the report is submitted as a standard PSI with no DUPRO remark and no packed-quantity statement.
**Correct example:** Report remark states "This is a DUPRO inspection because goods are 65% finished," with packed quantity and ratio clearly stated.


```check
where: [report.global_remark]
when: null
check: null
```

---

**ID:** 1.1.2
**Field / Location:** Warehouse location note (if applicable)
**What to check:** If goods are split across two warehouses that are 3–4 km apart, this is acceptable and does not require escalation.
**Scope:** `QUESTION`
**Error example:** Report flags a "split warehouse" issue as a problem requiring client approval when the two sites are 3 km apart.
**Correct example:** Report proceeds normally, noting goods are split across two nearby warehouses.


```check
where: [report.global_remark]
when: null
check: null
```

---

### 1.2 Inspector's Remarks (First Page)

---

**ID:** 1.2.1
**Field / Location:** Inspector's remark — first page of the report
**What to check:** The remark must always state the finished quantity, packed quantity, and packed ratio, regardless of pass/fail result.
**Scope:** `QUESTION`
**Error example:** Inspector's remark field is empty or generic ("Inspection completed").
**Correct example:** "Goods were finished and packed 61,355 pcs into 1,521 cartons 90%."


```check
where: [report.global_remark]
when: null
check: extract_bool("Does this remark state the finished quantity, packed quantity, and packed ratio?")
```

---

**ID:** 1.2.2
**Field / Location:** Inspector's remark — re-inspection notice
**What to check:** If the inspection is a re-inspection, the inspector must add a remark referencing the original report number.
**Scope:** `QUESTION`
**Error example:** This is the second inspection of the same order (after a prior FAIL), but no remark references the earlier report.
**Correct example:** "This is re-inspections from R-Cloud-25083616."


```check
where: [report.global_remark]
when: null
check: extract_bool("Does this remark reference an original report number for a re-inspection?")
```

---

**ID:** 1.2.3
**Field / Location:** Inspector's remark — out-of-tolerance findings
**What to check:** Since the measurement/product-dimensions checkpoint is always recorded as N/A, any out-of-tolerance measurement finding must instead be flagged via a remark on the report's first page.
**Scope:** `FULL REPORT` — cross-check against the (always-N/A) measurement section and the Measurement Defect AQL Table attachment
**Error example:** A cap is found 0.4cm out of circumference tolerance, but this is only buried in the attached Excel file with no mention on the first page.
**Correct example:** First-page remark states: "Note: 1 pc out of tolerance on circumference (-0.4cm), refer to attached Measurement Defect AQL Table."


```check
where: [report.global_remark]
when: null
check: null
```

---

## Section 2 – Documents Recorded in the Report

### 2.1 Pre-Inspection Mandatory Documents

---

**ID:** 2.1.1
**Field / Location:** Supporting documents (PO, spec sheets, measurement sheets, packing list, factory address/contact)
**What to check:** Verify these documents were provided by the factory on-site. If any is missing, this must be remarked in the report.
**Scope:** `QUESTION`
**Error example:** No packing list was available on-site and the report does not mention it.
**Correct example:** Report remarks "Packing list not provided by factory on-site."


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

**ID:** 2.1.2
**Field / Location:** Advice List / Audit Plan
**What to check:** The AQL and sample size used in the report must match what is specified in the Advice List for that specific booking; check the item breakdown and quantity against the list.
**Scope:** `FULL REPORT` — cross-check against Section 8 (AQL / AOQL Summary)
**Error example:** Report uses the default 500-pcs sample size while the Advice List specifies 315 pcs for this booking.
**Correct example:** Report's sample size (315 pcs) matches the Advice List exactly.


```check
where: [out_of_report:booking]
when: null
check: null
```

---

### 2.2 Approval Sample

---

**ID:** 2.2.1
**Field / Location:** Tests checklist — Approval sample comparison
**What to check:** Verify the approval sample was available on-site and identified via signature/seal/comparison to the booking picture/special marking. If not available, the inspection must proceed with a remark added.
**Scope:** `QUESTION`
**Error example:** "Approval sample comparison" checkpoint is left blank with no photos.
**Correct example:** "Approval sample comparison — Passed — Check the dimensions, shape, style or color of the product against the approval sample — was checked" with supporting photos.


```check
where:
  - kind: checklist
    match: [approval, sample, comparison]
    field: photo_count
when: null
check: count_at_least(1)
```

---

## Section 3 – Sampling, PO/MI & Carton Selection

### 3.1 Carton Selection

---

**ID:** 3.1.1
**Field / Location:** Tests & checkpoints — Random Carton Selection
**What to check:** Cartons/sampling size must have been selected fully randomly per QIMA's standard process; the checkpoint result must read PASSED if random selection was possible.
**Scope:** `SECTION`
**Error example:** "Random carton selection" is marked Passed with no supporting detail on how cartons were chosen.
**Correct example:** "PASSED — Supplier offers 68,173 pcs were finished production and packed 61,355 pcs into 1,521 cartons 90%. Carton sample was randomly selected 42 Cartons randomly PO and cover."


```check
where:
  - kind: checklist
    match: [random, carton, selection]
    field: result
when: null
check: equals(PASSED)
```

---

### 3.2 PO / MI Selection

---

**ID:** 3.2.1
**Field / Location:** Material Item (MI) selection
**What to check:** A maximum of 20 MI must be checked per Material Description (MD); if workmanship sample size is 750 or 800 pcs, a minimum of 25 MI must be covered.
**Scope:** `SECTION`
**Error example:** Only 15 MI covered for a workmanship sample size of 800 pcs (25 MI required).
**Correct example:** 25 MI covered, matching the 800-pcs Recap Quotation requirement.


```check
where: [workmanship.sample_size_major]
when: null
check: null
```

---

**ID:** 3.2.2
**Field / Location:** PO selection
**What to check:** Regardless of the total number of POs, only the 8 POs with the largest quantity should be selected for regular inspections; if workmanship sample size is 750 or 800 pcs, a minimum of 14 POs must be selected.
**Scope:** `SECTION`
**Error example:** Only 6 POs selected for a workmanship sample size of 750 pcs (14 POs required).
**Correct example:** PO ref field lists 14+ distinct PO numbers, matching the 750-pcs Recap Quotation requirement.


```check
where: [report.po_reference]
when: null
check: null
```

---

**ID:** 3.2.3
**Field / Location:** Recap Quotation compliance (Workmanship SS ↔ MI / PO / Shape / MD)
**What to check:** Cross-check the selection against the Recap Quotation table:

| Workmanship SS | MI Selection | PO Selected | Shape Selection | MD |
|---|---|---|---|---|
| 200 | 20 MI | 8 PO | 3 shapes | 1 MD |
| 315 | 20 MI | 8 PO | 3 shapes | 1 MD |
| 500 | 20 MI | 8 PO | 3 shapes | 1 MD |
| 750 | 25 MI | 14 PO | 3 shapes | 2 MD |
| 800 | 25 MI | 14 PO | 3 shapes | 2 MD |

**Scope:** `FULL REPORT`
**Error example:** Workmanship sample size is 500 pcs, but the report covers 2 MD instead of 1.
**Correct example:** Workmanship sample size 500 pcs → 20 MI, 8 PO, 3 shapes, 1 MD — consistent with the table.


```check
where: [workmanship.sample_size_major]
when: null
check: null
```

---

**ID:** 3.2.4
**Field / Location:** PO selection — NFL program
**What to check:** If the Advice List identifies an "NFL" program, all 8 selected POs must come from the NFL PO list.
**Scope:** `SECTION`
**Error example:** Advice List flags NFL program, but only 3 of the 8 selected POs are NFL-related.
**Correct example:** All 8 selected POs are confirmed NFL POs.


```check
where: [out_of_report:booking]
when: null
check: null
```

---

**ID:** 3.2.5
**Field / Location:** Client-specified PO priority
**What to check:** If New Era Cap explicitly asks the factory to prioritize specific POs, the report must clearly remark that this instruction was followed.
**Scope:** `QUESTION`
**Error example:** Client requested specific POs but the report gives no indication these were followed or why other POs were selected.
**Correct example:** Report remarks "Selected POs per client instruction relayed by [contact]."


```check
where: [report.global_remark]
when: null
check: extract_bool("Does this remark state that specific POs were selected per client instruction?")
```

---

**ID:** 3.2.6
**Field / Location:** Garment color/artwork selection
**What to check:** When a garment item has more than 6 colors or artworks, the 6 colors/artworks selected must cover all product types.
**Scope:** `SECTION`
**Error example:** Item has 10 colorways but only 3 were inspected, all from the same silhouette.
**Correct example:** 6 colorways selected, covering every product type in the order.


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

## Section 4 – Packaging

### 4.1 Packaging & Shipping Marks

---

**ID:** 4.1.1
**Field / Location:** Material Item Number (MI) vs. carton sticker
**What to check:** The MI number recorded in the defect table must match the "Material" field on the carton box sticker. Note that the MI number is not the official product style number.
**Scope:** `SECTION`
**Error example:** Defect table lists MI 70968082 but the carton sticker's Material field shows a different number.
**Correct example:** MI 70968082 in the defect table matches the Material field on the carton label exactly.


```check
where: [report.defects]
when: null
check: null
```

---

### 4.2 Package-Induced Deformation

---

**ID:** 4.2.1
**Field / Location:** Inspector's remark — package deformation
**What to check:** If a workmanship defect is found, the inspector must write down any relevant issue regarding product deformation caused by the packaging (e.g. folding issue). This must not appear elsewhere in the report if no workmanship defect was found.
**Scope:** `QUESTION`
**Error example:** A "Folding Issue" photo/remark is included in a report showing 0 workmanship defects found.
**Correct example:** A report with workmanship defects found includes remark/photo: "Folding Issue" (ref. R-Cloud-25169067).


```check
where: [report.inspector_text]
when: report.defect_count equals 0
check: scan_absent("Folding Issue")
```

---

## Section 5 – Workmanship

### 5.1 Defect List & Classification

---

**ID:** 5.1.1
**Field / Location:** Defects checklist used
**What to check:** Cap items must be graded against the Quality Assurance Manual (Rev. 9.1) defect list; garment items must be graded against the NEC Defect Classification List – Apparel.
**Scope:** `SECTION`
**Error example:** A cap defect is graded using the apparel defect code list instead of the QA Manual.
**Correct example:** Cap defects (e.g. Exposed Haircloth, Broken Stitches) are graded per the QA Manual defect list.


```check
where: [report.defects]
when: null
check: null
```

---

**ID:** 5.1.2
**Field / Location:** Cap defect severity terminology
**What to check:** For cap products, only two defect levels exist — "Critical" and "Non-Critical" — not Major/Minor as used for garments.
**Scope:** `QUESTION`
**Error example:** Cap defect table uses "Major / Minor" column headers.
**Correct example:** Cap defect table uses "Critical | Non Critical" column headers.


```check
where: [report.defects]
when: null
check: extract_bool("Does this field use 'Critical' and 'Non Critical' as the defect severity labels, not 'Major' and 'Minor'?")
```

---

**ID:** 5.1.3
**Field / Location:** Circumference out-of-tolerance classification
**What to check:** Any out-of-tolerance circumference finding on a cap must be recorded as a CRITICAL defect in the AQL/defect table, not only noted as a measurement footnote.
**Scope:** `FULL REPORT` — cross-check against Section 6 (Tests and Measurements)
**Error example:** 5 of 60 caps are out of tolerance on circumference, but the defect table shows 0 Critical defects.
**Correct example:** 5 CRITICAL defects are added to the defect table, matching the 5 out-of-tolerance caps found.


```check
where: [out_of_report:ip]
when: null
check: null
```

---

**ID:** 5.1.4
**Field / Location:** Label centering (garment/headwear labels)
**What to check:** A label more than 2mm off-center (top to bottom) must be classified as a MAJOR defect, with clear defect photos attached.
**Scope:** `QUESTION`
**Error example:** Label is 3mm off-center but is not recorded as a defect.
**Correct example:** Label off-center by 3mm is recorded as a MAJOR defect with a close-up photo attached.


```check
where: [report.defects]
when: null
check: null
```

---

**ID:** 5.1.5
**Field / Location:** Recurring defect on 20+ pieces
**What to check:** If the same/similar defect is found on 20 or more pieces of bulk production, the back office/SIC must be informed to check with the client whether it should be added as a distinct AQL line item. If no feedback is received, the defect must still be kept in the AQL table as usual (not omitted).
**Scope:** `SECTION`
**Error example:** A defect found on 25 pieces is silently dropped from the AQL table pending client feedback.
**Correct example:** The defect remains in the AQL table with its full count while back office/SIC is consulted in parallel.


```check
where: [out_of_report:sop]
when: null
check: null
```

---

### 5.2 Defect Breakdown Cross-Check

---

**ID:** 5.2.1
**Field / Location:** Workmanship section vs. Measurement Defect AQL Table attachment
**What to check:** The total Critical/Major/Minor (or Critical/Non-Critical) defect counts shown under "Workmanship" in the report body must exactly equal the totals shown in the attached Measurement Defect AQL Table Excel file.
**Scope:** `FULL REPORT`
**Error example:** Workmanship section shows 10 Major / 0 Minor defects found, but the attached Excel file totals 14 Major / 21 Minor.
**Correct example:** Workmanship section shows 10 Major / 0 Minor; attached Excel file totals 10 Major / 0 Minor — counts match exactly.


```check
where: [report.defect_count]
when: null
check: null
```

---

**ID:** 5.2.2
**Field / Location:** Excel defect breakdown — PO/MI/silhouette detail
**What to check:** The Excel defect breakdown must always include the PO number inspected, units inspected per PO, the cap silhouette (e.g. 920, 940, 5950), and the MI style number for every row.
**Scope:** `SECTION`
**Error example:** A row lists only "Cap, 20 pcs" with no PO number, silhouette, or MI number.
**Correct example:** "PO#4500469738, Cap, 20 pcs" with MI style number (e.g. 12274362) populated in its own column.


```check
where: [report.attachment_filenames]
when: null
check: null
```

---

## Section 6 – Tests and Measurements

### 6.1 Always-N/A Results

---

**ID:** 6.1.1
**Field / Location:** Weight Check (full garment)
**What to check:** Result must always be recorded as N/A.
**Scope:** `QUESTION`
**Error example:** Weight Check result is marked "Pass" with a recorded weight value.
**Correct example:** "Weight Check — 3 Pieces — N/A — no specification."


```check
where:
  - kind: checklist
    match: [weight, check]
    field: result
when: null
check: equals(NOT_APPLICABLE)
```

---

**ID:** 6.1.2
**Field / Location:** Fabric Weight Test (GSM)
**What to check:** Result must always be recorded as N/A.
**Scope:** `QUESTION`
**Error example:** GSM value entered and result marked "Pass."
**Correct example:** "Fabric Weight Test — 3 Pieces — N/A — no specification."


```check
where: [checklist.fabric_weight_test_gsm.result]
when: null
check: equals(NOT_APPLICABLE)
```

---

**ID:** 6.1.3
**Field / Location:** Product Dimensions / Measurement checklist (cap and garment)
**What to check:** The measurement checkpoint itself must always be recorded as N/A; any out-of-tolerance finding is instead flagged only via the first-page remark and the Measurement Defect AQL Table.
**Scope:** `FULL REPORT` — cross-check against Section 1 (Inspector's Remarks) and Section 5 (Workmanship)
**Error example:** Measurement checklist result is marked "Fail" directly on that checkpoint.
**Correct example:** "Product Dimensions Result — N/A — was checked," with any out-of-tolerance handled per Section 1.2.3 and Section 5.1.3.


```check
where:
  - kind: checklist
    match: [product, dimensions, result]
    field: result
when: null
check: equals(NOT_APPLICABLE)
```

---

### 6.2 Cap-Specific Measurement Rules

---

**ID:** 6.2.1
**Field / Location:** 59FIFTY circumference tolerance
**What to check:** For all 59FIFTY cap styles only, the circumference special tolerance is +/-0.3cm; crown should be squared off (flat), not rounded.
**Scope:** `QUESTION`
**Error example:** A 59FIFTY cap is graded using the general +/-0.5cm circumference tolerance.
**Correct example:** A 59FIFTY cap is graded against the special +/-0.3cm tolerance.


```check
where: [out_of_report:spec_sheet]
when: null
check: null
```

---

**ID:** 6.2.2
**Field / Location:** Measurement Defect AQL Table — header fields
**What to check:** The inspector must use the New Era Cap LLC_Measurement Defect AQL Table template and populate all required header fields: QIMA order ref., cap shape (if applicable), Material Item # (MI), PO, and sample size (measurement).
**Scope:** `SECTION`
**Error example:** Header fields for QIMA order ref. and PO are left blank.
**Correct example:** All 5 required header fields are populated with the correct booking information.


```check
where: [report.attachment_filenames]
when: null
check: null
```

---

**ID:** 6.2.3
**Field / Location:** Cap measurement sample size
**What to check:** Cap measurement sampling is always 60 pcs total per man-day, generally described as covering 3 cap shapes at 20 pcs each.
> ⚠️ TO CONFIRM: real reports show the 60-pc total sometimes spread across more than 3 style/MI combinations rather than exactly 3 shapes × 20 pcs. Treat the 60-pc total as fixed; the "3 shapes only" split may not be a hard rule.
**Scope:** `SECTION`
**Error example:** Only 30 pcs measured across 2 shapes for a cap workmanship inspection.
**Correct example:** 60 pcs measured, covering the styles/MI present in the selected POs.


```check
where: [workmanship.measurement_level]
when: null
check: null
```

---

**ID:** 6.2.4
**Field / Location:** Garment measurement out-of-tolerance comment
**What to check:** When a garment measurement is out of tolerance, the result must be N/A with the comment "Subject to Client's Evaluation."
**Scope:** `QUESTION`
**Error example:** Out-of-tolerance garment measurement is left without any comment.
**Correct example:** Result = N/A, Comment = "Subject to Client's Evaluation."


```check
where:
  - kind: checklist
    match: [garment, measurement]
    field: comment
when: null
check:
  - extract("Quote the comment text for this out-of-tolerance measurement, or null")
  - contains("Subject to Client's Evaluation")
```

---

### 6.3 Cap Moisture Test

---

**ID:** 6.3.1
**Field / Location:** Moisture Test for Cap
**What to check:** Test must be performed on a fixed 12 pcs (3 pcs × 4 MI styles, covering at least 3 cap styles, e.g. 5950/940/920); results must be updated in the Measurement Defect AQL Table and attached. For knitted/fully-fashioned headwear, only the centre and hem/fold positions need to be checked and recorded.
**Scope:** `SECTION`
**Error example:** Moisture test performed on only 2 MI styles.
**Correct example:** Moisture test performed on 4 MI styles covering 3+ cap styles, with results recorded in the attached Excel table.


```check
where: [report.attachment_filenames]
when: null
check: null
```

---

### 6.4 Other Tests

---

**ID:** 6.4.1
**Field / Location:** Carton Drop Test
**What to check:** Must NOT be performed for New Era Cap inspections.
**Scope:** `QUESTION`
**Error example:** Report includes a completed Carton Drop Test checklist.
**Correct example:** Carton Drop Test checkpoint is absent/not applicable.


```check
where: [report.all_text]
when: null
check: scan_absent("Carton Drop Test")
```

---

**ID:** 6.4.2
**Field / Location:** Wet & Dry Rub Test
**What to check:** Gray scale grading must be recorded in the comments. Acceptance: general colors Dry ≥4.0 / Wet ≥3.0; dark shades/indigo/pigment-dye/garment-dye/flannel/pile/denim fabric Dry 3–4 / Wet 2–3; not applicable to white/cream/ivory colors. Any result below threshold = FAIL. No test photo is required unless the test FAILED.
**Scope:** `QUESTION`
**Error example:** Dark-shade garment graded Dry 2.5/Wet 1.5 but result recorded as "Pass."
**Correct example:** Dark-shade garment graded Dry 2.5/Wet 1.5 → result recorded as "FAIL," with photo attached.


```check
where:
  - kind: checklist
    match: [wet, dry, rub, test]
    field: comment
when: null
check: null
```

---

## Section 7 – Report Photos

### 7.1 General / Front Page

---

**ID:** 7.1.1
**Field / Location:** Report front page
**What to check:** A group picture of all SKUs/items inspected must appear on the report's front page.
**Scope:** `QUESTION`
**Error example:** Front page has no group photo of the inspected items.
**Correct example:** Front page includes a group photo captioned "New Era Cap – Alpilao International sole company Ltd."


```check
where: [report.all_captions]
when: null
check: null
```

---

**ID:** 7.1.2
**Field / Location:** Defect Breakdown section
**What to check:** A screenshot of the Excel defect breakdown table must be embedded in the report body (in addition to the file attachment).
**Scope:** `QUESTION`
**Error example:** Defect Breakdown section only says "Excel attached" with no screenshot shown.
**Correct example:** Defect Breakdown section shows the Excel table screenshot inline plus the attached file.


```check
where:
  - kind: checklist
    match: [defect, breakdown]
    field: photo_count
when: null
check: count_at_least(1)
```

---

### 7.2 Outer Carton Photos

---

**ID:** 7.2.1
**Field / Location:** Photos — Outer Carton
**What to check:** Report must include: Selected Carton (multiple views), Shipping Mark, Carton Label, Barcode Check.
**Scope:** `QUESTION`
**Error example:** Carton Label photo is missing.
**Correct example:** All four outer-carton photo categories are present and correctly labeled.


```check
where:
  - kind: section
    match: [outer, carton]
    field: photo_count
when: null
check: count_at_least(4)
```

---

### 7.3 Inner Carton Photos

---

**ID:** 7.3.1
**Field / Location:** Photos — Inner Carton
**What to check:** Report must include: Selected Carton (inner), Inner Box Label, Barcode Scanning, Opened Box, Inner Packing View, All Product View.
**Scope:** `QUESTION`
**Error example:** "Opened Box" photo is missing.
**Correct example:** All six inner-carton photo categories are present.


```check
where:
  - kind: section
    match: [inner, carton]
    field: photo_count
when: null
check: count_at_least(6)
```

---

### 7.4 Product Photos

---

**ID:** 7.4.1
**Field / Location:** Photos — Products
**What to check:** Report must include: Front View, Back View, Main Embroidery, Embroidery Logo, Reference/Approval Sample vs. Product (comparison).
**Scope:** `QUESTION`
**Error example:** "Ref. Sample vs Product" comparison photo is missing.
**Correct example:** All product photo categories present, including side-by-side reference sample comparison.


```check
where:
  - kind: section
    match: [products]
    field: photo_count
when: null
check: count_at_least(5)
```

---

### 7.5 Specification & Label Photos

---

**ID:** 7.5.1
**Field / Location:** Photos — Spec & Label
**What to check:** Report must include: Compared with Spec., Brand/Fibre Label, Sticker on Visor, Hologram Sticker, Barcode Sticker, Tracking Label.
**Scope:** `QUESTION`
**Error example:** "Compared with Spec." photo is missing.
**Correct example:** All six spec/label photo categories are present.


```check
where:
  - kind: section
    match: [specification, label]
    field: photo_count
when: null
check: count_at_least(6)
```

---

### 7.6 Checking Photos

---

**ID:** 7.6.1
**Field / Location:** Photos — Checking
**What to check:** Report must include: Function Check, Seam Check, Size Check, Visor Curve Height Check, Shape Check, Metal Detection Check.
**Scope:** `QUESTION`
**Error example:** "Shape Check" photo is missing for a cap inspection.
**Correct example:** All six checking-process photos are present.


```check
where:
  - kind: section
    match: [checking]
    field: photo_count
when: null
check: count_at_least(6)
```

---

### 7.7 Moisture Checking Photos

---

**ID:** 7.7.1
**Field / Location:** Photos — Moisture Checking (cap)
**What to check:** Report must include: Front Panel (nearby Emb.), Visor (Upper), Visor (Lower), Sweatband.
**Scope:** `QUESTION`
**Error example:** Only 2 of the 4 moisture-check photo positions are shown.
**Correct example:** All 4 moisture-check positions are photographed with the moisture meter reading visible.


```check
where:
  - kind: section
    match: [moisture, checking]
    field: photo_count
when: null
check: count_at_least(4)
```

---

### 7.8 Defect Photos

---

**ID:** 7.8.1
**Field / Location:** Defect checklist photos
**What to check:** Every defect found must have a clear close-up photo with a written explanation of where the defect is located on the garment/headwear.
**Scope:** `QUESTION`
**Error example:** A "Broken Stitches" defect entry has a photo but no location description.
**Correct example:** Photo captioned "Broken Stitches" with location context visible/described (e.g. inside back sweatband area).


```check
where: [report.defects_without_photo]
when: null
check: equals(0)
```

---

### 7.9 Mandatory Attachments

---

**ID:** 7.9.1
**Field / Location:** Attachments — Defect Breakdown
**What to check:** The completed Measurement Defect AQL Table Excel file must be attached to the report, using the current template version.
**Scope:** `FULL REPORT` — cross-check against Section 5.2 (defect count match)
**Error example:** No Excel file attached, only a screenshot embedded in the report body.
**Correct example:** File "New Era Cap LLC_Measurement Defect AQL Table_2 June 2025 (1).xls" attached under Attachments → Defect Breakdown.


```check
where: [report.attachment_filenames]
when: null
check: filename_matches("New Era Cap LLC_Measurement Defect AQL Table*.xls")
```

---

## Section 8 – AQL / AOQL Summary

---

**ID:** 8.1.1
**Field / Location:** Inspection Standards box (Workmanship & Measurement sampling/AQL)
**What to check:** Verify the AQL/sampling level used matches the product category:

| Product Category | Workmanship Sampling & AQL | Measurement Sampling & AQL |
|---|---|---|
| Apparel and Accessories | Level II — Critical 0 / Maj 2.5 / Min 4.0 | Fixed 20pcs (all sizes); AQL Not Allowed |
| Headwear (Cap) | Level II — Critical 0 / Maj 1.5 / Min 2.5 | Always 60pcs (all sizes); AQL Not Allowed |
| Brand New Era or High-Profile orders | Level II — Critical 0 / Maj 1.5 / Min 2.5 | Apparel: Fixed 20pcs; AQL Not Allowed. Headwear: Always 60pcs; AQL Not Allowed |

**Scope:** `FULL REPORT` — cross-check against the Advice List (Section 2.1.2)
**Error example:** A cap booking uses Major AQL 2.5 (the apparel value) instead of 1.5.
**Correct example:** Cap booking's Inspection Standards box shows "AQL 1.5" for Major defects, sampling level General II, matching the Headwear row.


```check
where: [workmanship.aql_level_major]
when: null
check: null
```

---

**ID:** 8.1.2
**Field / Location:** Advice List override
**What to check:** If the Advice List specifies a sample size or AQL different from the default table above, the Advice List value takes precedence.
**Scope:** `FULL REPORT`
**Error example:** Report uses the default table's AQL even though the Advice List specifies a custom AQL for this booking.
**Correct example:** Report's AQL matches the Advice List's custom value, not the default table.


```check
where: [out_of_report:booking]
when: null
check: null
```

---

## Section 9 – Pass / Fail Decision Logic

---

**ID:** 9.1.1
**Field / Location:** Quantity section result
**What to check:** Quantity section must PASS if goods are 100% finished and ≥80% packed. It must FAIL if the packed quantity/ratio does not meet the required threshold (per Section 1.1.1), with the unpacked quantity clearly indicated.
**Scope:** `FULL REPORT`
**Error example:** Only 55% of goods are packed, but the Quantity section is marked "Pass."
**Correct example:** Quantity section marked "Fail," with unpacked quantity and ratio clearly stated.


```check
where: [product._first.real_packed_quantity, product._first.expected_packed_quantity]
when: null
check: ratio_at_least(0.8)
```

---

**ID:** 9.1.2
**Field / Location:** Overall Workmanship result
**What to check:** Overall Workmanship result must be PASS only if total defects found (per severity) are less than or equal to the acceptance point defined by the AQL table for the sample size used; any Critical defect (AQL 0) triggers FAIL.
**Scope:** `FULL REPORT`
**Error example:** 15 Major defects found against an acceptance point of 14, but result is marked "Pass."
**Correct example:** 10 Major defects found against an acceptance point of 14 → result correctly marked "Pass."


```check
where: [workmanship.found_critical]
when: workmanship.result equals PASS
check: equals(0)
```

---

**ID:** 9.1.3
**Field / Location:** Sample collection
**What to check:** No samples should be collected from the inspection. All defective units must be repaired or replaced on-site. No defective product should ever be knowingly shipped to the client.
**Scope:** `QUESTION`
**Error example:** Report notes defective units were set aside as "samples" to send to the client instead of being repaired/replaced.
**Correct example:** Report confirms all defective units found were repaired or replaced before packing was finalized.


```check
where: [report.global_remark]
when: null
check: extract_bool("Does this remark confirm that defective units were repaired or replaced rather than collected as samples?")
```

---

## Ambiguous or Incomplete Rules

> This section lists rules found in the source files that were unclear, contradictory, or
> missing key information. Review and resolve before using this document operationally.

- **Cap measurement sample distribution (Section 6.2.3):** the training material describes
  measurement sampling as "3 cap shapes × 20 pcs," but real reports show the fixed 60-pc
  total sometimes spread across more than 3 style/MI combinations. The 60-pc total itself is
  confirmed; how it must be split across shapes when more than 3 are present in the selected
  POs is not fully specified in the source material.
