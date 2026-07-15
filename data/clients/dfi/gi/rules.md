# DFI H&B Inspection Report Review – Rules Reference

> Sources: GI DFI H&B (Inspector Standard Test Procedure PDF, Apr 2025); Golden Report / Report Team GI (Apr 18 2026); Inspector To-Do List (Nov 2025); Sample Report Q2603753830
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

### 1.1 Cover Page — Inspection Details

---

**ID:** 1.1.1
**Field / Location:** Supplier Name / Factory Name — Cover page, Inspection Details
**What to check:** Both fields must be filled in English using the combined format: `Supplier Name (Factory Name)`. Neither field may contain Chinese characters or show only one of the two names.
**Scope:** `QUESTION` — verify both fields independently
**Error example:** Supplier Name = "Ruby Beauty Corporation Limited" / Factory Name = "ZHEJIANG YASILI COSMETICS CO., LTD" filled as two separate entries, or one field left blank
**Correct example:** Both fields read "Ruby Beauty Corporation Limited (ZHEJIANG YASILI COSMETICS CO., LTD)"

---

**ID:** 1.1.2
**Field / Location:** Product Name — Cover page / POs & product details, Name (Main identifier)
**What to check:** The product name field must show the real product name, not the SKU or barcode string. QIMAone auto-populates the SKU by default; the inspector must replace it manually. Check both the cover page and the POs & product details section.
**Scope:** `SECTION` — verify the same product name is consistent between cover and POs section
**Error example:** Name field reads "1_4894514123593 [Q2608117119_1]" (SKU string left unreplaced)
**Correct example:** Name field reads "Mannings Guardian Honey Moisturising Lip Balm 4.5g"

---

**ID:** 1.1.3
**Field / Location:** PO Number — Cover page, Inspection Details
**What to check:** If no PO was found on site, the field must read exactly "N/A" with no additional comment. The field must not be left blank.
**Scope:** `QUESTION` — verify field value only
**Error example:** PO field is blank, or reads "N/A — no PO available on site"
**Correct example:** PO field reads "N/A"

---

**ID:** 1.1.4
**Field / Location:** MFG Date / EXP Date / Batch Code — Cover page, Inspection Details
**What to check:** If all three date/batch fields are "N/A", they must be replaced with the sentence: "Refer to the individual batch/date code in the date code check section". If at least one field has a real value, no replacement is needed.
**Scope:** `SECTION` — cross-check with Date Code Check section to confirm codes are recorded there
**Error example:** MFG Date = N/A, EXP Date = N/A, Batch Code = N/A, and no replacement sentence present
**Correct example:** All three fields replaced with "Refer to the individual batch/date code in the date code check section", and codes are filled in the Date Code Check checklist

---

**ID:** 1.1.5
**Field / Location:** Location — Cover page, Inspection Details
**What to check:** The location field must be written entirely in English. No Chinese characters are permitted.
**Scope:** `QUESTION` — verify language only
**Error example:** Location reads "浙江省义乌市稠江街道" or a mix of Chinese and English
**Correct example:** Location reads "NO.163 CHOUYI WEST ROAD, YITING TOWN, YIWU CITY, China"

---

**ID:** 1.1.6
**Field / Location:** Unit — Cover page / POs & product details
**What to check:** The unit field must not display "Other". If "Other" appears, it must be replaced with the actual unit found in the booking — typically "Boxes" or "Packs".
**Scope:** `QUESTION` — verify field value only
**Error example:** Unit = "Other"
**Correct example:** Unit = "Pcs" or "Boxes"

---

### 1.2 Overall Result and Inspector Remarks

---

**ID:** 1.2.1
**Field / Location:** Overall Inspection Result — Cover page
**What to check:** The overall result must match the Pass/Pending/Fail/Missing Inspection logic defined in Section 8. Verify that the result shown is consistent with all findings in the body of the report.
**Scope:** `FULL REPORT` — cross-check against all test results, AQL outcomes, and measurement results
**Error example:** Overall result = PASS but adhesive test is recorded as failed (printing unreadable)
**Correct example:** Overall result = PENDING when adhesive test failed, with corresponding remark explaining the reason

---

**ID:** 1.2.2
**Field / Location:** Inspector's Remark — Cover page
**What to check:** Every Pending or Failed report must contain both of the following remarks: (1) "The inspection result is [Pending/Failed] due to [reason]." (2) "All defective items (and failure findings) are presented to the factory." Both must be present. Neither is optional.
**Scope:** `FULL REPORT` — result stated in remark must match the overall result on the cover
**Error example:** Report is Pending due to adhesive test failure, but Inspector's Remark only states "All defective items have been presented to the factory" with no explanation of the reason
**Correct example:** "The inspection result is Pending due to the adhesive test failed: 1 of the 8 samples was unreadable after the adhesive test. All defective items and failure findings are presented to the factory."

---

**ID:** 1.2.3
**Field / Location:** Inspector's Remark — Cover page
**What to check:** The remark must be in English. Chinese characters in inspector-written remark fields are not acceptable. Exception: date codes recorded exactly as printed on the product may appear in Chinese.
**Scope:** `QUESTION` — verify language of remark text
**Error example:** Remark contains a sentence written in Chinese describing a finding
**Correct example:** All remark text in English; a date code printed as "生产日期: 2026/01/12" may appear as-is if recorded from the product

---

## Section 2 – Documents and Attachments

### 2.1 Mandatory Attachments

---

**ID:** 2.1.1
**Field / Location:** Attachments section — end of report
**What to check:** The Measurement Table Excel file must be attached. Verify its presence. Also verify that the filename does not contain Chinese characters — a Chinese filename prevents the report team from opening the file.
**Scope:** `QUESTION` — verify presence and filename
**Error example:** Attachment absent, or filename reads "DFI测量表_20260402.xlsx"
**Correct example:** Attachment present with filename "DFI Sampling Plan R-Cloud-Q2603753830 sample.xlsx"

---

### 2.2 GSS (Green Seal Sample) Status

---

**ID:** 2.2.1
**Field / Location:** Green Seal Sample (GSS) — DFI(H&B) Product Specifications checklist
**What to check:** The GSS result must be "Yes" (available on site and valid) for any report with an overall result of PASS. If GSS is absent, expired, or invalid, the report must be PENDING. Verify the GSS result is consistent with the overall result.
**Scope:** `FULL REPORT` — cross-check GSS availability against overall result
**Error example:** GSS field = "No — GSS not available" but overall result = PASS
**Correct example:** GSS field = "Yes" for a PASS report; GSS field = "No" with a Pending overall result and remark explaining the situation

---

**ID:** 2.2.2
**Field / Location:** Any remark, photo caption, or checklist field throughout the report
**What to check:** The term "GSS" is the only accepted terminology for the approval sample. "Approved Sample", "Golden Sample", or any equivalent must never appear anywhere in the report text or photo captions.
**Scope:** `FULL REPORT` — scan all text fields and photo captions
**Error example:** Photo caption reads "Approved Sample vs Production" or remark states "compared with Golden Sample"
**Correct example:** All references use "GSS" — e.g. photo caption "GSS vs Actual Product"

---

**ID:** 2.2.3
**Field / Location:** Re-Sealed Green Seal Sample — DFI(H&B) Product Specifications checklist
**What to check:** After using the GSS for comparison, the inspector must re-seal it in a polybag with a signed QIMA sticker showing the date and order number, and upload a photo. Verify the re-sealed GSS photo is present in the Product Specifications section.
**Scope:** `SECTION` — cross-check re-seal photo against GSS comparison photos (if comparison was done, re-seal must follow)
**Error example:** GSS comparison photos are present but no re-sealed GSS photo is uploaded
**Correct example:** Re-sealed GSS photo shows polybag sealed with QIMA sticker, sticker is signed, date and order number visible

---

## Section 3 – Packaging and Carton

### 3.1 Carton Shipping Mark

---

**ID:** 3.1.1
**Field / Location:** Carton Shipping Mark — DFI(H&B) Shipping Carton Verification checklist
**What to check:** Photos of the shipping mark must be present for both the front face and the side face of the carton. If an inner shipping mark exists, it must also be photographed.
**Scope:** `SECTION` — verify photo count and angles within Shipping Carton section
**Error example:** Only one shipping mark photo showing the front face; side face photo absent
**Correct example:** Two shipping mark photos: one of the front face, one of the side face

---

**ID:** 3.1.2
**Field / Location:** Carton Check: Dimensions and Weight — DFI(H&B) Shipping Carton Verification checklist
**What to check:** For each product style, the report must record: printed size (L×W×H in mm), actual measured size, printed weight (kg), and actual measured weight. If actual values differ from printed spec, a remark is required. A difference alone does not trigger Pending or Fail.
**Scope:** `SECTION` — cross-check recorded values against remark; verify remark is present when a difference exists
**Error example:** Actual carton size = 420×265×150mm but printed spec = 420×265×145mm, and no remark describing the difference
**Correct example:** Remark states: "Actual carton size is 420×265×150mm vs printed spec 420×265×145mm on shipping mark."

---

### 3.2 Product Packaging Levels

---

**ID:** 3.2.1
**Field / Location:** Individual Pack AQL table — Workmanship section
**What to check:** An Individual Pack AQL table must be present if and only if the product has individual packaging. If the product has no individual pack, the table must be absent. Verify against the product description and photos.
**Scope:** `FULL REPORT` — cross-check table presence against product structure visible in photos and POs section
**Error example:** Individual Pack AQL table is present but all photos show products with no individual packaging layer
**Correct example:** Individual Pack AQL table present and photos confirm a separate individual pack layer exists inside the consumer pack

---

## Section 4 – Workmanship

### 4.1 AQL Tables

---

**ID:** 4.1.1
**Field / Location:** Workmanship AQL tables — Workmanship section (Consumer Pack, Individual Pack, Destructive Sample)
**What to check:** Three separate AQL tables must be present: Consumer Pack, Individual Pack (if applicable), and Destructive Sample. Each must have its own result. Verify sampling levels match the standard: Consumer Pack = Level II (onsite) or Level I (remote); Individual Pack = S4 (restorable pack) or S3 (destructive/sticker); Destructive Sample = S1.
**Scope:** `SECTION` — verify each table independently
**Error example:** Only one combined AQL table covers all packing levels; or Individual Pack table uses Level II instead of S3/S4
**Correct example:** Three separate tables with sampling levels: Consumer Pack Level II, Individual Pack S3, Destructive Sample S1

---

**ID:** 4.1.2
**Field / Location:** Sample size and Max (acceptance number) — Workmanship AQL tables
**What to check:** The "Checked" number must match the sample size in the DFI Sampling Plan. The "Max" acceptance numbers must match: sample size 8 → 0/0/0; sample size 13 → 0/0/1; sample size 32 → 0/1/3. Destructive sample size is 8 if lot ≤ 35,000 and 13 if lot > 35,000.
**Scope:** `SECTION` — cross-check Checked, Max, and lot size within the same section
**Error example:** Destructive sample size = 8 but lot size = 40,000 (should be 13); or sample size 13 with Max = 0/0/0 (should be 0/0/1)
**Correct example:** Lot size 32,064 → destructive sample size = 8 → Max = 0/0/0

---

**ID:** 4.1.3
**Field / Location:** AQL values (CRI/MAJ/MIN) — Workmanship AQL tables
**What to check:** AQL values for general products must be Not Allowed / 1.5 / 4.0. Earplug products: same (Not Allowed / 1.5 / 4.0). Protection Mask products: percentage-based values must match the DFI Sampling Plan attachment exactly.
**Scope:** `FULL REPORT` — cross-check AQL values against product type
**Error example:** Protection Mask product report shows AQL = Not Allowed / 1.5 / 4.0 instead of the percentage-based values from the Sampling Plan
**Correct example:** General product report shows AQL = Not Allowed / 1.5 / 4.0 across all three packing levels

---

**ID:** 4.1.4
**Field / Location:** Colors, Labels, Artworks, Accessories and Markings result — Workmanship section
**What to check:** If no special finding was observed in this category, the result must be "OK". QIMAone sometimes auto-generates "N/A" — this must be manually corrected to "OK" if there is no finding.
**Scope:** `QUESTION` — verify result value
**Error example:** Colors, Labels, Artworks result = "N/A" with no corresponding finding or explanation
**Correct example:** Colors, Labels, Artworks result = "OK" with remark "Conform with approval samples."

---

### 4.2 Defect Recording

---

**ID:** 4.2.1
**Field / Location:** Defect list and comments — Workmanship section
**What to check:** If no defects were found, the text "No Defects Found" must appear in the defect section. If defects were found, each defect must have at least one supporting photo with a QIMA sticker or arrow clearly indicating the defect.
**Scope:** `SECTION` — cross-check defect entries against photos
**Error example:** 3 defects recorded but only 1 photo uploaded with no arrows; or defect section is blank with no "No Defects Found" text
**Correct example:** "No Defects Found" text present when no defects; or each defect has a labeled photo with visible arrow or QIMA sticker

---

**ID:** 4.2.2
**Field / Location:** Defect comments and Important Remark — Workmanship section
**What to check:** If multiple defects were found on the same sample, only the most serious is counted in the AQL. A remark must appear in both the Defect Comment and the Important Remark following this template: "Found [X] pcs with multiple defects: [most serious] (counted into AQL) + [other] (excluded from AQL), see defect pictures below, all defects are arrowed."
**Scope:** `SECTION` — cross-check defect count in AQL table against remark
**Error example:** AQL table shows 3 Minor defects on the same sample but the remark only says "Found dirt mark and scratch mark" with no indication of which was counted
**Correct example:** "Found 1 pc with multiple defects: Dirt mark (counted into AQL) + Shadow Mark (excluded from AQL), see defect pictures below, all defects are arrowed."

---

**ID:** 4.2.3
**Field / Location:** AQL table and remark — Workmanship section
**What to check:** If a defect was found outside the workmanship check stage (e.g. during quantity check or dimension measurement), it must NOT appear in the AQL workmanship table. Instead, a remark must describe it separately, the report must be set to Pending, and the full consumer pack must be sealed in a polybag with a QIMA sticker.
**Scope:** `FULL REPORT` — cross-check remark against AQL table entries and overall result
**Error example:** Defect found during quantity check is added directly to the workmanship AQL table without any remark
**Correct example:** AQL table unchanged; remark states "Found additional 1 MIN defect on 1 pc Consumer Pack during Quantity Check of Dimension section"; overall result = Pending

---

## Section 5 – Tests and Measurements

### 5.1 Date Code Check

---

**ID:** 5.1.1
**Field / Location:** Date Code Check table — DFI(H&B) Date code check & Barcode details checklist
**What to check:** Date codes must be recorded exactly as printed: same format, separators, and casing. The format AND printing position must match between GSS and actual product. The actual values (dates, lot numbers) may differ — this is acceptable.
**Scope:** `SECTION` — cross-check GSS row against Actual Product row within the date code table
**Error example:** GSS shows MFG Date format "12/01/2026" (DD/MM/YYYY) but Actual Product records it as "2026/01/12" (YYYY/MM/DD)
**Correct example:** Both GSS and Actual Product rows show the same format "12/01/2026" with the same field positions; values may differ

---

**ID:** 5.1.2
**Field / Location:** Date Code Check table — DFI(H&B) Date code check & Barcode details checklist
**What to check:** At least one of the three codes must be present: MFG Date / EXP Date / Lot# (Batch#). If a code is absent on the product, record "N/A" in that field. If no date code AND no batch code is found on any packaging: this is a back-office escalation situation — verify that a remark and a Pending result are present.
**Scope:** `FULL REPORT` — cross-check against overall result if all codes are N/A
**Error example:** All three fields (MFG, EXP, Batch) are blank for actual product rather than filled with "N/A"
**Correct example:** MFG Date = "N/A", EXP Date = "12/01/2029", Batch Code = "26011"

---

**ID:** 5.1.3
**Field / Location:** Date Code Check table — multiple batches or sub-products
**What to check:** If the product has multiple batches or multiple sub-products (e.g. a travel set), all date codes must be clearly separated by batch and item keywords, with 1 batch per line. Chinese date codes must be recorded in Chinese exactly as printed.
**Scope:** `QUESTION` — verify formatting of date code table entries
**Error example:** Travel set with shampoo and conditioner, all date codes listed in one cell as "Shampoo 001 Conditioner 002 07/09/2023"
**Correct example:** Separate rows: "Shampoo (batch 001): MFG 07/09/2023" / "Conditioner (batch 001): MFG 17/08/2023"

---

**ID:** 5.1.4
**Field / Location:** Barcode Details — DFI(H&B) Date code check & Barcode details checklist
**What to check:** The full barcode number must be recorded for each packaging level: Individual Pack / Consumer Pack / Outer Carton. If no Individual Pack exists, that field must show "N/A" — it must not be left blank.
**Scope:** `QUESTION` — verify all three barcode fields are filled
**Error example:** Individual Pack barcode field is blank; Consumer Pack = "4894514109108"; Outer Carton = "04894514125986"
**Correct example:** Individual Pack = "N/A"; Consumer Pack = "4894514109108"; Outer Carton = "04894514125986"

---

### 5.2 Product Measurements

---

**ID:** 5.2.1
**Field / Location:** Measurement table — DFI(H&B) Product Dimensions & Weights checklist
**What to check:** Only specs explicitly claimed on the product name, label, or packaging must be measured. Do not measure specs not claimed anywhere. Both Consumer Pack and Individual Pack claimed specs must be measured. The Measurement Table is a template — only rows relevant to the actual product should be filled.
**Scope:** `SECTION` — cross-check measured specs against product label visible in photos
**Error example:** Report measures carton dimensions even though no carton dimension spec is claimed on the label, while the claimed volume (500 ml) is left unmeasured
**Correct example:** Only the specs printed on the packaging are measured: quantity (30 pcs), volume (500 ml), dimension (if claimed)

---

**ID:** 5.2.2
**Field / Location:** Measurement results — DFI(H&B) Product Dimensions & Weights checklist
**What to check:** Apply pass/fail logic per spec type: (1) Volume, Quantity, Weight (general product): actual ≥ label claim → PASS; actual < label claim (even by 0.01) → FAIL. (2) Weight (health product — identified by NIP panel) and Size/Dimension: tolerance required; within tolerance → PASS; outside tolerance in either direction → FAIL.
**Scope:** `SECTION` — cross-check recorded values against pass/fail result and label claim
**Error example:** Product net weight label claim = 4.500g; actual measured = 4.480g; result recorded as PASS
**Correct example:** Product net weight = 4.480g < 4.500g label claim → result = FAIL

---

**ID:** 5.2.3
**Field / Location:** Measurement remark — DFI(H&B) Product Dimensions & Weights checklist
**What to check:** For any tolerance-based check (dimension or health product weight), the tolerance range must be stated in the remark regardless of pass or fail outcome. Required format: "Checked OK, the tolerance range of [weight/dimension] is XXX – XXX."
**Scope:** `SECTION` — verify remark is present whenever a tolerance-based measurement is recorded
**Error example:** Dimension measured and result = PASS but remark only says "Checked OK" with no tolerance range stated
**Correct example:** "Checked OK, the tolerance range of dimension is 17.5cm – 18.5cm."

---

**ID:** 5.2.4
**Field / Location:** Measurement table values — DFI(H&B) Product Dimensions & Weights checklist
**What to check:** If all 8 (or 13) samples show exactly the same value for a measurement, flag as a likely data entry error. Real measurement variation across samples is expected — identical values across all samples are suspicious.
**Scope:** `QUESTION` — scan all measurement columns for uniform values
**Error example:** Product weight: S1=0.705, S2=0.705, S3=0.705, S4=0.705, S5=0.705, S6=0.705, S7=0.705, S8=0.705
**Correct example:** Product weight values vary across samples: S1=10.730, S2=10.740, S3=N/A, S4=10.710, S5=10.730, S6=10.680, S7=10.710, S8=10.750

---

**ID:** 5.2.5
**Field / Location:** Measurement table — Protection Mask products
**What to check:** For Protection Mask products, the individual mask net weight must always be measured and recorded, even if no weight spec is claimed on the label.
**Scope:** `QUESTION` — verify net weight row is present for Mask products
**Error example:** Protection Mask report with no product net weight row in the measurement table
**Correct example:** Measurement table includes "Product net weight" row filled for all 8 (or 13) destructive samples

---

**ID:** 5.2.6
**Field / Location:** Measurement table — Health products (products with NIP panel)
**What to check:** For health products (identified by a Nutrition Information Panel on the label), both total net weight and individual serving weight must be measured if the serving size per piece is stated on the NIP. Examples: "1 Capsule/1.043g" → weigh 1 capsule; "3 Tablets/5.4g" → weigh 3 tablets; "1370mg/softgel" → weigh 1 softgel.
**Scope:** `SECTION` — cross-check NIP label visible in photos against measurement rows
**Error example:** NIP states "Serving size: 1 capsule (1.043g)" but measurement table only records total net weight, no capsule weight row
**Correct example:** Measurement table has both "Product net weight" row and "Serving weight (1 capsule)" row, both filled for all 8 samples

---

### 5.3 Carton Drop Test

---

**ID:** 5.3.1
**Field / Location:** Carton drop test result — DFI(H&B) Shipping Carton Verification checklist
**What to check:** The carton drop test result must follow this logic: PASS if no damage on product (carton dented but product OK = PASS); PENDING if carton broken/opened but product undamaged; FAIL if product is damaged or falls out. Any outcome other than a fully clean pass requires a descriptive remark.
**Scope:** `SECTION` — cross-check result against remark description
**Error example:** Remark states "carton was broken at drop 7, product not damaged" but result = FAIL
**Correct example:** Remark states "Carton damaged at drop 7 (1 point, 1 edge, 5 faces were done) and no damage on products. Hasn't further proceeded with the rest drop as the carton already opened." Result = PENDING

---

**ID:** 5.3.2
**Field / Location:** Carton drop test result — DFI(H&B) Shipping Carton Verification checklist
**What to check:** The carton drop test is mandatory for all products. Exceptions: fragile products (ceramics, glass — factory documentation must be checked), and product "Guardian WEIGHING SCALE BR9012" from supplier "Camry Electronic". If the factory refused: result must be PENDING with a remark.
**Scope:** `FULL REPORT` — cross-check against product type and overall result
**Error example:** Drop test section shows "N/A — factory refused" but overall result = PASS
**Correct example:** Drop test remark states "Factory refused the carton drop test" and overall result = PENDING

---

### 5.4 Adhesive Test

---

**ID:** 5.4.1
**Field / Location:** Adhesive test result — test checklist (e.g. DCL 013 - Dairy Farm - Toiletry V9 H&B)
**What to check:** An adhesive test failure (printing unreadable after tape removal) must result in overall report = PENDING, never FAIL. Verify consistency between adhesive test result and overall result.
**Scope:** `FULL REPORT` — cross-check adhesive test result against overall result
**Error example:** Adhesive test = "Not OK — 1 sample unreadable" and overall result = FAIL
**Correct example:** Adhesive test = "Not OK — 1 of 8 samples was unreadable after the adhesive test" and overall result = PENDING

---

**ID:** 5.4.2
**Field / Location:** Adhesive test remark — test checklist
**What to check:** The tape model used must be stated in the remark. Accepted models: 3M 500, 3M 600P, 3M 810.
**Scope:** `QUESTION` — verify remark contains tape model reference
**Error example:** Adhesive test remark reads "PASSED. Checked ok." with no tape model mentioned
**Correct example:** Adhesive test remark reads "PASSED. Checked ok, and the tape model was 3M 500."

---

**ID:** 5.4.3
**Field / Location:** Adhesive test remark — test checklist (exemption products)
**What to check:** For products on the adhesive test date code exemption list (cotton tips in canisters from SOFT TIP (THAILAND) CO., LTD and WISE EVER ENTERPRISES LIMITED; PE bag products including Gurdian/Mannings amino acid bubble cleansing towel and Mannings Face Towel 10s), the date code area is exempt. If this exemption applies, a mandatory remark must be added: "Adhesive test on the date code waived due to limitation of the can and ink." All other printed areas on these products must still be tested.
**Scope:** `QUESTION` — verify exemption remark is present when applicable
**Error example:** Mannings Spiral Cotton Tips report has no remark about the date code exemption
**Correct example:** Remark reads "Adhesive test on the date code waived due to limitation of the can and ink."

---

### 5.5 Rubbing Test

---

**ID:** 5.5.1
**Field / Location:** Rubbing test result — test checklist
**What to check:** The rubbing test must be performed on all printed areas and markings on both Consumer Pack and Individual Pack (if present). The test must be performed with both dry cloth (10 strokes, 9N force) and wet cloth. Result = PASS if printing clear and cloth unstained; FAIL if printing rubbed off, dimmed, or illegible.
**Scope:** `SECTION` — cross-check result against photos showing cloth and product surface
**Error example:** Rubbing test result = PASS but only consumer pack photos are present; no rubbing test photos for individual pack
**Correct example:** PASS result with photos showing rubbing performed on both consumer pack and individual pack surfaces, cloth visible and unstained

---

## Section 6 – Report Photos

### 6.1 Mandatory Photo Presence

---

**ID:** 6.1.1
**Field / Location:** Cover photo — Cover page
**What to check:** The cover photo must show the Consumer Pack (retail packaging), frontal angle, vertical orientation, with the full product name clearly readable.
**Scope:** `QUESTION` — verify photo content
**Error example:** Cover photo shows the outer shipping carton, or the product is photographed at an angle with the name partially cropped
**Correct example:** Frontal, vertical photo of the consumer pack with the full product name visible

---

**ID:** 6.1.2
**Field / Location:** GSS photos — DFI(H&B) Product Specifications checklist
**What to check:** A photo of the GSS showing the DFI QA Team label with signature must be present. The re-sealed GSS photo (polybag + signed QIMA sticker) must also be present.
**Scope:** `SECTION` — verify both GSS-related photos within the Product Specifications section
**Error example:** GSS comparison photos present but no photo of the GSS label or re-sealed GSS
**Correct example:** GSS label photo shows DFI QA signature clearly; re-sealed GSS photo shows polybag, QIMA sticker signed with date and order number

---

**ID:** 6.1.3
**Field / Location:** GSS comparison photos — DFI(H&B) Product Specifications checklist
**What to check:** GSS vs actual product comparison photos must cover: all four faces (top, bottom, front, back) for Consumer Pack and Individual Pack (if present); date code area close-up; composition/ingredient label; volume or quantity claims; all barcodes and markings; product inside (capsules, liquid, etc.). Each element must appear in a photo.
**Scope:** `SECTION` — verify completeness of comparison photo set
**Error example:** Comparison photos show only the front and back of consumer pack; no close-up of the date code area, no photos of product inside
**Correct example:** Photos cover all four faces of consumer pack, close-up of date code area on both GSS and actual product, composition label, barcode, and product inside (e.g. lip balm stick removed from packaging)

---

**ID:** 6.1.4
**Field / Location:** Measurement photos — DFI(H&B) Product Dimensions & Weights checklist
**What to check:** Every spec that was measured must have at least one photo per sample (minimum 8 photos for a sample size of 8). Weight photos must show the scale display readable with the product on the scale. Dimension photos must show the measuring tool and product.
**Scope:** `SECTION` — cross-check number of photos against sample size and number of measured specs
**Error example:** Sample size = 8 but only 3 weight photos uploaded; scale display not readable in photos
**Correct example:** 8 photos of weight measurement, one per sample; scale display showing the reading clearly in each photo

---

**ID:** 6.1.5
**Field / Location:** Carton drop test photos — DFI(H&B) Shipping Carton Verification checklist
**What to check:** Three photo stages are required: (1) before drop showing intact carton; (2) during drop; (3) after drop showing carton exterior condition AND interior product condition. Interior product photo is especially critical when any damage or deformation is observed.
**Scope:** `SECTION` — verify all three photo stages are present
**Error example:** Only one after-drop photo of the carton exterior; no photo showing the interior product condition
**Correct example:** Three-stage photo set: intact carton before drop; carton being dropped; carton opened after test showing interior product condition

---

**ID:** 6.1.6
**Field / Location:** Adhesive and Rubbing test photos — test checklist
**What to check:** Adhesive test photos must clearly show the tape being applied or removed on the date code area specifically, for both Consumer Pack and Individual Pack (if present). Rubbing test photos must show the cloth on the product surface.
**Scope:** `SECTION` — verify photo content and coverage
**Error example:** Adhesive test photo shows tape applied to the front artwork area only; no photo covering the date code; no individual pack test photo
**Correct example:** Adhesive test photos show: tape on date code area of consumer pack + tape on date code area of individual pack; rubbing test photo shows cloth on product surface

---

**ID:** 6.1.7
**Field / Location:** Factory Review photos — QIMA Factory Review checklist
**What to check:** The following photos must be present: factory entrance/gate (confirming location), inspection room lighting, weighing scale and measuring tools with calibration certificates visible, and all three signed QIMA documents (Factory Disclaimer, Draft Report, COC).
**Scope:** `SECTION` — verify all four photo categories within Factory Review
**Error example:** Factory Review section has tools photos but no calibration certificate visible; signed documents photos missing
**Correct example:** Tool photos show calibration certificate alongside the scale; three separate photos of signed Factory Disclaimer, Draft Report, and COC

---

### 6.2 Worker Identity

---

**ID:** 6.2.1
**Field / Location:** Any photo throughout the report
**What to check:** No photo in the report may show a worker's face, name badge, or ID in a way that identifies the individual. If visible, this is a data privacy issue.
**Scope:** `FULL REPORT` — scan all photos
**Error example:** Workmanship defect photo shows an inspector's face clearly visible while holding the product
**Correct example:** Photos show product and defect areas only; faces are not identifiable

---

## Section 7 – AQL Summary

---

**ID:** 7.1.1
**Field / Location:** AQL tables — Workmanship section
**What to check:** Verify the AQL levels and acceptance numbers match the product type and inspection mode (onsite vs remote):

| Product type | Sampling level — Consumer Pack | Sampling level — Individual Pack | Sampling level — Destructive | AQL CRI/MAJ/MIN |
|---|---|---|---|---|
| General (onsite) | Level II | S4 or S3 | S1 | Not Allowed / 1.5 / 4.0 |
| General (remote) | Level I | S3 | S1 | Not Allowed / 1.5 / 4.0 |
| Earplug | See DFI Sampling Plan | See DFI Sampling Plan | S1 | Not Allowed / 1.5 / 4.0 |
| Protection Mask | See DFI Sampling Plan | See DFI Sampling Plan | S1 | % based — see Sampling Plan |

**Scope:** `FULL REPORT` — cross-check product type, inspection mode, and AQL values
**Error example:** Onsite inspection of a general product with Consumer Pack sampling level = Level I (remote level used in error)
**Correct example:** Onsite inspection, general product: Consumer Pack = Level II, Individual Pack = S3, Destructive = S1, AQL = Not Allowed / 1.5 / 4.0

---

## Section 8 – Pass / Fail Decision Logic

---

**ID:** 8.1.1
**Field / Location:** Overall Inspection Result — Cover page
**What to check:** The overall result must follow this logic exactly.

**PASS requires ALL of:**
- No measurement below spec or outside tolerance
- No AQL exceedance
- No onsite test failure (except adhesive — see Pending)
- Carton dimension/weight different from Shipping Mark spec alone does not trigger Pending or Fail
- GSS available, valid, and consistent with bulk product
- Quantity on site ≥ 100% finished AND ≥ 80% packed

**PENDING triggered by ANY of:**
- Adhesive test failed (printing unreadable after tape removal)
- Quantity on site < 100% finished or < 80% packed
- No GSS, GSS expired, or GSS inconsistent with bulk product
- Factory refused carton drop test or did not provide inspection tools
- Any scenario that cannot be confirmed on site

**FAIL triggered by ANY of:**
- Any measurement below spec or outside tolerance (even by 0.01)
- Beyond AQL
- Any onsite test failed — except adhesive test (adhesive fail = Pending)

**MISSING INSPECTION:**
- No product found / wrong address / factory refused inspection entirely

**Scope:** `FULL REPORT` — cross-check overall result against all findings across all sections
**Error example:** Measurement result shows product net weight 4.480g vs label claim 4.500g (shortfall) but overall result = PASS
**Correct example:** Product net weight < label claim → overall result = FAIL regardless of all other findings

---

**ID:** 8.1.2
**Field / Location:** Overall Inspection Result — Cover page
**What to check:** The adhesive test is the only test where failure triggers PENDING rather than FAIL. All other test failures (rubbing test, function test, sensory check, barcode scanning, back adhesive test for pantyliners, bristle pull test) trigger FAIL. Verify the overall result matches this distinction.
**Scope:** `FULL REPORT` — cross-check test results against overall result
**Error example:** Rubbing test failed (printing rubbed off) but overall result = PENDING
**Correct example:** Rubbing test failed → overall result = FAIL; adhesive test failed → overall result = PENDING

---

## Ambiguous or Incomplete Rules

> This section lists rules found in the source files that were unclear, contradictory, or missing key information. Review and resolve before using this document operationally.

- **GSS QA stamp vs signature only (2.2.1 area):** The Inspector To-Do List (Nov 2025) states the GSS must have "a label and be signed by DFI Retail Group QA Team with QA Stamp". The GI (Apr 2026) states "signature only is OK" and "No QA stamp to be displayed on the GSS sticker but signature only is OK". The more recent GI (Apr 2026) takes precedence: signature alone is sufficient, QA stamp is not required. ⚠️ TO CONFIRM: verify with KA whether the Nov 2025 requirement for a QA stamp has been officially superseded.

- **Barcode leading zero (5.1.4 area):** The GI states that if a leading "0" is not recognized by one scanner but is recognized by other apps/tools, the test is PASS with no remark needed. No example of an expected barcode format is provided in the source files to allow independent verification. Rule written based on GI text only.

- **Protection Mask AQL percentage values:** The GI references a "DFI Sampling Plan attachment" for the percentage-based AQL values for Protection Mask products, but this attachment was not provided as a source file. Rules referencing Mask AQL values cannot be fully specified. ⚠️ TO CONFIRM: obtain the DFI Sampling Plan attachment to populate the Mask AQL values.

- **Earplug-specific sampling plan:** The GI references a dedicated file "Earplug only - DFI Sampling Plan, workmanship check, Date Code, measurement" for earplug products, but this file was not provided. Earplug-specific rules cannot be fully specified beyond AQL values. ⚠️ TO CONFIRM: obtain the earplug-specific sampling plan file.
