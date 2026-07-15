"""Extract comparable facts from QIMAone inspection report PDFs (cover + checklist hints)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz


def _num(text: str | None) -> int | None:
    if not text:
        return None
    cleaned = str(text).replace(",", "").strip()
    try:
        return int(float(cleaned))
    except (TypeError, ValueError):
        return None


def _norm_result(text: str | None) -> str:
    if not text:
        return ""
    return str(text).strip().upper().replace("PASSED", "PASS").replace("FAILED", "FAIL")


@dataclass
class PdfCoverFacts:
    overall_result: str = ""
    inspection_reference: str = ""
    inspection_date: str = ""
    ordered_quantity: int | None = None
    real_produced_quantity: int | None = None
    expected_produced_quantity: int | None = None
    real_packed_quantity: int | None = None
    expected_packed_quantity: int | None = None
    found_critical: int | None = None
    found_major: int | None = None
    found_minor: int | None = None
    workmanship_result: str = ""
    sku: str = ""
    po_reference: str = ""
    global_remark_lines: list[str] = field(default_factory=list)


@dataclass
class PdfChecklistHint:
    item_name: str
    result: str = ""
    photo_count: int | None = None
    value: str = ""


def pdf_full_text(path: Path, *, pages: list[int] | None = None) -> str:
    doc = fitz.open(path)
    try:
        if pages is None:
            return "\n".join(page.get_text() for page in doc)
        return "\n".join(doc[i].get_text() for i in pages if i < len(doc))
    finally:
        doc.close()


def extract_cover_facts(text: str) -> PdfCoverFacts:
    facts = PdfCoverFacts()

    m = re.search(r"Overall result\s*\n\s*(Pass|Fail|PASS|FAIL)\b", text, re.I)
    if m:
        facts.overall_result = _norm_result(m.group(1))

    m = re.search(r"Inspection reference:\s*([\d\s]+)", text, re.I)
    if m:
        facts.inspection_reference = re.sub(r"\s+", "", m.group(1))

    m = re.search(r"Inspection date:\s*\n\s*([0-9\-A-Za-z]+)", text, re.I)
    if m:
        facts.inspection_date = m.group(1).strip()

    m = re.search(r"Ordered quantity\s*\n\s*([\d,]+)", text, re.I)
    if m:
        facts.ordered_quantity = _num(m.group(1))

    m = re.search(
        r"Produced quantity\s*\n\s*([\d,]+)\s*(?:\n\s*[\d.]+\s*%)?\s*\n\s*Expected:\s*([\d,]+)",
        text,
        re.I | re.S,
    )
    if m:
        facts.real_produced_quantity = _num(m.group(1))
        facts.expected_produced_quantity = _num(m.group(2))

    m = re.search(
        r"Packed quantity\s*\n\s*([\d,]+)\s*(?:\n\s*[\d.]+\s*%)?\s*\n\s*Expected:\s*([\d,]+)",
        text,
        re.I | re.S,
    )
    if m:
        facts.real_packed_quantity = _num(m.group(1))
        facts.expected_packed_quantity = _num(m.group(2))

    m = re.search(
        r"Workmanship\s*\n\s*Defective rate:.*?\n\s*(Pass|Fail)\s*\n\s*CRI\s*(\d+)\s*\n\s*MAJ\s*(\d+)\s*\n\s*MIN\s*(\d+)",
        text,
        re.I | re.S,
    )
    if m:
        facts.workmanship_result = _norm_result(m.group(1))
        facts.found_critical = _num(m.group(2))
        facts.found_major = _num(m.group(3))
        facts.found_minor = _num(m.group(4))

    m = re.search(r"SKU\s*\n\s*(\S+)", text, re.I)
    if m:
        facts.sku = m.group(1).strip()

    m = re.search(r"PO ref:\s*([^\n]+)", text, re.I)
    if m:
        facts.po_reference = m.group(1).strip()

    m = re.search(r"Inspector's remark\s*\n(.*?)(?:\nPO & Product details|\nSKU\s)", text, re.I | re.S)
    if m:
        facts.global_remark_lines = [
            line.strip() for line in m.group(1).split("\n") if line.strip() and not line.startswith("Generated")
        ]

    return facts


def _hint_from_window(item_name: str, window: str) -> PdfChecklistHint:
    hint = PdfChecklistHint(item_name=item_name)
    upper = window.upper()
    for token in ("NOT_APPLICABLE", "N/A", "PASS", "FAIL", "PENDING"):
        if re.search(rf"\b{re.escape(token)}\b", upper):
            hint.result = _norm_result(token)
            break
    if re.search(r"\bPASSED\b", upper):
        hint.result = "PASS"

    photo_match = re.search(r"(\d+)\s*(?:photos?|cartons?|pictures?|videos?)?\s*\n\s*(?:Pass|Fail|PASS|FAIL)", window, re.I)
    if photo_match:
        hint.photo_count = _num(photo_match.group(1))
    else:
        count_match = re.search(r"\n(\d+)\s*\n(?:Checked|Selected|Pass|Fail|PASS|FAIL|PASSED)", window)
        if count_match:
            hint.photo_count = _num(count_match.group(1))

    if "PASSED" in upper:
        hint.value = "PASSED"
    return hint


def extract_checklist_hints(text: str, item_names: list[str]) -> dict[str, PdfChecklistHint]:
    """Best-effort: locate each checklist item name in PDF text and read nearby result/photos."""
    hints: dict[str, PdfChecklistHint] = {}
    for name in item_names:
        key = name.strip()
        if not key:
            continue
        pos = text.find(key)
        if pos < 0:
            hints[key] = PdfChecklistHint(item_name=key)
            continue
        window = text[pos : pos + min(400, len(text) - pos)]
        hints[key] = _hint_from_window(key, window)
    return hints


def compare_cover(pdf: PdfCoverFacts, semantic: dict[str, Any]) -> list[dict[str, Any]]:
    """Return list of mismatches between PDF cover and semantic JSON facts."""
    mismatches: list[dict[str, Any]] = []
    product = (semantic.get("products") or [{}])[0]
    workmanship = semantic.get("workmanship") or {}

    pairs = [
        ("overall_result", pdf.overall_result, _norm_result(semantic.get("overall_result"))),
        ("ordered_quantity", pdf.ordered_quantity, product.get("ordered_quantity")),
        ("real_produced_quantity", pdf.real_produced_quantity, product.get("real_produced_quantity")),
        ("expected_produced_quantity", pdf.expected_produced_quantity, product.get("expected_produced_quantity")),
        ("real_packed_quantity", pdf.real_packed_quantity, product.get("real_packed_quantity")),
        ("expected_packed_quantity", pdf.expected_packed_quantity, product.get("expected_packed_quantity")),
        ("found_major", pdf.found_major, int(workmanship.get("found_major") or 0) if workmanship else None),
        ("found_minor", pdf.found_minor, int(workmanship.get("found_minor") or 0) if workmanship else None),
        ("found_critical", pdf.found_critical, int(workmanship.get("found_critical") or 0) if workmanship else None),
        ("workmanship_result", pdf.workmanship_result, _norm_result(workmanship.get("result"))),
        ("sku", pdf.sku, semantic.get("sku")),
    ]

    for field_name, pdf_val, sem_val in pairs:
        if pdf_val in (None, "") or sem_val in (None, ""):
            continue
        if str(pdf_val).replace(",", "") != str(sem_val).replace(",", ""):
            mismatches.append({"field": field_name, "pdf": pdf_val, "parser": sem_val})

    if pdf.po_reference and semantic.get("po_reference"):
        pdf_tokens = [t for t in re.split(r"[,;]", pdf.po_reference) if t.strip()]
        sem_tokens = [t for t in re.split(r"[,;]", str(semantic.get("po_reference", ""))) if t.strip()]
        pdf_digits = re.sub(r"\D", "", pdf.po_reference)
        sem_digits = re.sub(r"\D", "", str(semantic.get("po_reference", "")))
        # PDF line-wrap often truncates PO refs; skip strict compare when PDF capture is incomplete.
        if len(pdf_digits) >= 6 and sem_digits and pdf_digits not in sem_digits and sem_digits not in pdf_digits:
            if not any(pt.strip() in st for pt in pdf_tokens for st in sem_tokens):
                mismatches.append(
                    {"field": "po_reference", "pdf": pdf.po_reference, "parser": semantic.get("po_reference")}
                )

    return mismatches


def compare_checklist_items(
    hints: dict[str, PdfChecklistHint],
    semantic_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for item in semantic_items:
        name = item.get("item_name") or ""
        hint = hints.get(name)
        if hint is None:
            mismatches.append({"item": name, "issue": "not_found_in_pdf"})
            continue
        if hint.result and item.get("result"):
            pdf_r = _norm_result(hint.result)
            sem_r = _norm_result(item.get("result"))
            if pdf_r and sem_r and pdf_r != sem_r and not (pdf_r == "PASS" and sem_r == "NOT_APPLICABLE"):
                mismatches.append(
                    {"item": name, "field": "result", "pdf": hint.result, "parser": item.get("result")}
                )
        if hint.photo_count is not None and item.get("photo_count") is not None:
            if hint.photo_count != item.get("photo_count"):
                mismatches.append(
                    {
                        "item": name,
                        "field": "photo_count",
                        "pdf": hint.photo_count,
                        "parser": item.get("photo_count"),
                    }
                )
    return mismatches
