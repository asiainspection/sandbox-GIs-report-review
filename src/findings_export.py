"""Build report-team findings Excel from PolicyGuard review flags."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Exact headers from the findings handoff template
FINDINGS_HEADERS = [
    "Order #",
    "Empty",
    "1",
    "What was checked",
    "Checkpoint",
    "Original Content",
    "Non-confirmities",
    "Suggested actions",
    "Finding Verdict",
    "Remark",
]

_SELECTOR_RE = re.compile(
    r"checklist\.(?P<node>[a-z0-9_]+)\.(?P<field>photo_count|caption_count|comment|result)(?:=(?P<val>[^,;]+))?",
    re.I,
)
_MAX_RE = re.compile(r"\bmax=(\d+)", re.I)
_STYLE_RE = re.compile(r"missing style\s+(\S+)", re.I)


def order_id_for_report(report_path: Path, report: dict[str, Any] | None = None) -> str:
    """Prefer Q-number from filename; fall back to inspection id."""
    stem = report_path.stem.replace("_flawed", "").replace("_llm", "")
    q = re.match(r"(Q\d{9,10})", stem, re.I)
    if q:
        return q.group(1)
    if report is None and report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            report = None
    if isinstance(report, dict):
        for key in ("inspectionId", "reportId", "qspInspectionId"):
            val = report.get(key)
            if val:
                return str(val)
    return stem


def requirements_by_id(checkpoints: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for cp in checkpoints:
        cid = str(cp.get("id") or "")
        req = str(cp.get("requirement") or cp.get("what_to_check") or "").strip()
        if cid:
            out[cid] = req
    return out


def checkpoint_meta_by_id(checkpoints: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """id → {requirement, fail_if, section, severity} for handoff wording."""
    out: dict[str, dict[str, Any]] = {}
    for cp in checkpoints:
        cid = str(cp.get("id") or "")
        if not cid:
            continue
        fail_if = cp.get("fail_if") or []
        if isinstance(fail_if, str):
            fail_if = [fail_if]
        out[cid] = {
            "requirement": str(cp.get("requirement") or cp.get("what_to_check") or "").strip(),
            "fail_if": [str(x).strip() for x in fail_if if str(x).strip()],
            "section": str(cp.get("section") or "").strip(),
            "severity": str(cp.get("severity") or "").strip(),
        }
    return out


def _node_label(node: str) -> str:
    return node.replace("_", " ").strip().title()


def _clip(text: str, n: int = 280) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _gi_snippet(meta: dict[str, Any] | None) -> str:
    if not meta:
        return ""
    req = _clip(str(meta.get("requirement") or ""), 220)
    fail = meta.get("fail_if") or []
    # Prefer the GI statement (often the last fail_if "Report does not satisfy: …")
    gi_fail = ""
    for item in fail:
        if "Report does not satisfy:" in item:
            gi_fail = item.split("Report does not satisfy:", 1)[-1].strip()
            break
    if not gi_fail and fail:
        gi_fail = str(fail[0])
    gi_fail = _clip(gi_fail, 220)
    if req and gi_fail and gi_fail.lower() not in req.lower():
        return f"GI: {req} | Rule: {gi_fail}"
    if req:
        return f"GI: {req}"
    if gi_fail:
        return f"GI: {gi_fail}"
    return ""


def _humanize_evidence(evidence: str) -> str:
    """Turn machine evidence into a short report-side description."""
    ev = (evidence or "").strip()
    if not ev:
        return "(no report snippet available)"

    # Global remark quote already present
    if "report.global_remark" in ev:
        # e.g. report.global_remark blank=False; report.global_remark=<text>
        m = re.search(r"report\.global_remark=(.+)$", ev, re.S)
        if m:
            body = m.group(1).strip()
            if body and body.lower() not in ("true", "false"):
                return f'Inspector remark: "{_clip(body, 260)}"'
        if "blank=True" in ev or re.search(r"report\.global_remark=\s*$", ev):
            return "Inspector remark: (blank)"
        return _clip(ev, 260)

    style = _STYLE_RE.search(ev)
    if style:
        return f"Measurement attachment / chart: style {style.group(1)} not found in report attachments."

    # Count comparisons: checklist.X.photo_count=N, max=M
    m = _SELECTOR_RE.search(ev)
    if m:
        node = _node_label(m.group("node"))
        field = m.group("field")
        val = (m.group("val") or "").strip()
        max_m = _MAX_RE.search(ev)
        max_n = max_m.group(1) if max_m else None
        if field == "photo_count":
            if max_n is not None:
                return f'Checklist "{node}": {val} photo(s) attached (allowed max {max_n} for this result).'
            return f'Checklist "{node}": {val} photo(s) attached.'
        if field == "caption_count":
            # often "caption_count=0 >= photo_count=…"
            photos = re.search(r"photo_count=?(\d+)", ev)
            photo_n = photos.group(1) if photos else "?"
            return (
                f'Checklist "{node}": {val} caption(s) for {photo_n} photo(s) '
                f"(captions must identify each comparison photo)."
            )
        if field == "comment":
            if "blank=True" in ev or val == "":
                return f'Checklist "{node}": comment is blank.'
            return f'Checklist "{node}" comment: "{_clip(val, 200)}"'
        if field == "result":
            return f'Checklist "{node}" result: {val or "(empty)"}.'

    # Caption vs photo shorthand from symbolic: "caption_count=0 >= …photo_count=N"
    if "caption_count" in ev and "photo_count" in ev:
        return _clip(ev.replace("checklist.", "").replace("_", " "), 260)

    return _clip(ev, 260)


def original_content(flag: dict[str, Any], report_snippet: str | None = None) -> str:
    """Actual snippet from the report (prefer enriched pull; else humanized evidence)."""
    if report_snippet and report_snippet.strip():
        return _clip(report_snippet.strip(), 320)
    return _humanize_evidence(str(flag.get("evidence") or ""))


def non_conformity(flag: dict[str, Any], meta: dict[str, Any] | None) -> str:
    """GI snippet + what is wrong in the report."""
    gi = _gi_snippet(meta)
    report_err = _humanize_evidence(str(flag.get("evidence") or ""))
    reason = str(flag.get("reason") or "").strip()
    if reason and reason not in (
        "Report evidence violates this requirement.",
        "Report evidence violates this requirement",
    ):
        report_err = f"{report_err} ({_clip(reason, 120)})"
    if gi:
        return f"{gi}\n— Error in report: {report_err}"
    return f"Error in report: {report_err}"


def suggested_actions(flag: dict[str, Any], meta: dict[str, Any] | None) -> str:
    """Concrete modify / adjust / remove / add wording for the inspector."""
    ev = str(flag.get("evidence") or "")
    cid = str(flag.get("checkpoint_id") or "")
    node_m = _SELECTOR_RE.search(ev)
    node = _node_label(node_m.group("node")) if node_m else ""
    field = node_m.group("field") if node_m else ""
    max_m = _MAX_RE.search(ev)
    max_n = int(max_m.group(1)) if max_m else None

    if "global_remark" in ev or cid in ("1_2_1", "1_3_2"):
        return (
            "Modify the Inspector Remark: add a complete defect breakdown by PO "
            '(format: "PO xxx: X pcs defect found / Total: X% defects found").'
        )

    style = _STYLE_RE.search(ev)
    if style or cid == "5_1_1":
        style_n = style.group(1) if style else "the booking style number"
        return (
            f"Replace the measurement chart attachment with the mandatory Joseph Ribkoff POM template "
            f'named "Measurement Chart-{style_n}.xlsx" (or matching style).'
        )

    if field == "photo_count" and max_n == 0:
        return f'Remove the photo(s) from checklist "{node}" (GI forbids photos for this result) — keep only if the test FAILS.'
    if field == "photo_count" and max_n is not None and max_n > 0:
        return f'Adjust "{node}": keep at most {max_n} photo(s); remove extras.'
    if field == "caption_count":
        return (
            f'Adjust captions under "{node}": every comparison photo must be captioned to identify '
            "bulk product vs approval sample (SKU/style)."
        )
    if field == "comment" and ("blank=True" in ev or re.search(r"comment=\s*(;|$)", ev)):
        return f'Add a numeric finding in the "{node}" comment (e.g. stitch count per inch).'
    if "missing" in ev.lower():
        return "Correct the report: upload the missing required attachment/photo referenced by the GI."

    # Fallback from GI requirement first clause
    req = _clip(str((meta or {}).get("requirement") or ""), 160)
    if req:
        return f"Modify the report to comply with the GI: {req}"
    return "Review this checkpoint in the GI and correct the report accordingly."


def enrich_report_snippet(report: dict[str, Any] | None, evidence: str) -> str | None:
    """Pull a live checklist comment/result snippet from the report JSON when possible."""
    if not report:
        return None
    m = _SELECTOR_RE.search(evidence or "")
    if not m:
        if "global_remark" in (evidence or ""):
            remark = (report.get("result") or {}).get("globalRemark") or {}
            msg = str(remark.get("message") or "").strip()
            return f'Inspector remark: "{_clip(msg, 260)}"' if msg else "Inspector remark: (blank)"
        return None

    target = normalize_node(m.group("node"))
    field = m.group("field")
    for el in _iter_checklist_elements(report):
        name = _element_name(el)
        if normalize_node(name) != target and normalize_node(name.replace(" ", "_")) != target:
            # fuzzy: compare collapsed forms
            if re.sub(r"[^a-z0-9]", "", name.lower()) != re.sub(r"[^a-z0-9]", "", target):
                continue
        result = el.get("result")
        imgs = len(el.get("images") or [])
        comment = ""
        c = el.get("comment") or {}
        if isinstance(c, dict):
            comment = str(c.get("message") or "").strip()
        if field == "comment":
            return (
                f'Checklist "{name}" result={result}; comment="{_clip(comment, 200) if comment else "(blank)"}"'
            )
        if field in ("photo_count", "caption_count"):
            cap = sum(1 for im in (el.get("images") or []) if (im.get("caption") or "").strip())
            extra = f'; comment="{_clip(comment, 120)}"' if comment else ""
            return f'Checklist "{name}" result={result}; photos={imgs}; captions={cap}{extra}'
        if field == "result":
            return f'Checklist "{name}" result={result}; photos={imgs}'
        return f'Checklist "{name}" result={result}; photos={imgs}'
    return None


def normalize_node(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")


def _element_name(el: dict[str, Any]) -> str:
    n = el.get("name") or el.get("title") or ""
    if isinstance(n, dict):
        n = n.get("message") or ""
    return str(n)


def _walk(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for el in elements:
        found.append(el)
        if el.get("elements"):
            found.extend(_walk(el["elements"]))
        content = (el.get("content") or {}).get("elements")
        if content:
            found.extend(_walk(content))
    return found


def _iter_checklist_elements(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for step in (report.get("result") or {}).get("steps", []):
        for action in step.get("actions", []):
            for key in ("testsChecklist", "defectsChecklist"):
                cl = action.get(key) or {}
                out.extend(_walk((cl.get("content") or {}).get("elements", [])))
    return out


def flag_rows_for_order(
    *,
    order_id: str,
    flags: list[dict[str, Any]],
    requirements: dict[str, str],
    meta_by_id: dict[str, dict[str, Any]] | None = None,
    report: dict[str, Any] | None = None,
) -> list[list[Any]]:
    """One Excel row per flag; Order # only on the first row of the group."""
    meta_by_id = meta_by_id or {}
    rows: list[list[Any]] = []
    for i, flag in enumerate(flags, start=1):
        cid = str(flag.get("checkpoint_id") or "")
        meta = meta_by_id.get(cid)
        snippet = enrich_report_snippet(report, str(flag.get("evidence") or ""))
        what = requirements.get(cid) or (meta or {}).get("requirement") or flag.get("section") or ""
        rows.append(
            [
                order_id if i == 1 else None,
                None,  # Empty
                i,  # sequence within the order
                _clip(str(what), 200),
                cid,
                original_content(flag, snippet),
                non_conformity(flag, meta),
                suggested_actions(flag, meta),
                None,  # Finding Verdict — filled by report team
                None,  # Remark — filled by report team
            ]
        )
    return rows


def write_findings_workbook(
    orders: list[tuple[str, list[dict[str, Any]]]],
    requirements: dict[str, str],
    output_path: Path,
    *,
    summary_rows: list[dict[str, Any]] | None = None,
    meta_by_id: dict[str, dict[str, Any]] | None = None,
    reports_by_order: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write Findings (+ optional Summary) workbook.

    ``orders`` is a list of ``(order_id, flags)`` in the order they should appear.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"
    ws.append(FINDINGS_HEADERS)

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(color="FFFFFF", bold=True)
    wrap = Alignment(wrap_text=True, vertical="top")
    for col, _ in enumerate(FINDINGS_HEADERS, start=1):
        cell = ws.cell(1, col)
        cell.fill = header_fill
        cell.font = header_font

    reports_by_order = reports_by_order or {}
    for order_id, flags in orders:
        if not flags:
            continue
        for row in flag_rows_for_order(
            order_id=order_id,
            flags=flags,
            requirements=requirements,
            meta_by_id=meta_by_id,
            report=reports_by_order.get(order_id),
        ):
            ws.append(row)

    widths = {
        "A": 14,
        "B": 8,
        "C": 6,
        "D": 40,
        "E": 12,
        "F": 45,
        "G": 55,
        "H": 45,
        "I": 16,
        "J": 30,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=10):
        for cell in row:
            cell.alignment = wrap
            if cell.row > 1:
                ws.row_dimensions[cell.row].height = 75
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(FINDINGS_HEADERS))}{max(ws.max_row, 1)}"

    if summary_rows:
        sm = wb.create_sheet("Summary")
        keys = list(summary_rows[0].keys())
        sm.append(keys)
        for row in summary_rows:
            sm.append([row.get(k) for k in keys])
        for col in range(1, len(keys) + 1):
            sm.column_dimensions[get_column_letter(col)].width = 18

    legend = wb.create_sheet("Verdict legend")
    legend.append(["Finding Verdict", "Meaning"])
    for verdict, meaning in (
        ("Accurate", "Finding is correct — report should be fixed"),
        ("Extra but ok", "Valid observation but not needed for this handoff"),
        ("Wrong", "False positive — do not send / ignore"),
        ("Pending review", "Not yet judged by the report team"),
    ):
        legend.append([verdict, meaning])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
