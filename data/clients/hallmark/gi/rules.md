# Hallmark (HMK) — GI Rules Reference

**Client:** Hallmark (HMK)

This document does not contain any client rules beyond what was provided. Every requirement is a candidate rule; conditional rules ("if X then Y") are captured with their condition in the "What to check" field. Each rule entry uses the standard format: ID | Field/Location | What to check | Scope, where Scope is one of QUESTION (single field, no cross-check needed), SECTION (cross-check within the same report section), or FULL REPORT (cross-check across sections or with attachments). Where a rule is unclear or contradictory, it is still written as a full entry and a note is added directly below it in this format: > ⚠️ TO CONFIRM: [description of the ambiguity].

---

## 0. Notes on source conflicts / things to reconcile

> ⚠️ TO CONFIRM: The product-type sampling table states flatly "Non-HA and Non-HCLP 2D items → Double sampling plan," but the "Sampling plan matrices" section states the choice for non-HA 2D items actually depends on packing method: **mixed-packed → Single**, **individually packed → Double**. These two statements are not fully reconciled. Apply the more specific rule (packing-method dependent) but confirm with back office.

> ⚠️ TO CONFIRM: One passage states "QIMA inspector use single sampling plan for 2D HA items, 3D HA and 3D non-HA items; use double sampling plan for 2D non-HA items," and elsewhere references "QIMA use double sampling plan for 2D non-high attention items but need single sampling plan for 3D and 2D high attention items" — these are consistent with each other but should be read together with the Dayspring-specific exception below.

> ⚠️ TO CONFIRM: For **Dayspring 2D items**, HMK and QIMA inspectors use **double** sampling, but suppliers and Hallmark inspection agents use **single** sampling. Confirm which party status applies when QIMA is a sub-contracted agent vs. direct QIMA inspection.

---

## 1. Mandatory Documents Checklist

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| DOC.1.1 | Product ref number / PO number | If the inspector cannot find the PO in QIMAone, contact the quality team to notify the client immediately. If no timely feedback, proceed with the inspection and update the PO later once available. | QUESTION |
| DOC.1.2 | IRF (Inspection Request Form) | IRF was filled by supplier; it cannot be the supporting document for adjusting test results. Inspectors must check actual testing reports (SR and FR) to verify results. | FULL REPORT |
| DOC.1.3 | Product Spec | Must be used together with the DAS; pay close attention to bulk vs. DAS comparison during inspection. | FULL REPORT |
| DOC.1.4 | Packing list | Available when a carton contains mixed SKUs. Inspector can refer to it to check assortment and carton range; any discrepancy must be clearly remarked. | SECTION |
| DOC.1.5 | PO sheet | Check the order quantity against the QIMAone PO quantity. | FULL REPORT |
| DOC.1.6 | Defects Variances | If no file available onsite, proceed with the inspection and add remarks in the report. | QUESTION |
| DOC.1.7 | SRR / SR (Safety Report, issued by test lab) | Checked per SKU; missing SR → fail SR checkpoint. Valid 1 year (Toys & Children: 4 weeks). For group HMK9700, near-food product must be tested per PO. If the SR report fails and factory can provide the Hallmark override email, it is acceptable — provide the email record to SIC/back office, keep correspondence records, and upload them in the inspection report. If factory provides an SR report at product-format level (same format, within 1-year validity), acceptable, but inspector must contact SIC to double-check. No need for SR report if the SRR report shows 3 "No" — record in the report, no need to fail the SR checkpoint. If missing SR report, mark it in the report and notify Andrew Chan (andrew.chan@hallmark.com). | FULL REPORT |
| DOC.1.8 | SR report — Gift products 3D | A valid SR report must be on file, verified during inspection. SR reports acceptable within 1-year validity, including re-run orders from different POs — except Toys, Children products, and Food-contact products. For Material Confirmation Requirement, when re-using an SR report from a different PO (non-exempt categories, within valid date), inspector must confirm the supplier provided confirmation to the client's 3rd-party lab that no materials have changed for the re-run order. | FULL REPORT |
| DOC.1.9 | FR (Function Report, issued by Hallmark or certified vendor) | Non-high-attention items: FR checked per SKU, valid 1 year. High-attention items: FR valid 1 year AND must be tested by each PO. If missing FR, fail the FR checkpoint. | FULL REPORT |
| DOC.1.10 | Ship test report (transportation test) | Always valid unless there are changes such as supplier, production process, product, packaging material, packed quantity, or packaging method. If missing, fail the Documents and Sample Availability checkpoint. Note: for FR test reports from 2024 onward, the ship test report is included as an appendix. | FULL REPORT |
| DOC.1.11 | VAS (Visual Approval Sample) | For the BU Keepsake ornament only, for mass-product comparison. | QUESTION |
| DOC.1.12 | DAS (Design Approval Sample) | For mass-product comparison; if missing, check with SIC/back office for instructions. | QUESTION |
| DOC.1.13 | Commit sheet (or commit list) — Hallmark Ornaments only | Cross-check: Product SKU vs. Colorway SKU (DAS shows only product SKU; each colorway SKU shows in the product spec and commit sheet — verify correctness in the mass-production shipment). Colorway UPC code must match the actual production package. Package type and retail price (if shown) must match spec under colorway SKU — inform back office if discrepancy found. Product image must match the actual product. Unit price must be consistent between DAS, specs, commit sheet, and actual retail package. Copyright must be consistent between DAS, specs, commit sheet, actual retail package, and product. | FULL REPORT |
| DOC.1.14 | Limit sample | For mass-product comparison, used when mass products cannot 100% meet client requirements; must be signed by HMK engineers. | QUESTION |
| DOC.1.15 | PP Report (Product/Production Pilot Report) | Requested for close-attention and highly confidential products. Must pay close attention to defects found in the PP report during workmanship check, and compare packaging details of the mass product against the PP report. | SECTION |
| DOC.1.16 | Visual Standard (PT. Camino — KPS Keepsake) | Mandatory when factory = PT. Camino Industrial, Indonesia AND product = Hallmark KPS (Keepsake) items only. Inspector must check and follow the Visual Standard during visual inspection, in addition to Hallmark's general visual requirements. | SECTION |
| DOC.1.17 | Additional attachments | Example files available on SharePoint (Additional Attachments – Example link). | QUESTION |

---

## 2. High Attention (HA) Products and Highly Confidential Licensed Products (HCLP)

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| HA.2.1 | How to identify HA product | Check the IRF ("High Attention Item?" field), the Spec ("High Attention Product" field and "Products Integrity Notes"), whether the client attached special checkpoints in the booking, and whether there are instructions under "Products Integrity Notes." | FULL REPORT |
| HA.2.2 | HA handling | Adopt Single Sampling Plan; ask factory to provide the PP Report; ensure sufficient communication with back office/Hallmark PE (Project Engineer) by asking if there are special requirements; if no special doc/instruction found, check with SIC/back office. | FULL REPORT |
| HA.2.3 | HCLP identification | Signs of HCLP found on DAS's tag, Specs, Packaging levels (carton/wholesale/retail), and IRF (e.g., "Confidential licensed SKU," "Highly Confidential-Licensor [Name]," embargo dates, "STOP — DO NOT OPEN" labels). | SECTION |
| HA.2.4 | HCLP photo handling | Do NOT show the entire product picture in the report — use a plank/blank picture and mark "HCLP, no photo." For defect photos, focus only on the defect area, do not show the entire product. | SECTION |
| HA.2.5 | Reason for the inspection (HMK Document Availability checkpoint) | Refer to the IRF "Reason" field: if supplier specifies a reason, select the matching "For CQS – HMK Engineer Specify" option. If the supplier leaves it blank, the supplier is Non-CQS or Non-SEP — select that option. | QUESTION |

---

## 3. Production Status / Timing (PSI)

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| PSI.3.1 | Finished % / Packed % at PSI | Inspector must immediately inform the quality team about on-site status. If ≥80% finished and packed, QIMA can proceed with inspection and add a remark in the report. If <80% finished and packed before 12pm, QIMA can issue a missing inspection — unless the inspector can start with another SKU that is finished and packed. | QUESTION |

---

## 4. Carton & Product Selection

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| CS.4.1 | Carton selection formula | Cartons to select = Visual sample size ÷ retail sample to be pulled from each carton. Visual sample size from the booking (calculated based on AOQL level and lot size); retail-per-wholesale and wholesale-per-carton figures from the PO. | SECTION |
| CS.4.2 | Pulling ratio table | 1 retail/wholesale → pull 5 wholesales/shipper (5 samples); 2 retail/wholesale → pull 2 wholesales/shipper (4 samples); 3 retail/wholesale → pull 1 wholesale/shipper (3 samples); 4 retail/wholesale → pull 1 wholesale/shipper (4 samples); 5+ retail/wholesale → pull 1 wholesale/shipper (5 samples); bulk-packed (no wholesale) → no more than 5 samples/shipper. | SECTION |
| CS.4.3 | Pulling procedure | Pull one complete shipper carton to the inspection room; other samples drawn in the warehouse via a turnover box. Open half the cartons from the top, half from the bottom. Pull samples from all layers randomly. If total carton quantity is less than the calculated sample, pull evenly from all cartons. | SECTION |
| CS.4.4 | Repack of OK sample | The inspected OK sample must be re-packaged into a carton with a QIMA sticker placed above the corner label. | QUESTION |
| CS.4.5 | Packaging Inspection sample size | Always select 18 cartons/wholesale packs/retail packs for visual/packaging check. If any defect is found in these 18, do a second sampling of 100 (total 118). Reference: sampling table — 18 pcs first sample (Accept 0 / Reject 3), 100 pcs second sample (cumulative Accept ≤2 / Reject ≥3). | SECTION |
| CS.4.6 | Cartons piling up | Factory must pile cartons no more than 3 rows and less than 2 meters high, per sketch. Inspector can refuse to proceed if not met — must check with back office first. | QUESTION |
| CS.4.7 | Shipper carton checks (18 cartons) | Check: shipping mark, shipper quality, carton label contents & position, Bumpa sticker/partial-filled label (if applicable), carton label scanning, quantity verification (wholesale qty in shipper consistent with specs/ship test report/carton label), carton label vs. PO, carton quality (5-ply), carton dimension. | SECTION |
| CS.4.8 | Carton dimension tolerance | Refer to "Shipper Dimensions & Weight & Marks" QIMAone instructions per retailer brand. If actual dimension exceeds max/min, fail the shipper check and add a remark. If no specific tolerance in spec, default weight tolerance = +/-5%. | SECTION |
| CS.4.9 | Product selection | Follow QIMA's SOP (Standard Operation Process) for all product types. | QUESTION |

---

## 5. Sampling Plans & AQL/AOQL

### 5.1 Plan selection by product type

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SMP.5.1 | Non-HA/Non-HCLP 2D items | AOQL Double sampling per spec/IRF (first sample size from Double Sample Plan matrix). *See ⚠️ TO CONFIRM in Section 0.* | FULL REPORT |
| SMP.5.2 | Non-HA/Non-HCLP 3D items | AOQL Single sampling per spec/IRF (sample size from LOT size + Single Sampling Plan matrix). | FULL REPORT |
| SMP.5.3 | HA and HCLP 2D and 3D | AOQL Single sampling per spec/IRF regardless of dimension type. | FULL REPORT |
| SMP.5.4 | Dayspring 2D items | AOQL Double sampling (first sample per Double Sample Plan matrix) — for HMK/QIMA inspectors. | FULL REPORT |
| SMP.5.5 | Dayspring 3D items | AOQL Single sampling, minimum sample size = 85, per AOQL level and Single Sampling Plan Matrix. | FULL REPORT |
| SMP.5.6 | Sewn/plush products | Major AOQL 1.5%, Minor AOQL 4.0%; sample size per LOT size (Sewn/plush sampling table). | FULL REPORT |
| SMP.5.7 | Pre-packaged / PDQ products | Single sampling plan for ALL items (HA and non-HA); sampling based on LOT size in **retail quantity**. | FULL REPORT |
| SMP.5.8 | Hallmark Nihon (Japan) orders | AOQL 1.5% — double sampling for 2D items, single sampling for 3D items. "JP" appended next to Category Name on carton marking; "Nihon JP Order" noted in IRF remark column. Non-JP Nihon orders use AOQL 3.0%. | FULL REPORT |
| SMP.5.9 | Fixtures and Dealer Service items | AOQL 2.5% single sampling, fixed sample size = 15, for ALL inspection parties (HMK, QIMA, Agent, CQS, SEP) — Accept Number = 0. | FULL REPORT |
| SMP.5.10 | Marks & Spencer products | Per department/product-format table (T21/T79/T40 codes): AQL Level I (Major 1.5/Minor 4.0/Total 4.0) for Everyday/Xmas Card, Roll Wrap, Bag, Halloween/Party/Stationery pure-printing items, Ribbon & Bow. AQL Level II (same values) for Cracker, Techno Card, Halloween/Stationery non-pure-printing, 3D Xmas/Advent, Event Gifting, Puzzle, Plush, Art & Craft, Toys, Leather product. | FULL REPORT |
| SMP.5.11 | Crayola orders | AQL Level II: Critical 0, Major function 0.4, Major visual 1.5, Minor 4.0. | FULL REPORT |
| SMP.5.12 | Dayspring, Mary & Martha | AOQL 3.0%. | FULL REPORT |
| SMP.5.13 | 2D International/FOB orders | UK/HCA/Netherlands: AOQL 3.0%. Nihon JP: AOQL 1.5%; Nihon non-JP: AOQL 3.0%. Walmart FOB 2D: AQL Level I, Critical 0, Major 1.5, Minor 4.0. | FULL REPORT |
| SMP.5.14 | Cracker component / Cracker | Component: AQL Level II, Critical 0, Major 1.0, Minor 2.5. Cracker itself: AQL Level II, Critical 0, Major 1.5, Minor 4.0, Total 4.0. Also must follow Cracker/Module E inspection guidelines. | FULL REPORT |
| SMP.5.15 | 3D International/FOB orders | Follow the product specification for inspection standard/sampling plan. | FULL REPORT |
| SMP.5.16 | Inspection lot size (general rule) | Follow the guideline in the spec if applicable. If not specified: double sampling plan → each lot ≤ 50k; single sampling plan → refer to Hallmark Inspection Manual tables (pages 4–5). | FULL REPORT |
| SMP.5.17 | Sampling plan responsibility matrix (party-dependent) | HMK inspector: single for HA, double for non-HA. Supplier/CQS/SEP inspectors/HMK inspection agents: always single (HA and non-HA). QIMA inspector: single for 2D HA, 3D HA, and 3D non-HA; double for 2D non-HA. | FULL REPORT |
| SMP.5.18 | Keepsake (KPSK) inspection type | Always refer to the inspection type under "Keepsake (KPS)" for Hallmark Ornaments/Keepsake items — do not use a generic 3D non-food category. | FULL REPORT |

### 5.2 AOQL identification method

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SMP.5.19 | Method 1 — IRF/Spec lookup | Check the IRF for the AOQL standard per SKU; cross-check the product spec's "Testing and Inspection" page for the visual standard/AOQL. | FULL REPORT |
| SMP.5.20 | Method 2 — SAP Group # lookup | Refer to GI document "QIMAone_Hallmark (HMK) Inspection Type and Inspection Workflow Decision Matrix." Look up the SAP Group # (HMK #) on the "HMK SAP Group # and AOQL%" sheet to get the AOQL%. | FULL REPORT |
| SMP.5.21 | Multiple specs in one report | Always refer to the spec with the SAME SAP Group # (HMK #) as the order to determine Inspection Type/AOQL%. Also check price and UPC# info for the Child SKU at the same time. | FULL REPORT |
| SMP.5.22 | PDQ lot-size calculation | When product/order qty is in PDQ, calculate the retail-unit quantity and sample based on the retail LOT size. Example: 5378 PDQ × 72 retail units/PDQ = 387,216 pcs lot size (not 5,378 PDQ). | FULL REPORT |
| SMP.5.23 | Quantity unit in report (CTN vs PCS) | Check the "Qty of inspection lot" unit in the IRF (CTN or PCS). Produced/packed quantity units must be consistent with the PO. If unit is carton, report the carton figures, not the converted piece figures — retail quantity can be remarked separately if needed. | FULL REPORT |
| SMP.5.24 | Product Integrity Notes | Inspector must review Product Spec/Product Detail "Product Integrity Notes" and inspect per its content. Any discrepancy → fail the corresponding checkpoint and add a remark. | FULL REPORT |

### 5.3 Sampling plan matrices (detailed rules)

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SMP.5.25 | HA items (2D & 3D) | Always use Single Sampling Plan. | SECTION |
| SMP.5.26 | 3D products (any HA status) | Always use Single Sampling Plan. | SECTION |
| SMP.5.27 | 2D non-HA products | Packing-method dependent: mixed-packed → Single; individually packed → Double. *(see ⚠️ TO CONFIRM, Section 0)* | FULL REPORT |
| SMP.5.28 | Sampling unit | Always use the Market Sale Unit (retail unit) as the sampling unit; confirm with SIC if unsure. | QUESTION |
| SMP.5.29 | Double sampling — 2nd sample trigger | 2nd sample needed only when visual defect qty is between the Accept and Reject numbers of the Double Sampling Plan. If report already failed for another section (test/packing), overall result is Fail and 2nd sampling is NOT required. Inspector may pull 1st+2nd sample sizes together to save time; revise sample size in IAPP to reflect the total if 2nd sampling proceeds. | SECTION |
| SMP.5.30 | Visual sample size examples (reference only) | AOQL 3.0% double: 1st sample 30 pcs (Accept 0/Reject 5), 2nd sample 60 pcs (Accept 4/Reject 5 combined). AOQL 5.0% (Good Bags) double: 1st sample 20 (Accept 0/Reject 6), 2nd 60 (Accept 5/Reject 6 combined). Single sampling AOQL 3.0%, lot 5001–10000 → sample size 105. | SECTION |

---

## 6. Specifications, DAS/VAS, Labels & Packaging

### 6.1 Approval sample (DAS/VAS)

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SPEC.6.1 | Approval sample presence & ID | Confirm presence in factory; identify via signature/seal/comparison to booking picture/special marking. If not present → proceed and clearly remark in report. | QUESTION |
| SPEC.6.2 | DAS + Spec combined use | Inspector must use DAS and Specs together; pay close attention to bulk vs. DAS comparison. | FULL REPORT |

### 6.2 Shipping marks / carton labeling — general categories

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SPEC.6.3 | Side mark scenarios | Two scenarios: (1) Side mark for Canada/USA, (2) Side mark for international (excl. Canada/USA) — content must match the respective template. | SECTION |
| SPEC.6.4 | Reuse # calculation | Measure carton inside dimensions (L/W/D in inches). Max cubic = (L+0.5)(W+0.5)(D+0.5); Min cubic = (L-0.5)(W-0.5)(D-0.5). Value must fall within this range to be acceptable. Explanatory yellow text is not to be printed on the carton. | SECTION |
| SPEC.6.5 | Shipping mark color/font | Ship marking color is always BLACK regardless of wholesale quantity (including "wholesale as shipper" case = qty 1). Do NOT partially fill a wholesale box. Font ≈13mm (0.5") tall bold text; downsize only if carton size doesn't permit. | SECTION |
| SPEC.6.6 | Shipmark template | Must follow the latest shipmark template ("Asia Carton Print-rev 121917" from Hallmark Document Library) — content: NET/GROSS WEIGHT, DIMENSIONS, CARTON NUM, HALLMARK MARKETING COMPANY LLC, REUSE #, MADE IN. | SECTION |
| SPEC.6.7 | Shipper min/max size & weight (Hallmark general, updated 2025.08.27) | Min O.D.: L12"xW8"xD5" (305x203x127mm); Max O.D.: L22"xW21"xD32" (559x533x813mm); Min weight 5 lbs; Max weight 50 lbs. (M&S and Dayspring use other standards — see below.) | SECTION |
| SPEC.6.8 | Walgreens FOB carton | Max L48"xW40"xH/D46" (121.9x101.6x116.8cm), 50 lbs (22.68kg); no minimum limit to consider. | SECTION |
| SPEC.6.9 | International orders (excl. Canada) — end panel content | PO NUMBER, Stock No., Description, Qty, Net/Gross weight, Dimensions, Vendor ID, Prod. Date (MMYY date code), Made in, REUSE#. Font: 19mm (0.75") bold for PO#/SKU, 13mm (0.5") bold for other info. Side panel 1 = Hallmark crown logo; side panel 2 = shipping address. | SECTION |
| SPEC.6.10 | Barcoded shipper (corner) label — when required | Required for finished products shipped to Hallmark warehouses in US/Canada only. NOT required for: sales samples, components, and international orders (excluding Canada). | SECTION |
| SPEC.6.11 | Corner label position | Placed on right-bottom corner of the shipper side bearing the crown logo; distance from bottom of label to bottom of shipper = 1"–3". Label must wrap around two adjacent panels, visible from both side and end panels; bottom must be within ±15° of parallel with carton bottom. | SECTION |
| SPEC.6.12 | Tall box corner label | If carton >22" tall OR depth > 2× width → "tall box": lay box down with top flaps to the right, place label on lower-right corner of the side panel. | SECTION |
| SPEC.6.13 | Corner label content — scan format | SKU# scanning result must be in 4-3-4 digit format (pad with leading zeros; add space(s) after letters to make the middle segment 3 digits). Examples: SKU 399EGC1255 → scans as 0399EGC1255; SKU 99TM2024 → 0099TM 2024 (space between M and 2); SKU 150B12J → 0150B  012J; SKU A8B → 0000A  008B. | FULL REPORT |
| SPEC.6.14 | Corner label content — Whsle Qty | "Whsle QTY" on the label = wholesale quantity **inside the shipping carton** (NOT retail quantity). | SECTION |
| SPEC.6.15 | Corner label content fields | Stock number (SAP Material Number on top, Material/SKU number at bottom — 11-digit code, no international suffix printed); Material Description must match PO/spec; Wholesale Quantity (4-digit); Partial Quantity (blank or zero); Destination (per PO); Date code (MMYY, cannot be later than shipping month); Vendor ID (prefer GS code, else VN code); Canada Price (optional, blank acceptable). | FULL REPORT |
| SPEC.6.16 | Made In field | US-produced: "US" + 2-digit USPS state code (e.g., USKS). Non-US: 2-letter country/region code (CN, VN, TH, ID, IN, LK, MY, MX, etc.), 10-point font. Must represent actual production location. | SECTION |
| SPEC.6.17 | Barcode scanning of corner label | 4 barcodes on label: 2 longer (right) = Material Number/SKU; 2 shorter (left) = wholesale quantity. Barcode must be clearly readable (grade C or above; HCA orders require grade B or above). Only one label per lot needs detailed inspection; if it fails (wrong info or poor print), record as a shipper packing defect. | SECTION |
| SPEC.6.18 | Corner label minor correction | Non-barcode info errors (destination code, date code, vendor ID, country of origin) may be corrected with a small overlay label or reprint. Barcode information errors cannot be corrected this way. | SECTION |

### 6.3 Dayspring-specific labeling

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SPEC.6.19 | Dayspring shipping mark | Font ≈13mm (0.5") bold. Item No. = UPC code minus first & last digit, 10 digits (e.g. 8198376958). Template (rev. April 2025) removed the "Case Count: xx of xxx" line. | SECTION |
| SPEC.6.20 | Dayspring carton label | 4"x4" label, 1 per carton, top-right corner of long side. Must include: Dayspring item number (1" font, scannable UPC), Prime item number, Carton Quantity, Description of Merchandise, Date of mfg. Generated via https://retailer.dayspring.com/vendor. Barcode format: E0000 + 8-digit item# = shows as "E0000088198362631" (10-digit Item# + 6-digit Qty encoding). | SECTION |
| SPEC.6.21 | Dayspring branding | Must use official logo files (Illustrator/PDF); do NOT distort logo non-uniformly. | QUESTION |
| SPEC.6.22 | Dayspring/Mary & Martha carton max size/weight | Max dimensions: 24" (609mm) Tall x 24" (609mm) Width x 14.5" (368mm) Length/Deep; Max weight 30 lbs (13.6kg) — revised 07/06/2022 (previously 35 lbs). | SECTION |

### 6.4 Fragile / Partially Filled Carton labels

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SPEC.6.23 | Fragile label — when required | Recommended for easily broken items (ceramic, glass frame, FRP, etc.). If missing, inspector should point it out (label or printed marking acceptable). Symbol placed 31mm from top flap score and 31mm from corner score; symbol size 75mm tall. | QUESTION |
| SPEC.6.24 | Carton drop test trigger | Required if: HMK ENG special request in spec; ceramic & glass products; any product dimension >16" (40.64cm); item failed ship test at HMK DG lab more than once; any packaging shows a fragile note/icon/sign. Mandatory for all SKUs marked fragile even if not in the spec, unless Hallmark issues a waiver. | FULL REPORT |
| SPEC.6.25 | Partially Filled Carton (PFC) definition | PFC = carton with less than the stated wholesale quantity (usually the last carton). Must have 2 separately-printed PFC labels (not manually amended) applied to two opposite corners; carton label must be reprinted (not manually amended) to reflect actual wholesale quantity and correctly scan. No filler material from empty wholesale/retail boxes — clean corrugate/Kraft paper only. Only ONE PFC allowed per PO per shipment (the last carton#). | SECTION |
| SPEC.6.26 | PFC label specs | Orange background PMS 1505C, white lettering, "PARTIALLY FILLED CARTON," 15mm bold face, size 5"x2", self-adhesive. Do NOT use RED or GREEN (reserved for Customs). Position: normal shipper — width/opposition edge, 5" from corner, 1–3" from bottom; tall box — depth-middle/opposite edge. | SECTION |
| SPEC.6.27 | Overage tolerance (Hallmark AU) | Delivery of +3%/-0% of PO quantity allowed for Everyday programs; 0%/0% (no variance) for Seasonal programs. | FULL REPORT |

### 6.5 Wholesale / retail packaging labels

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SPEC.6.28 | Wholesale label content (standard US/Canada format) | (1) SAP Material number, (2) Product description, (3&4) Wholesale package qty, (5&6) Material/SKU number (11 digits), (7) Partial qty (blank/zero), (8) Destination (first 4 digits), (9) Date code, (10) Vendor ID, (11) PO#, (12) Made in. | FULL REPORT |
| SPEC.6.29 | Wholesale label — when NOT required | If product shipped directly to customer (not via Hallmark DC): label not required if (a) unit count easily countable without opening wholesale film, or (b) stock number clearly visible. Additional requirements for film/polybag wholesales (rev. Aug 2019): stock number ≥3mm (1/8") tall AND clearly visible through film; retail count visible through film; Retail UPC visible & scannable through film/polybag. | SECTION |
| SPEC.6.30 | Wholesale label size/color/placement | Size: 3.25"x1.125" (83x29mm) — or per SKU spec if specified. Color: black on white. Position: smallest side panel of the wholesale unit (or front/top if impractical); never place on the sealing area. | SECTION |
| SPEC.6.31 | Wholesale label — Hallmark DC-routed shipments (new guideline, rev. June 2022) | If shipped through Hallmark DC then onward: follow new guideline — layout consistent within product category, stock number most prominent (top), size 2.625"x1.69" (67x43mm), black print, min type size 0.25"(6mm) for stock number via inkjet (else 0.125"/3mm min), UPC must match retail label's contrast/format/size. | SECTION |
| SPEC.6.32 | Country of Origin wording | "Made In" (not "Produced In") on retail product & packaging for all NA POs (effective June 2015). UNICEF, International, M&S, Crayola keep their existing wording unchanged. | SECTION |
| SPEC.6.33 | Wholesale Packaging for Hallmark Australia | Sealed LDPE (≥30% recycled) bag, clear stock number, readable barcode; bag material may be 40 micron/1.5 mil; label min size 3¼"x1⅛" (83x29mm), black on white, placed for visibility (near Hallmark logo if non-pack); multiples of 5 preferred unless specified; label not required if unit count easily countable and stock number visible. | SECTION |
| SPEC.6.34 | 1FB Inner Carton Box/Tray (Hallmark AU) | Size 420(L)x170(H)x205(W)mm, tolerance +0/-2mm; single-wall corrugated; snap-out tray design; 2 x 1FB packed per outer carton; used for Single Cards/Gift Tags unless specified otherwise. | SECTION |
| SPEC.6.35 | 1FB Label (Hallmark AU) | Includes PO number, "INNER" wording top-middle, stock number, wholesale unit quantity; size 100x150mm; pressure-sensitive permanent label; black print; placed on back panel of tray. | SECTION |
| SPEC.6.36 | Shipping carton requirements (Hallmark AU) | 2FB carton holds 2x1FB (≈445x355x230mm double wall); various standard shipper sizes per product type (flat wrap, gift bags, XL gift bags, Gifting 3D); max gross weight 12kg (15kg for tag-on orders). One stock number per carton — do not mix. Hot-melt seal + 2" clear tape, no steel strapping. | SECTION |
| SPEC.6.37 | Retail singles (Hallmark AU) | Retail singles will not be accepted/received — only complete wholesale units placed in cartons. | SECTION |
| SPEC.6.38 | Polybag warning statement (general) | Required unless opening width <5" (12.7cm) flat, or it's a wholesale-only polybag (never reaches consumer). Must include English, French, and Spanish (if required) suffocation warning, repeated every 18". "WARNING"/"CAUTION" in all caps only (≥4mm letter height); other text not required in all caps. Print size scales with bag size (60"+ → 24pt; 40-59" → 18pt; 25-39" → 14pt; <25" → 10pt). Material mostly PE; thickness >1 mil (0.0254mm) unless BU-specific rule differs; toys must also comply with ASTM F963 §4.12. | SECTION |
| SPEC.6.39 | Product logo checkpoint | Verify inspector's Pass/Fail/N/A result is consistent with what's visible in report photos — logos can appear in non-obvious locations; do not accept N/A/no-logo without photographic evidence of absence. | FULL REPORT |
| SPEC.6.40 | PID Number check (2D only) | PID = display board on card items. Select N/A only if the product genuinely has no such display board. | SECTION |
| SPEC.6.41 | Warning Statement and License checkpoint | Verify copyright info on retail package conforms to spec and DAS before selecting Pass. | FULL REPORT |
| SPEC.6.42 | Client/Destination selection | Lung Cheong (Indonesia), Starlite (Malaysia), PT IGP suppliers → always select "KC HKBO." Hallmark-brand orders shipping to USA → "KC HKBO." Costco/Walmart/Walgreens/QVC etc. orders → select the specific retailer name. | QUESTION |
| SPEC.6.43 | Reece's Law check (button-cell battery items) | Applicable ONLY to items with button cell battery shipping to US/Canada. Select "Mark as N/A" for items without button cell battery or non-US/Canada destination. Not applicable to Keepsake 2024 products. Does not apply to toys for children under 14 compliant with the Toy Standard. Both product and retail packaging must show visible warning statements (exception: heavy embossed/textured product will not have a product marking). | SECTION |
| SPEC.6.44 | Color accuracy — CMYK (PressSIGN Report) | Result should be ≥90%; if below, remark in report. | QUESTION |
| SPEC.6.45 | Color accuracy — PMS/Delta E | Delta E should be ≤2 (solid color only). If >2, check with SIC for instruction. If factory lacks a Delta E device, request their own test record. If inspector has doubts, remark and fail the color check. | QUESTION |

---

## 7. Product Measurements / POMs

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| MEAS.7.1 | M&S and Dayspring products | Refer to the Hallmark Inspection Manual for measurement questions. No AQL for measurement — only 1 pc (retail sample) is measured and recorded; noticeable difference → report with a failure remark. | FULL REPORT |
| MEAS.7.2 | Paper bags | Must measure handle length and remark in the report. | QUESTION |
| MEAS.7.3 | Products with components | Must weigh the component as well. | QUESTION |

---

## 8. Tests

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| TST.8.1 | Visual batch check — Card Items | Sample size e.g. 30 pcs: 1 pc checked against DAS for full compliance; remaining 29 pcs use batch-checking method. | SECTION |
| TST.8.2 | Visual batch check — Boxed Cards | Batch check for visual; check ALL pieces for functional check (no missing cards/envelopes, no mix-ups, correct qty). Envelope sealing function test: 10 pcs per inspection lot. | SECTION |
| TST.8.3 | Visual batch check — Handle Bags | Batch check for visual; check ALL pieces for functional check (pull/check handle strength, open each bag to review construction/gluing/visual inside). | SECTION |
| TST.8.4 | Abuse test (pull test, glue joint test) | Sample must be selected from bulk SEPARATELY, not pulled from the visual-check samples. | SECTION |
| TST.8.5 | Color Accuracy Check (Delta E concern) | If Delta E variance is a concern between DAS and production, include photos of color target Lab value and Delta E reading against the target (e.g. PMS Pantone from spectrometer's digital library). | QUESTION |
| TST.8.6 | Pull Test | If no pull tester onsite, inspector may DIY one using measured dead weight (e.g. 2/3/5 lbs via hook/clip). Test must not be skipped; remark that a DIY Weight Pull Tester was used. | QUESTION |
| TST.8.7 | Functional Test acceptance | If functional defect qty >50% of Acceptance quantity (C#), fail the Functional Test and remark. Accept functional defect qty ≤ C#/2; for >C#/2, send to PE for final decision. | SECTION |
| TST.8.8 | UPC Scan Test | AU orders require grade B or above (else check supplier's scanner). Special barcode scanner required (or "Barcode Scanner" app + inspector sends PDF/image to QIMA DG lab). Results table: Pass ≥90%/grade A(>0.62); Warning zone 75–89%/grade C(≥0.25); Fail <75%/grade D(<0.25). If result Pass → insert scan photos. If Fail → fail checkpoint + seal 1 barcode sticker per version for further testing (or fail + remark if no seal possible). If result unavailable before inspector leaves → rate Fail with remark, update later with lab result. | SECTION |
| TST.8.9 | UPC test sample size | Shipper carton: 1 carton, scan every corner label barcode. Retail package: Greetings/Print Specialty/Gift/Ornament = 1 pc; International/Crayola/Marks & Spencer = 10 pcs. | QUESTION |
| TST.8.10 | UPC scan procedure | Laser gun ~6" from UPC, held at 5° perpendicular angle, trigger held 3 sec (top-to-bottom scan), push enter until DECODE%/DECODABILITY% shown; if bad scan, do not record — rescan. Retail box extra price barcode: use Barcode Scanner app; result Pass only if info appears under "Metadata." | QUESTION |
| TST.8.11 | UPC scan pass criterion (7-of-10 rule) | If 7 or more of 10 scans are acceptable (grade C or above), overall result = Pass; otherwise Fail. | SECTION |
| TST.8.12 | Carton Drop Test | Required per triggers in SPEC.6.24. Sample: wholesale boxes fill 50–85% of shipper; ≥12 retails but no more than 3 shippers. Report any breakage to the responsible HMK Engineer for final decision. Not required for subsequent lots if 1st lot passed. | FULL REPORT |
| TST.8.13 | Grammage/Paper weight test | GSM meter on 5 samples; compare to factory-provided paper weight test report. Tolerance: label claim ±5%. | FULL REPORT |
| TST.8.14 | FHSA test (electrical function items only) | Test 5 samples for: Working current <200mA; Standby current <10µA; Voltage (per factory-supplied batteries); dB 75–85 for keepsake. Ask factory for "Battery Powered Product Evaluation Report"; acceptance standard not exceeding 10%. Record in the required format with photo evidence in IAPP. | FULL REPORT |
| TST.8.15 | Adhesion Tape Test (non-paper products w/coating) | 3M #810 tape applied to coated/painted surface, rest 1 min, remove rapidly. Acceptable if no visual effect. Exception for glass/ceramic décor not intended for handling in coated area: up to 25% coating removal acceptable. Not required for fabric/plush items or products not managed by Gift Presentation & Package Expressions BU. | QUESTION |
| TST.8.16 | Envelope Seal (20-min) Function Test | Scope: Hallmark UK, HCA (Hallmark Australia), M&S only. Sample: 10 envelopes. Procedure: insert card, moisten adhesive strip, close flap, slide finger once, wait 20 min, open. Pass = fiber pull detected. Fail = flap opens early or no fiber pull after 20 min. | QUESTION |
| TST.8.17 | Test instructions fallback | If inspector doesn't understand how to perform a test, follow the SR or FR report's instructions. For all onsite tests: if failed, reflect the number of failed pieces in remarks; if passed, no comment required. | QUESTION |
| TST.8.18 | Function test — general reminder | Check function for all inspected samples (1-2 cycles); report issues under appearance/workmanship section. Functional defect = impacts designed product function (electronic or mechanical), rendering the product unsellable — clarify with HMK engineer if unclear. | QUESTION |
| TST.8.19 | Function test sample size | 25 test attempts per specs; sample size follows FR protocol (FR KPS, Greeting Cards, Houseware Food/Non-food → function test sample size = 1). | FULL REPORT |

---

## 9. Workmanship Defects

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| WM.9.1 | No defect found | Select "no defect found" from the public defect list. | QUESTION |
| WM.9.2 | Tea Towel defect variances | Refer to "1SNN1015 Tea Towel defects variances SG feedback" for accepted variances. | QUESTION |
| WM.9.3 | Felt ornament visual standard | Shape/width/thickness variation acceptable if item remains recognizable; facial features may vary if symmetrical and proportionate; design feature placement may vary; wholesale variation acceptable (no two identical). Minor print defect <5mm — no need to report UNLESS it affects sellability (then classify as Major). | QUESTION |
| WM.9.4 | Box cards / set products | Count only 1 defect per box or set (not per individual card). | QUESTION |
| WM.9.5 | Acceptable defect — dirt marks (kraft recycled paper) | Dirt marks on kraft recycled paper material acceptable if no glue residue penetrated the bag surface — no need to record. | QUESTION |
| WM.9.6 | MAJOR defect photo requirement | 2 photos required per Major defect (global view + close view). | QUESTION |
| WM.9.7 | Critical defects (zero tolerance) | Not accepted: Animal Fur; Human Hair or body fluid (e.g. blood); Insect/Insect Debris/Animal Debris; Mold on packaging or product; Sharp Tools (cutter, needle, scissor, etc.). Client may accept some functional sharp points/edges — clarify with SIC if needed. PE decides on potential risk for sharp point/edge/small parts. | QUESTION |
| WM.9.8 | Major defect classification | Refer to client defect visual standard and HQR to rate defects; follow the "golden rule" if no matching example exists in the visual standard. Defects affecting sellability = Major. Doubt on MIN/MAJ classification → check with back office. | FULL REPORT |
| WM.9.9 | Minor defects under AOQL inspections | Minor defects are NOT allowed under AOQL inspections — any apparent Minor defect must be reclassified as Major. Exception: plush items apply AOQL 1.5% Major / AOQL 4.0% Minor (Minor allowed here). | SECTION |
| WM.9.10 | Defect photo caption | For defects >1cm, describe length/area accurately in the caption and place a ruler next to the defect in the photo. | QUESTION |
| WM.9.11 | Test/Functional/Critical acceptable qty (Manual detail) | Functional defect acceptance ≤ C#/2 (else PE decision); 0 (zero) critical defects accepted. | SECTION |

---

## 10. Report Writing Rules (Photos, Comments, Remarks)

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| RPT.10.1 | Inspector's Remark section | Must never be left empty; follow the standard 5-line format: (1) QIMA order number, (2) Inspector name, (3) which test/spec documents the factory provided onsite, (4) sample repacking note, (5) sampling method/carton count. | QUESTION |
| RPT.10.2 | Picture orientation | Landscape, not portrait. | QUESTION |
| RPT.10.3 | Picture description | Every picture field must have a description/caption. | QUESTION |
| RPT.10.4 | Date format | Date-Month-Year (e.g., 17-July-2020). | QUESTION |
| RPT.10.5 | Report cover photo | 1 photo required. | QUESTION |
| RPT.10.6 | Carton/Shipper photos | ~3 photos: 45° view (corner label position + shipping mark), close-up of corner label detail (both sides, ideally one photo), photo showing total wholesale count (easily countable). | SECTION |
| RPT.10.7 | Wholesale package photos | ~2 photos: side view of wholesale label/marking, photo showing retail count per wholesale (easily countable). | SECTION |
| RPT.10.8 | Retail package photos | ~3 photos: front view, back view, photo clearly showing retail labeling. (Skip duplication if already covered in DAS check photos.) | SECTION |
| RPT.10.9 | DAS check photos | ~8-10 photos, DAS and production sample need to be in the SAME photo: front/back/bottom view of retail package; front/back/left/right/top/bottom view of product (as applicable); 1 photo of 4-6 products together for consistency review. | SECTION |
| RPT.10.10 | Testing photos | Pull test (hanger/component): no photo unless failed (then remark pull-off force data). UPC test: 4 photos on corner label + 1 on retail package. Adhesive tape test: no photo unless failed. Grammage paper weight: photo required + actual measurement data remarked. Envelope seal test: 1 photo to show the tested sample (tearing areas) if applicable. Other tests required per FR protocol: remark test names in comment field, insert 1 photo for each test. For plush item: photos to show test force diagram and test data. | SECTION |
| RPT.10.11 | Measurement section | Record measuring results/data in report; insert measurement photos with remark if measurement fails. | SECTION |
| RPT.10.12 | Workmanship defect photos | Insert photos based on actual defects found. | SECTION |
| RPT.10.13 | Re-inspection reports | Must make sure there is an inspection reason at the head of the report. | QUESTION |
| RPT.10.14 | HA/HCLP communication note | Please make sure the inspector advises if they have communicated with back office. | QUESTION |
| RPT.10.15 | No combining inspection reports | Inspector must NOT combine inspection reports (Hallmark required inspection report will be issued by SKU and inspection lot) unless Hallmark confirms to do so. | QUESTION |
| RPT.10.16 | Shipper packaging picture composability | Photo must make it easy to count wholesale quantity (e.g., 2 columns x 4 rows x 3 layers = 24). | QUESTION |
| RPT.10.17 | Wholesale packaging picture composability | Photo must make it easy to count retail quantity. | QUESTION |
| RPT.10.18 | Packaging comment template | For Shipper/Wholesale/Retail packaging sections, if no inconsistency found, use exact template: "Conform to Specs, PO and approved ship test report." | QUESTION |
| RPT.10.19 | Quantity/Sampling count field (QIMAone) | "Defect sampling level & AQL" input must be the Acceptance Number (NOT the workmanship defect count found). | SECTION |
| RPT.10.20 | Golden report review | Inspector should review the golden report (attached to Inspector GI) before writing the QIMAone report. | QUESTION |

---

## 11. QIMAone Platform / Workflow Setup

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| PLT.11.1 | Search / selection | Search by SKU (Product Reference) or PO Number (only the portion before "+"). QTY of the selected project must be the **Order PO QTY** (from the PO attachment "Purchase Order Chance"), NOT a generic "order QTY" field elsewhere. | FULL REPORT |
| PLT.11.2 | Inspection Type selection | Always chosen based on the Specifications attached to the order — the SAP Group# (HMK#) on the spec must match the order. Single Sampling → Lot size = available quantity in factory. Double Sampling → no lot size required. If unsure, contact back office. | FULL REPORT |
| PLT.11.3 | Workflow selection | Only select workflows under Type "SP" (Self Picking); search using keyword "HMK –"; refer to the workflow decision matrix; contact back office if unclear. | FULL REPORT |
| PLT.11.4 | Report finalization | "COMPLETE MY INSPECTION" should only be clicked when inspection is genuinely finished — report becomes inaccessible afterward. | QUESTION |

---

## 12. Summary / Inspection Remarks — cross-checks

| ID | Field/Location | What to check | Scope |
|---|---|---|---|
| SUM.12.1 | Negative responses require explanation | Every "No"/"Failed"/anomaly recorded anywhere in the report must have a corresponding explanation in the Inspector's Remark / Summary Review. | FULL REPORT |
| SUM.12.2 | HA/HCLP disclosure | If item is HA or HCLP, the summary/remarks must reflect this and confirm back-office communication occurred. | FULL REPORT |

---

## 13. Ambiguous or incomplete rules (cannot be written as a rule entry)

- Repeated references to "cf photo 1," "cf picture 3," etc. point to images that were provided directly alongside the text (incorporated inline where relevant) — no items remain unresolved on this front.
- The Hallmark Inspection Manual page-specific references (wholesale/retail package and polybag details) were provided and have been incorporated above. No gaps identified.
- Reference to the file **"QIMAone_Hallmark (HMK) Inspection Type and Inspection Workflow Decision Matrix"** (an Excel workbook) is used repeatedly as the authoritative source for SAP Group#/AOQL% and workflow lookup, but the workbook itself was not provided as an attachment — only screenshots of specific rows (HMK9725 → 3.00%). Full workbook content beyond those rows cannot be verified and should be treated as an external reference, not reproduced here.
- **"Golden Report" (Hallmark UK – Golden QIMAone Report.pdf)**, referenced as an annotated-report source, was not provided — its annotations could not be converted into rule entries. If supplied later, each annotation should become a rule entry (bad example → Error example, correct behavior → Correct example).
- **Tea Towel defects variances file (1SNN1015)** and **Felt ornament variation file** referenced in Section 9 were not provided as attachments — only the summarized guidance was captured (WM.9.3, and the reference note under WM.9.2).

---

## 14. Do-not-flag — client-specific notes

- Minor print defects under 5mm on felt ornaments — acceptable unless they affect sellability.
- Dirt marks on kraft recycled paper products, provided no glue residue has penetrated the bag surface.
- Minor defects recorded under standard (non-plush) AOQL inspections should NOT exist as "Minor" — if found, this is itself an error (see WM.9.9), not a do-not-flag case.
- N/A on Reece's Law checkpoint for items without button-cell battery, non-US/Canada destination, or Keepsake 2024 products.
- N/A on HA/HCLP checkpoints for orders not shipped to Kansas City.
- N/A on PID Number checkpoint for products with no display board (2D only checkpoint).
- Blank Canada Price field on wholesale label when no Canadian Material Number exists on the PO.
- Missing wholesale label when the film/polybag conditions (countable units, visible stock number, visible/scannable UPC) are all met.
