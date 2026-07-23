"""Hand-authored, coherence-checked New Era GI authoring Excel.

Bindings verified against the real report checklist item names
(data/clients/new_era/corrected/*.json parsed via semantic_report) and the
golden report. Manual review is used ONLY where evidence is outside the report
(Advice List / Recap Quotation / Excel table content / on-site docs) or needs
human judgement (defect severity grading). Everything the report actually
contains is expressed as a deterministic or conditional check.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_gi_authoring_excel import build_workbook  # noqa: E402

OUT_XLSX = ROOT / "data/clients/new_era/gi_authoring_new_era.xlsx"

def R(id, section, rule, look, part, rtype, val="", when="", each="", ex=""):
    return {"id": id, "row_type": "Rule", "section": section, "rule": rule,
            "applies_when": when, "for_each": each, "look_at": look,
            "check_part": part, "rule_type": rtype, "value": val, "example": ex}

def C(id, rule, look, part, rtype, val):
    return {"id": id, "row_type": "Condition (hidden)", "section": "Conditions",
            "rule": rule, "applies_when": "", "for_each": "", "look_at": look,
            "check_part": part, "rule_type": rtype, "value": val, "example": ""}

rows = [
    # ---- Conditions (hidden) ----
    C("C1", "Inspection type is Pre-Shipment Inspection", "Inspection type", "", "Must equal", "Pre-Shipment Inspection"),
    C("C2", "No workmanship defect found", "Defect count", "", "Must equal", "0"),

    # ---- Section 1 – General Report Setup ----
    R("1.1.1", "Section 1 – General Report Setup",
      "For a PSI, goods must be at least 80% packed (100% finished & >=80% packed to proceed as standard PSI).",
      "Packed quantity", "", "Ratio at least", "0.8", when="@C1",
      ex="Wrong: 65% packed, submitted as standard PSI · Right: >=80% packed, or DUPRO remark added"),
    R("1.1.2", "Section 1 – General Report Setup",
      "Goods split across two nearby warehouses (3-4 km) is acceptable and needs no escalation.",
      "Inspector remark", "", "Manual review",
      ex="Wrong: flags 3km split as a problem · Right: proceeds normally"),
    R("1.2.1", "Section 1 – General Report Setup",
      "Inspector remark must state finished qty, packed qty, and packed ratio (regardless of result).",
      "Inspector remark", "", "AI yes/no (flag if false)",
      "Does this remark state the finished quantity, packed quantity, and packed ratio?",
      ex="Wrong: 'Inspection completed' · Right: 'finished and packed 61,355 pcs into 1,521 cartons 90%'"),
    R("1.2.2", "Section 1 – General Report Setup",
      "If a re-inspection, the remark must reference the original report number.",
      "Inspector remark", "", "Manual review",
      ex="Wrong: no reference · Right: 'This is re-inspection from R-Cloud-25083616'"),
    R("1.2.3", "Section 1 – General Report Setup",
      "Any out-of-tolerance measurement finding must be flagged in the first-page remark (measurement checkpoint is always N/A).",
      "Inspector remark", "", "Manual review",
      ex="Wrong: OOT only in attached Excel · Right: first-page remark notes the OOT finding"),

    # ---- Section 2 – Documents ----
    R("2.1.1", "Section 2 – Documents Recorded in the Report",
      "Mandatory pre-inspection docs (PO, spec, measurement sheet, packing list, factory address) provided on-site; if missing, remark it.",
      "Spec sheet", "", "Manual review",
      ex="Wrong: no packing list, not mentioned · Right: 'Packing list not provided on-site'"),
    R("2.1.2", "Section 2 – Documents Recorded in the Report",
      "AQL and sample size must match the Advice List for this booking.",
      "Booking", "", "Manual review",
      ex="Wrong: 500 pcs used vs Advice List 315 · Right: sample size matches Advice List"),
    R("2.2.1", "Section 2 – Documents Recorded in the Report",
      "Approval sample comparison must be done with supporting photos.",
      "Approval sample comparison", "photo count", "At least N", "1",
      ex="Wrong: checkpoint blank, no photos · Right: comparison done with photos"),

    # ---- Section 3 – Sampling, PO/MI & Carton Selection ----
    R("3.1.1", "Section 3 – Sampling, PO/MI & Carton Selection",
      "Random carton selection checkpoint must read PASSED.",
      "Random carton selection", "result", "Must equal", "PASSED",
      ex="Wrong: Passed with no detail · Right: PASSED with random selection detail"),
    R("3.2.1", "Section 3 – Sampling, PO/MI & Carton Selection",
      "MI selection count must match the Recap Quotation for the workmanship sample size.",
      "Booking", "", "Manual review",
      ex="Wrong: 15 MI for 800 pcs SS · Right: 25 MI per Recap Quotation"),
    R("3.2.2", "Section 3 – Sampling, PO/MI & Carton Selection",
      "Only the 8 largest-qty POs selected (14 if SS is 750/800 pcs).",
      "Booking", "", "Manual review",
      ex="Wrong: 6 POs for 750 pcs SS · Right: 14 POs selected"),
    R("3.2.3", "Section 3 – Sampling, PO/MI & Carton Selection",
      "Selection must match the Recap Quotation table (SS -> MI/PO/Shapes/MD).",
      "Booking", "", "Manual review",
      ex="Wrong: 500 pcs SS covers 2 MD · Right: 500 pcs -> 1 MD per table"),
    R("3.2.4", "Section 3 – Sampling, PO/MI & Carton Selection",
      "If Advice List flags NFL program, all 8 POs must come from the NFL PO list.",
      "Booking", "", "Manual review",
      ex="Wrong: 3 of 8 POs NFL · Right: all 8 POs NFL"),
    R("3.2.5", "Section 3 – Sampling, PO/MI & Carton Selection",
      "If client asked to prioritise specific POs, the remark must state the instruction was followed.",
      "Inspector remark", "", "Manual review",
      ex="Wrong: no indication · Right: 'Selected POs per client instruction'"),
    R("3.2.6", "Section 3 – Sampling, PO/MI & Carton Selection",
      "When a garment has >6 colors/artworks, the 6 selected must cover all product types.",
      "Spec sheet", "", "Manual review",
      ex="Wrong: 3 of 10 colorways, one silhouette · Right: 6 colorways covering all types"),

    # ---- Section 4 – Packaging ----
    R("4.1.1", "Section 4 – Packaging",
      "MI number in the defect table must match the Material field on the carton sticker.",
      "Defects", "", "Manual review",
      ex="Wrong: MI 70968082 vs different sticker · Right: MI matches carton label"),
    R("4.2.1", "Section 4 – Packaging",
      "If no workmanship defect is found, no package-deformation remark (e.g. 'Folding Issue') should appear.",
      "Inspector remark", "", "Must not contain text", "Folding Issue", when="@C2",
      ex="Wrong: 'Folding Issue' with 0 defects · Right: folding issue only when a defect is found"),

    # ---- Section 5 – Workmanship ----
    R("5.1.1", "Section 5 – Workmanship",
      "Caps graded per QA Manual (Rev 9.1); garments per NEC Apparel defect list.",
      "Defects", "", "Manual review",
      ex="Wrong: cap graded with apparel codes · Right: cap graded per QA Manual"),
    R("5.1.2", "Section 5 – Workmanship",
      "Cap defect severity must use 'Critical'/'Non-Critical', not Major/Minor.",
      "Full report text", "", "AI yes/no (flag if false)",
      "Does the defect table use 'Critical' and 'Non Critical' as severity labels, not 'Major' and 'Minor'?",
      ex="Wrong: Major/Minor headers on cap · Right: Critical/Non Critical"),
    R("5.1.3", "Section 5 – Workmanship",
      "Out-of-tolerance circumference on a cap must be a CRITICAL defect in the AQL table.",
      "Defects", "", "Manual review",
      ex="Wrong: 5 OOT caps, 0 Critical · Right: 5 Critical defects recorded"),
    R("5.1.4", "Section 5 – Workmanship",
      "A label >2mm off-center must be a MAJOR defect with clear photos.",
      "Defects", "", "Manual review",
      ex="Wrong: 3mm off-center not recorded · Right: MAJOR defect with photo"),
    R("5.1.5", "Section 5 – Workmanship",
      "If a defect recurs on 20+ pieces, inform back office/SIC; keep it in the AQL table regardless.",
      "SOP", "", "Manual review",
      ex="Wrong: defect on 25 pcs dropped · Right: kept in AQL table, back office consulted"),
    R("5.2.1", "Section 5 – Workmanship",
      "Defect counts under Workmanship must equal the totals in the attached Measurement Defect AQL Table.",
      "Defect count", "", "Manual review",
      ex="Wrong: body shows 10/0, Excel 14/21 · Right: counts match exactly"),
    R("5.2.2", "Section 5 – Workmanship",
      "Excel defect breakdown must include PO#, units/PO, silhouette, and MI style for every row.",
      "Defect Breakdown", "", "Manual review",
      ex="Wrong: 'Cap, 20 pcs' only · Right: 'PO#..., Cap, 20 pcs, MI 12274362'"),

    # ---- Section 6 – Tests and Measurements ----
    R("6.1.1", "Section 6 – Tests and Measurements",
      "Weight Check must never carry a pass/fail grade (result stays N/A or blank).",
      "Weight Check", "result", "Must be one of", "N/A, NO_RESULT",
      ex="Wrong: 'Pass' with weight value · Right: N/A, no specification"),
    R("6.1.2", "Section 6 – Tests and Measurements",
      "Fabric Weight Test (GSM) must never carry a pass/fail grade (result stays N/A or blank).",
      "Fabric Weight Test", "result", "Must be one of", "N/A, NO_RESULT",
      ex="Wrong: GSM value marked Pass · Right: N/A, no specification"),
    R("6.1.3", "Section 6 – Tests and Measurements",
      "Product Dimensions measurement must never carry a pass/fail grade (result stays N/A or blank).",
      "Product Dimensions Result", "result", "Must be one of", "N/A, NO_RESULT",
      ex="Wrong: measurement marked Fail · Right: N/A, OOT handled via remark"),
    R("6.2.1", "Section 6 – Tests and Measurements",
      "59FIFTY caps use special +/-0.3cm circumference tolerance; crown squared off.",
      "Spec sheet", "", "Manual review",
      ex="Wrong: graded at +/-0.5cm · Right: graded at +/-0.3cm"),
    R("6.2.2", "Section 6 – Tests and Measurements",
      "Measurement Defect AQL Table header fields (QIMA ref, shape, MI, PO, SS) must all be populated.",
      "Defect Breakdown", "", "Manual review",
      ex="Wrong: QIMA ref & PO blank · Right: all 5 header fields populated"),
    R("6.2.3", "Section 6 – Tests and Measurements",
      "Cap measurement sampling is always 60 pcs per man-day.",
      "Booking", "", "Manual review",
      ex="Wrong: 30 pcs across 2 shapes · Right: 60 pcs total"),
    R("6.2.4", "Section 6 – Tests and Measurements",
      "Out-of-tolerance garment measurement must be N/A with comment 'Subject to Client's Evaluation'.",
      "Product Dimensions Result", "comment", "Manual review",
      ex="Wrong: OOT, no comment · Right: N/A + 'Subject to Client's Evaluation'"),
    R("6.3.1", "Section 6 – Tests and Measurements",
      "Cap moisture test on fixed 12 pcs (3x4 MI, 3+ styles); results in the attached Excel table.",
      "Moisture Test for Cap", "comment", "Manual review",
      ex="Wrong: 2 MI styles · Right: 4 MI styles / 3+ cap styles recorded"),
    R("6.4.1", "Section 6 – Tests and Measurements",
      "Carton Drop Test must NOT be performed for New Era.",
      "Full report text", "", "Must not contain text", "Carton Drop Test",
      ex="Wrong: Carton Drop Test present · Right: no carton drop test"),
    R("6.4.2", "Section 6 – Tests and Measurements",
      "Wet & Dry Rub Test gray scale grading must be recorded in the comment and meet the acceptance thresholds.",
      "Wet Test", "comment", "Manual review",
      ex="Wrong: dark shade 2.5/1.5 marked Pass · Right: grading recorded, FAIL below threshold"),

    # ---- Section 7 – Report Photos ----
    R("7.1.1", "Section 7 – Report Photos",
      "A group picture of all inspected SKUs must appear on the report front page.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Is there a group picture showing all inspected SKUs/items together?",
      ex="Wrong: no group photo · Right: group photo of all items"),
    R("7.1.2", "Section 7 – Report Photos",
      "A screenshot of the Excel defect breakdown must be embedded in the report body.",
      "Defect Breakdown", "photo count", "At least N", "1",
      ex="Wrong: 'Excel attached' only · Right: inline screenshot + attached file"),
    R("7.2.1", "Section 7 – Report Photos",
      "Outer carton photos: Selected Carton, Shipping Mark, Carton Label, Barcode Check.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include Selected Carton, Shipping Mark, Carton Label, and Barcode Check?",
      ex="Wrong: Carton Label missing · Right: all four present"),
    R("7.3.1", "Section 7 – Report Photos",
      "Inner carton photos: Selected Carton (inner), Inner Box Label, Barcode Scanning, Opened Box, Inner Packing View, All Product View.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include inner Selected Carton, Inner Box Label, Barcode Scanning, Opened Box, Inner Packing View, and All Product View?",
      ex="Wrong: Opened Box missing · Right: all six present"),
    R("7.4.1", "Section 7 – Report Photos",
      "Product photos: Front View, Back View, Main Embroidery, Embroidery Logo, Reference Sample vs Product.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include Front View, Back View, Main Embroidery, Embroidery Logo, and Reference Sample vs Product comparison?",
      ex="Wrong: ref-sample comparison missing · Right: all present"),
    R("7.5.1", "Section 7 – Report Photos",
      "Spec/label photos: Compared with Spec, Brand/Fibre Label, Sticker on Visor, Hologram Sticker, Barcode Sticker, Tracking Label.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include Compared with Spec, Brand/Fibre Label, Sticker on Visor, Hologram Sticker, Barcode Sticker, and Tracking Label?",
      ex="Wrong: Compared with Spec missing · Right: all six present"),
    R("7.6.1", "Section 7 – Report Photos",
      "Checking photos: Function Check, Seam Check, Size Check, Visor Curve Height Check, Shape Check, Metal Detection Check.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include Function Check, Seam Check, Size Check, Visor Curve Height Check, Shape Check, and Metal Detection Check?",
      ex="Wrong: Shape Check missing · Right: all six present"),
    R("7.7.1", "Section 7 – Report Photos",
      "Moisture checking photos: Front Panel (near Emb), Visor (Upper), Visor (Lower), Sweatband.",
      "Mandatory pictures", "photo content", "AI photo check (flag if false)",
      "Do the photos include Front Panel (near Emb), Visor Upper, Visor Lower, and Sweatband positions?",
      ex="Wrong: 2 of 4 positions · Right: all 4 positions shown"),
    R("7.8.1", "Section 7 – Report Photos",
      "Every defect found must have a clear close-up photo.",
      "Defects", "photo count", "At least N", "1", each="each defect",
      ex="Wrong: defect with no photo · Right: each defect has a close-up photo"),
    R("7.9.1", "Section 7 – Report Photos",
      "The completed Measurement Defect AQL Table Excel file must be attached.",
      "Defect Breakdown", "file name", "File name matches",
      "*Measurement*Defect*AQL*Table*.xls",
      ex="Wrong: no Excel attached · Right: Measurement Defect AQL Table .xls attached"),

    # ---- Section 8 – AQL / AOQL Summary ----
    R("8.1.1", "Section 8 – AQL / AOQL Summary",
      "AQL/sampling level must match the product category (cap: Maj 1.5; apparel: Maj 2.5).",
      "Booking", "", "Manual review",
      ex="Wrong: cap booking uses Maj 2.5 · Right: cap uses Maj 1.5"),
    R("8.1.2", "Section 8 – AQL / AOQL Summary",
      "If the Advice List specifies a different sample size/AQL, the Advice List value takes precedence.",
      "Booking", "", "Manual review",
      ex="Wrong: default AQL used · Right: Advice List custom AQL used"),

    # ---- Section 9 – Pass / Fail Decision Logic ----
    R("9.1.1", "Section 9 – Pass / Fail Decision Logic",
      "Quantity section pass/fail decision (>=80% packed) must be justified; unpacked qty stated when failing.",
      "Available Quantity Check", "result", "Manual review",
      ex="Wrong: 55% packed marked Pass · Right: <80% marked Fail with unpacked qty"),
    R("9.1.2", "Section 9 – Pass / Fail Decision Logic",
      "Workmanship passes only if defects are within the AQL acceptance point; any Critical defect triggers FAIL.",
      "Defects", "", "Manual review",
      ex="Wrong: 15 Major vs AP 14 marked Pass · Right: fails when over acceptance"),
    R("9.1.3", "Section 9 – Pass / Fail Decision Logic",
      "No samples collected; defective units repaired/replaced on-site.",
      "Inspector remark", "", "Manual review",
      ex="Wrong: defects set aside as samples · Right: repaired/replaced on-site"),
]

wb = build_workbook(rows)
ws = wb["Checks"]
for dv in ws.data_validations.dataValidation:
    for sqref in dv.sqref.ranges:
        sqref.max_row = 200

OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT_XLSX)
n_cond = sum(1 for r in rows if r["row_type"].startswith("Condition"))
n_manual = sum(1 for r in rows if r["rule_type"] == "Manual review")
print(f"Wrote {len(rows)} rows ({n_cond} conditions, {n_manual} manual) -> {OUT_XLSX.name}")
