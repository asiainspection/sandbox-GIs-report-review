# Joseph Ribkoff — GI checks

Golden Report QIMA1–16 + old GI rules not covered by those comments.  
Blank **when** = always. **param** only when Action needs it.

Companion: `harness_actions.md` · `harness_where.md` · `harness_compile_prompt.md`

---

# Part A — Golden Report (QIMA1–16)

## QIMA1 — Inspection location address

**id:** A.1.1  
**check:** Factory address should include the complete factory address and postal code  
**where:** Factory address  
**action:** LLM yes/no  
**param:** Does this address include street/building, city, country, and a postal/zip code?  
**example:** Wrong: missing postal code 

**id:** A.1.2  
**check:** Factory address should be in English (no Chinese)  
**where:** Factory address  
**action:** is in English  
**example:** Wrong: Chinese characters · Right: English only

---

## QIMA2 — Inspector remark / defects by PO

**id:** A.2.1  
**check:** Inspector remark should list all defects found broken down by PO number with a total defect %  
**where:** Inspector remark  
**action:** LLM yes/no  
**param:** Does this remark list defects broken down by PO number and include a total defect percentage?  
**when:** when defects are found  
**example:** Wrong: "3 defects found" · Right: "PO 081901: 3 defects … Total: 6.00%"

---

## QIMA3 — Workmanship defects

**id:** A.3.1  
**check:** Untrimmed threads longer than 1/4 inch should be classified MAJOR; shorter than 1/4 inch MINOR  
**where:** Defects  
**action:** needs vision  
**param:** For untrimmed-thread defects, is any thread longer than about 1/4 inch classified as MINOR?  
**when:** when untrimmed thread defects exist  
**example:** Wrong: 1/2 inch thread as MINOR · Right: over 1/4 inch as MAJOR

**id:** A.3.2  
**check:** All dirt/stain defects should be classified MAJOR  
**where:** Defects  
**action:** LLM yes/no  
**param:** Are all dirt or stain defects classified as MAJOR?  
**when:** when dirt or stain defects exist  

**id:** A.3.3  
**check:** All stitching defects should be classified MAJOR  
**where:** Defects  
**action:** LLM yes/no  
**param:** Are all stitching defects classified as MAJOR?  
**when:** when stitching defects exist  

**id:** A.3.4  
**check:** Each defect type should have at most 5 photos  
**where:** Defects photo count  
**action:** at most N photos  
**param:** 5  
**for each:** each defect  
**example:** Wrong: 20 photos for one defect name · Right: at most 5 photos  

**id:** A.3.5  
**check:** For multiple references or colors, only 1 photo per color should be added per defect  
**where:** Defects  
**action:** LLM yes/no  
**param:** When the same defect appears on multiple colors or references, is there at most 1 photo per color?  
**when:** when multiple colors or references have the same defect  

---

## QIMA4 — Specifications photos

**id:** A.4.1  
**check:** One photo is required for each specifications checkpoint; duplicated photos should be avoided  
**where:** Product Style & Construction photo count  
**action:** at least N photos  
**param:** 1  

**id:** A.4.2  
**check:** Outer packing photos should include boxes on pallets, seals, and labelling on the side of the boxes  
**where:** Outer Packing & Shipping Marks: Front & Side photo count  
**action:** at least N photos  
**param:** 3  
**example:** Wrong: front label only · Right: pallet + seal + side label

---

## QIMA5 — Carton drop test photos

**id:** A.5.1  
**check:** Carton-drop photos should not be included when the test passed; only include if the test fails  
**where:** Carton drop test photo count  
**action:** at most N photos  
**param:** 0  
**when:** when the drop test passed  
**example:** Wrong: drop photos on Pass · Right: no photos on Pass

---

## QIMA6 — Product logo

**id:** A.6.1  
**check:** Product logo should be checked carefully on samples including sewn-on trims; do not mark N/A or “no product logo” when a logo is present  
**where:** Product Logo result  
**action:** is one of  
**param:** PASS, FAIL, Pending  
**example:** Wrong: N/A when logo is on sewn-on trim · Right: Pass or Fail after check

---

## QIMA7 — Measuring boxes photos

**id:** A.7.1  
**check:** Photos of measuring the boxes should not be included  
**where:** Outer Packing: Assortment, Dimensions & Weight photo content  
**action:** needs vision  
**param:** Does any photo show a tape measure on the carton or measuring the boxes?  
**example:** Wrong: measuring-boxes photo · Right: no measuring photos

---

## QIMA8 — Labels grouped

**id:** A.8.1  
**check:** All hang tags and care labels should appear together under Product Labels  
**where:** Product Labels photo count  
**action:** at least N photos  
**param:** 1  
**example:** hang tags and care labels grouped in Product Labels, not scattered

---

## QIMA9 — Approval sample comparison

**id:** A.9.1  
**check:** Approval sample comparison should show on-site product vs approval sample side by side  
**where:** Approval Sample Comparison photo count  
**action:** at least N photos  
**param:** 1  

**id:** A.9.2  
**check:** Approval sample comparison should include a caption that identifies the approval sample  
**where:** Approval Sample Comparison photo caption  
**action:** LLM yes/no  
**param:** Does any caption identify which item is the approval sample?  

**id:** A.9.3  
**check:** Approval sample photos should clearly show the approval sample next to the bulk product  
**where:** Approval Sample Comparison photo content  
**action:** needs vision  
**param:** Does the photo show the approval sample next to the bulk product (e.g. green QIMA SAMPLE tag visible)?  

---

## QIMA10 — Product weight photos

**id:** A.10.1  
**check:** Product weight photos should not appear under Product Dimensions Result  
**where:** Product Dimensions Result photo content  
**action:** needs vision  
**param:** Does any photo show a weight scale or product-weight reading?  

---

## QIMA11 — Measurement chart content

**id:** A.11.1  
**check:** SKU number in the measurement file should match the product description / style in the report  
**where:** Product Dimensions Result file name  
**action:** manual review  
**example:** Wrong: 261838 written instead of 261938  

**id:** A.11.2  
**check:** All out-of-tolerance values in the measurement file should be highlighted  
**where:** Product Dimensions Result file content  
**action:** manual review  

**id:** A.11.3  
**check:** POM out-of-tolerance calculation should include the +/- 1/8" tolerance; if beyond that, measurement should fail or out-of-tolerance count should be written  
**where:** Product Dimensions Result file content  
**action:** manual review  

---

## QIMA12 — Test photos

**id:** A.12.1  
**check:** Each test in the checklist should include only one photo; avoid multiple photos per test  
**where:** Zipper test photo count  
**action:** at most N photos  
**param:** 1  

**id:** A.12.2  
**check:** Failed tests should provide only one photo per failure  
**where:** Zipper test photo count  
**action:** at most N photos  
**param:** 1  
**when:** when the test failed  

---

## QIMA13 — Stitch density

**id:** A.13.1  
**check:** Stitch density should state the stitches-per-inch count clearly  
**where:** Stitch density check comment  
**action:** LLM yes/no  
**param:** Does this comment state a stitches-per-inch count?  
**example:** Wrong: no count · Right: "42 stitches per inch"

**id:** A.13.2  
**check:** Stitch density photo should be from seam assembly, not from sewing on the main label  
**where:** Stitch density check photo content  
**action:** needs vision  
**param:** Is the stitch-count photo taken from a seam assembly (not the main label seam)?  

---

## QIMA14 — Ironing check photos

**id:** A.14.1  
**check:** Ironing check should show clear photos of the approval sample next to the bulk product  
**where:** Ironing, washing, treatment check photo count  
**action:** at least N photos  
**param:** 2  
**when:** Ironing, washing, treatment check result is one of PASS, FAIL
**example:** Wrong: bulk only · Right: approval sample + bulk sample

---

## QIMA15 — General pictures

**id:** A.15.1  
**check:** General pictures should not be added to the report  
**where:** All captions  
**action:** LLM yes/no  
**param:** Are all captions strictly related to the product inspection, with no general factory-exterior or environment shots?  
**example:** Wrong: factory exterior / general environment shots  

---

## QIMA16 — Measurement chart file

**id:** A.16.1  
**check:** Measurement attachment file name should be “Measurement Chart - style number”  
**where:** Product Dimensions Result file name  
**action:** filename matches  
**param:** Measurement Chart-{style}.xlsx  
**example:** Wrong: wrong template name · Right: "Measurement Chart - 261740.xlsx"

**id:** A.16.2  
**check:** Measurement chart should avoid typo errors (e.g. letters in numeric result cells)  
**where:** Product Dimensions Result file content  
**action:** manual review  
**example:** Wrong: letters in a result cell  
