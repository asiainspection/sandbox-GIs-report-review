"""Ground Field/Location prose to report evidence bindings.

Checklist item names are NOT a closed catalog — they vary per report and client.
Authoring uses intent bindings (keywords from GI prose). Runtime matches
those keywords against checklist names in the actual report.

Optional: sample corrected reports can sharpen match tokens when available.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fact_schema import bind_checklist_name, bind_checklist_names_all, normalize_name
from semantic_report import parse_semantic_report

# GI prose often says "Tests checklist"; reports use "Checkpoints".
_SECTION_ALIASES: dict[str, list[str]] = {
    "tests": ["checkpoints"],
    "test": ["checkpoints"],
    "checkpoints": ["checkpoints"],
    "product specifications": ["product specifications"],
    "specifications": ["product specifications"],
    "packing": ["product packing & packaging"],
    "packaging": ["product packing & packaging"],
    "workmanship": ["workmanship"],
    "quantity": ["quantity"],
    "dimensions": ["product dimensions"],
}


_INTENT_NOISE = frozenset(
    {
        "test",
        "tests",
        "check",
        "checklist",
        "report",
        "photos",
        "photo",
        "picture",
        "section",
        "item",
        "field",
        "location",
        "the",
        "and",
        "for",
        "with",
    }
)


def _client_corrected_dir(root: Path, client: str) -> Path:
    return root / "data" / "clients" / client / "corrected"


def load_checklist_names_from_reports(root: Path, client: str) -> list[str]:
    """Union of checklist item names seen in a client's corrected report fixtures."""
    corrected = _client_corrected_dir(root, client)
    if not corrected.is_dir():
        return []
    names: set[str] = set()
    for path in sorted(corrected.glob("*.json")):
        if "injection" in path.name:
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        semantic = parse_semantic_report(report)
        for item in semantic.checklist_items:
            nm = (item.item_name or "").strip()
            if nm:
                names.add(nm)
    return sorted(names, key=str.lower)


def load_checklist_names(root: Path, client: str) -> list[str]:
    """Names seen in sample corrected reports — not a closed allowlist."""
    return load_checklist_names_from_reports(root, client)


def load_section_names_from_report(report_path: Path | None) -> list[str]:
    if report_path is None or not report_path.is_file():
        return []
    report = json.loads(report_path.read_text(encoding="utf-8"))
    semantic = parse_semantic_report(report)
    return sorted(
        {str(item.section).strip() for item in semantic.checklist_items if str(item.section or "").strip()}
    )


def _candidate_phrases(field: str) -> list[str]:
    """Pull likely checklist-item phrases from a Field/Location line."""
    field = (field or "").strip()
    if not field:
        return []
    phrases: list[str] = []
    # Split on common separators used in GI markdown.
    for part in re.split(r"[/—|–]", field):
        part = part.strip()
        if not part:
            continue
        low = part.lower()
        # Drop trailing "… checklist" / "report photos" noise.
        cleaned = re.sub(
            r"\s*(checklist|report photos|report|photos?)\s*$",
            "",
            part,
            flags=re.I,
        ).strip()
        cleaned = re.sub(r"\s*checklist\s*$", "", cleaned, flags=re.I).strip()
        if len(cleaned) >= 4 and cleaned.lower() not in ("tests", "test", "report"):
            phrases.append(cleaned)
        if "checklist" in low and cleaned:
            phrases.append(cleaned)
    # Whole field as last resort (minus trailing section label).
    whole = re.sub(r"\s*[—/].*$", "", field).strip()
    if len(whole) >= 4:
        phrases.append(whole)
    # Dedupe preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for p in phrases:
        key = normalize_name(p)
        if key and key not in seen:
            seen.add(key)
            out.append(p)
    return out


def match_checklist_item(field: str, available: list[str]) -> str | None:
    """Best fuzzy match of Field/Location against real checklist item names."""
    if not available:
        return None
    best_name: str | None = None
    best_score = 0.0
    for phrase in _candidate_phrases(field):
        hit = bind_checklist_name(phrase, available, min_score=0.45)
        if hit is None:
            continue
        # Prefer exact / near-exact phrase hits.
        from fact_schema import _score_checklist_name

        score = _score_checklist_name(phrase, hit)
        if score > best_score:
            best_score = score
            best_name = hit
    return best_name


def match_section(field: str, available_sections: list[str] | None = None) -> str | None:
    """Map GI section wording (e.g. Tests checklist) to a real report section."""
    text = (field or "").lower()
    sections = list(available_sections or [])
    # Alias table first.
    for key, aliases in _SECTION_ALIASES.items():
        if key in text:
            for alias in aliases:
                if sections:
                    hit = bind_checklist_name(alias, sections, min_score=0.4)
                    if hit:
                        return hit
                else:
                    return alias.title() if alias != "checkpoints" else "Checkpoints"
    if sections:
        for phrase in _candidate_phrases(field):
            hits = bind_checklist_names_all(phrase, sections, min_score=0.5)
            if hits:
                return hits[0]
    return None


def infer_evidence_field(field: str, what: str) -> str:
    """Pick checklist suffix / report field from rule prose."""
    text = f"{field or ''} {what or ''}".lower()

    if any(
        k in text
        for k in (
            "photo must show",
            "photos must show",
            "side by side",
            "what the photo",
            "visible in the photo",
            "photo content",
            "fit model",
        )
    ):
        return "photo_content"

    if any(k in text for k in ("measurement chart", "xlsx", "excel", "attachment", "must attach")):
        if "content" in text or "inside" in text or "cells" in text or "tolerance" in text or "sequence" in text:
            return "attachment_content"
        return "attachment_filenames"

    if "caption" in text:
        return "photo_captions"

    if any(k in text for k in ("photo", "picture", "upload", "image")):
        return "photo_count"

    if any(k in text for k in ("must be pass", "result must", "mark as pass", "n/a", "not applicable")):
        return "result"

    if any(k in text for k in ("remark", "comment", "must state", "explain")):
        return "comment"

    # Default for a resolved checklist item: comment (text, checkable now).
    return "comment"


# Cover / report / workmanship surfaces named in Field/Location but not checklist items.
# Order matters: first match wins.
_REPORT_LOCUS_RULES: list[tuple[tuple[str, ...], str]] = (
    (("days postponed", "postponed", "planned date"), "report.days_postponed"),
    (("inspection date", "inspection date fields"), "report.inspection_date"),
    (("overall", "inspection result"), "report.overall_result"),
    (("po number", "po reference", "purchase order"), "report.po_reference"),
    (("sku", "product ref", "product reference", "product label", "product name"), "report.product_label"),
    (("supplier",), "report.supplier_name"),
    (("factory address", "factory location", "production site"), "report.factory_address"),
    (("factory name", "factory"), "report.factory_name"),
    (("location — cover", "location —", "location field", "cover page, inspection details"), "report.production_site"),
    (("unit —", "unit field", "quantity unit"), "product._first.unit"),
    (("ordered quantity", "order quantity"), "product._first.ordered_quantity"),
    (("packed quantity", "real packed"), "product._first.real_packed_quantity"),
    (("aql major", "major aql"), "workmanship.aql_level_major"),
    (("aql minor", "minor aql"), "workmanship.aql_level_minor"),
    (("aql critical", "critical aql"), "workmanship.aql_level_critical"),
    (("workmanship result",), "workmanship.result"),
    (
        (
            "defects checklist",
            "defect severity",
            "dirt",
            "stain",
            "stitching defect",
            "yarn defect",
            "puckering",
            "rust defect",
            "classification",
            "classified as",
        ),
        "report.defects",
    ),
    (("defect photo", "defects without photo", "every defect"), "report.defects_without_photo"),
    (("defect", "workmanship"), "report.defect_count"),
    (("attachment", "techpack", "pdf file", "measurement file", "xlsx", "excel"), "report.attachment_filenames"),
    (("caption",), "report.all_captions"),
    (("global remark", "summary review", "other remarks"), "report.global_remark"),
    (("destination",), "report.destinations"),
    (("inspection type",), "report.inspection_type"),
)


def match_report_locus(field: str, what: str) -> str | None:
    """Map Field/Location + What prose onto a canonical report selector."""
    text = f"{field or ''} {what or ''}".lower()
    if not text.strip():
        return None
    for keys, selector in _REPORT_LOCUS_RULES:
        if any(k in text for k in keys):
            return selector
    # Cover-page / inspection-details catch-all → inspector-visible text.
    if any(k in text for k in ("cover page", "inspection details", "front page", "report front")):
        return "report.inspector_text"
    if any(k in text for k in ("remark", "note", "comment", "explain", "must state")):
        return "report.global_remark"
    if not _field_names_checklist_item(field or ""):
        if any(k in text for k in ("photo", "picture", "image")):
            return "report.all_captions"
    return None


def _intent_tokens(text: str, *, limit: int = 6) -> list[str]:
    tokens = [
        t
        for t in re.split(r"[^a-z0-9]+", (text or "").lower())
        if len(t) >= 3 and t not in _INTENT_NOISE
    ]
    out: list[str] = []
    seen: set[str] = set()
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= limit:
            break
    return out


def intent_where(match_name: str, field_suffix: str, *, kind: str = "checklist") -> dict[str, Any]:
    """Intent binding — runtime fuzzy-matches; do not freeze a wrong slug."""
    tokens = _intent_tokens(match_name)
    if not tokens:
        tokens = [t for t in re.split(r"[^a-z0-9]+", match_name.lower()) if len(t) >= 2][:4]
    return {"kind": kind, "match": tokens or [match_name], "field": field_suffix}


def intent_from_prose(field: str, what: str, field_suffix: str) -> dict[str, Any]:
    """Build a checklist intent from GI prose alone — no name catalog required."""
    phrases = _candidate_phrases(field)
    seed = phrases[0] if phrases else (field or "").strip()
    tokens = _intent_tokens(f"{seed} {what or ''}")
    if not tokens:
        tokens = _intent_tokens(field or what or "checklist")
    return {"kind": "checklist", "match": tokens or ["checklist"], "field": field_suffix}


def _field_names_checklist_item(field: str) -> bool:
    """Field/Location names a specific checklist test (not cover/defects scalars)."""
    text = (field or "").lower()
    if any(k in text for k in ("defects checklist", "cover page", "inspection details", "front page")):
        return False
    if any(k in text for k in ("checklist", "checkpoints", " test", "test ", " check", "checkpoint")):
        return True
    return bool(re.search(r"\b(test|check)\b", field or "", re.I))


def _field_targets_checklist_item(field: str, what: str) -> bool:
    """True when evidence lives on a checklist item, not a report scalar."""
    if not _field_names_checklist_item(field):
        return False
    return match_report_locus(field, what) is None


def ground_where(
    *,
    client: str,
    root: Path,
    field: str,
    what: str,
    section_names: list[str] | None = None,
) -> list[Any] | None:
    """Return a where list grounded in real report structure, or None if unmapped."""
    suffix = infer_evidence_field(field, what)

    report_sel = match_report_locus(field, what)
    if report_sel:
        return [report_sel]

    names = load_checklist_names(root, client)
    item = match_checklist_item(field, names) if names else None
    if item:
        return [intent_where(item, suffix, kind="checklist")]

    if _field_targets_checklist_item(field, what):
        return [intent_from_prose(field, what, suffix)]

    section = match_section(field, section_names)
    if section:
        return [intent_where(section, suffix, kind="section")]

    return None


def resolve_locus(
    *,
    client: str,
    root: Path,
    field: str,
    what: str,
    section_names: list[str] | None = None,
) -> list[Any]:
    """Always return a where list — never leave a rule unmapped.

    Last resort is report.inspector_text (in-report, checkable/unauthored).
    """
    grounded = ground_where(
        client=client,
        root=root,
        field=field,
        what=what,
        section_names=section_names,
    )
    if grounded:
        return grounded
    text = f"{field or ''} {what or ''}".lower()
    if any(k in text for k in ("photo", "picture", "image", "caption")):
        return ["report.all_captions"]
    if any(k in text for k in ("attach", "file", "pdf", "xlsx", "excel")):
        return ["report.attachment_filenames"]
    return ["report.inspector_text"]
