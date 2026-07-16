#!/usr/bin/env python3
"""Inject ```check blocks into rules.md after each checkpoint (idempotent)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADVISORY = "data_source: PO_booking\nwhere: []\nwhen: null\ncheck: null"
ADVISORY_SPEC = "data_source: spec_sheet\nwhere: []\nwhen: null\ncheck: null"
ADVISORY_EXT = "data_source: external\nwhere: []\nwhen: null\ncheck: null"

RIBKOFF_BLOCKS: dict[str, str] = {
    "1_1_1": ADVISORY_EXT,
    "1_1_2": ADVISORY,
    "1_2_1": """data_source: in_report
where: [report.global_remark]
when: null
check: extract("Does the inspector remark list defects broken down by PO number and include a total defect percentage? Quote the sentence or null if absent.")""",
    "1_3_1": """data_source: in_report
where: [product._first.real_packed_quantity, product._first.ordered_quantity]
when: null
check: ratio_at_least(0.8)""",
    "1_3_2": """data_source: in_report
where: [report.global_remark]
when: product._first.real_packed_quantity != product._first.ordered_quantity
check: extract("Quote the sentence explaining the quantity shortage or overage vs booking, or null if absent.")""",
    "1_4_1": """data_source: in_report
where: [report.global_remark]
when: null
check: extract("For every 'No' answer recorded in inspection details, is there a matching explanation in the summary review or global remark? Answer true only if all are explained.")""",
    "2_1_1": ADVISORY,
    "2_1_2": ADVISORY,
    "2_1_3": """data_source: in_report
where: [report.global_remark]
when: null
check: extract("Do the lot numbers on hangtags match the lot numbers on shipping cartons? Answer true only if they match or a clear discrepancy remark is present.")""",
    "2_2_1": """data_source: in_report
where: [checklist.are_the_qima_documents_signed.photo_count]
when: null
check: count_at_least(3)""",
    "3_1_1": """data_source: in_report
where: [checklist.random_carton_selection.result]
when: null
check: in_set(PASS, FAIL)""",
    "3_1_2": ADVISORY_EXT,
    "3_1_3": """data_source: in_report
where: [checklist.outer_packing_shipping_marks_front_side.photo_count]
when: null
check: count_at_least(3)""",
    "3_1_4": ADVISORY_EXT,
    "3_1_5": """data_source: in_report
where: [checklist.match_packing_info.result]
when: null
check: equals(PASS)""",
    "3_1_6": """data_source: in_report
where: [checklist.carton_drop_test.photo_count]
when: checklist.carton_drop_test.result equals PASS
check: count_at_most(0)""",
    "3_1_7": """data_source: in_report
where: [checklist.outer_packing_assortment_dimensions_weight.photo_count]
when: null
check: count_at_most(0)""",
    "3_1_8": ADVISORY_SPEC,
    "3_1_9": ADVISORY_EXT,
    "3_1_10": ADVISORY_EXT,
    "3_2_1": """data_source: in_report
where: [checklist.product_labels.photo_count]
when: null
check: count_at_least(1)""",
    "3_2_2": ADVISORY_EXT,
    "3_2_3": """data_source: in_report
where: [checklist.product_logo.result]
when: null
check: checklist.product_logo.result != NOT_APPLICABLE""",
    "3_2_4": """data_source: in_report
where: [checklist.product_style_construction.result]
when: null
check: equals(PASS)""",
    "3_2_5": ADVISORY_EXT,
    "3_2_6": ADVISORY_EXT,
    "3_2_7": ADVISORY_EXT,
    "4_1_1": """data_source: in_report
where: [workmanship.found_critical, workmanship.max_defects_critical]
when: null
check: workmanship.found_critical <= workmanship.max_defects_critical""",
    "4_1_2": ADVISORY_EXT,
    "4_1_3": ADVISORY_EXT,
    "4_1_4": ADVISORY_EXT,
    "4_1_5": ADVISORY_EXT,
    "4_1_6": ADVISORY_EXT,
    "4_1_7": ADVISORY_EXT,
    "4_1_8": ADVISORY_EXT,
    "4_2_1": """data_source: in_report
where: [report.defects_without_photo]
when: null
check: equals(0)""",
    "5_1_1": """data_source: in_report
where: [checklist.product_dimensions_result.attachment_filenames]
when: null
check: filename_matches("Measurement Chart-*.xlsx")""",
    "5_1_2": ADVISORY_SPEC,
    "5_1_3": ADVISORY_SPEC,
    "5_1_4": ADVISORY_SPEC,
    "5_1_5": ADVISORY_SPEC,
    "5_2_1": """data_source: in_report
where: [checklist.color_shading_check.photo_count]
when: null
check: count_at_most(1)""",
    "5_2_2": """data_source: in_report
where: [checklist.stitch_density_check.comment]
when: null
check:
  - present
  - has_number""",
    "5_2_3": ADVISORY_EXT,
    "5_2_4": ADVISORY_EXT,
    "5_2_5": ADVISORY_EXT,
    "5_2_6": ADVISORY_EXT,
    "5_2_7": ADVISORY_EXT,
    "5_3_1": ADVISORY_EXT,
    "6_1_1": """data_source: in_report
where: [report.overall_result]
when: null
check: in_set(PASS, FAIL, PENDING)""",
    "6_1_2": ADVISORY_EXT,
    "6_1_3": ADVISORY_EXT,
    "6_1_4": ADVISORY_EXT,
    "7_1_1": """data_source: in_report
where: [workmanship.aql_level_major]
when: null
check: equals(2.5)""",
    "7_1_2": """data_source: in_report
where: [workmanship.aql_level_minor]
when: null
check: equals(4.0)""",
    "8_1_1": """data_source: in_report
where: [product._first.real_packed_quantity, product._first.ordered_quantity]
when: report.overall_result equals PASS
check: ratio_at_least(0.8)""",
}


def _slug(rule_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", rule_id.strip().lower()).strip("_")


def inject_blocks(markdown: str, blocks: dict[str, str], *, replace: bool = False) -> str:
    if replace:
        markdown = re.sub(r"\n*```check\n[\s\S]*?```", "", markdown)
    parts = re.split(r"(?=^\*\*ID:\*\*)", markdown, flags=re.MULTILINE)
    out: list[str] = []
    for part in parts:
        if not part.strip():
            continue
        id_match = re.match(r"^\*\*ID:\*\*\s+(.+)$", part, flags=re.MULTILINE)
        if not id_match:
            out.append(part)
            continue
        cp_id = _slug(id_match.group(1))
        if cp_id not in blocks:
            out.append(part)
            continue
        if "```check" in part and not replace:
            out.append(part)
            continue
        block_body = blocks[cp_id]
        fenced = f"\n\n```check\n{block_body}\n```\n"
        if "\n---\n" in part:
            part = part.replace("\n---\n", fenced + "\n---\n", 1)
        else:
            part = part.rstrip() + fenced + "\n"
        out.append(part)
    return "".join(out)


def main() -> None:
    rules_md = ROOT / "data/clients/ribkoff/gi/rules.md"
    text = rules_md.read_text(encoding="utf-8")
    updated = inject_blocks(text, dict(RIBKOFF_BLOCKS), replace="--replace" in sys.argv)
    rules_md.write_text(updated, encoding="utf-8")
    injected = sum(1 for cp_id in RIBKOFF_BLOCKS if f"```check" in updated and cp_id in updated)
    print(f"Updated {rules_md} ({len(RIBKOFF_BLOCKS)} block definitions)")


if __name__ == "__main__":
    main()
