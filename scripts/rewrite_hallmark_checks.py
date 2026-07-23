#!/usr/bin/env python3
"""Rewrite Hallmark ```check``` blocks with Gemini (gemini-pro-latest).

Reads prose + current check from rules.md, asks the model for a clean
where/when/check block per checkpoint (DSL only), validates, patches rules.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from check_block import parse_check_block_text, validate_block  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from google import genai  # noqa: E402
from semantic_report import parse_semantic_report  # noqa: E402

RULES_MD = ROOT / "data/clients/hallmark/gi/rules.md"
LIBRARY = ROOT / "data/library"
SAMPLE_REPORT = ROOT / "data/clients/July17_Hallamark/Q2617160220_11.json"
AUTHOR_MODEL = "gemini-pro-latest"
BATCH_SIZE = 8


SYSTEM_PROMPT = """You author GI check blocks for Hallmark inspection reports.

Output ONLY a JSON array. Each element:
  {"id": "<checkpoint id>", "check": "<yaml body with keys where / when / check>"}

The "check" value must be the body of a ```check fence (no fences), keys ONLY:
  where / when / check

Role split (mandatory):
  - You ground facts or pick deterministic ops.
  - Python decides pass/fail. You never grade the whole GI.

Priority: deterministic → extract+contains/matches → extract_bool (rare) →
vision → check:null with real where.

Banned phrases in any LLM question:
  satisfy the GI / satisfy the requirement / correctly / does this pass /
  according to the rule / Does the bound remark/comment satisfy /
  Does this field evidence satisfy

If Correct example / What-to-check gives an exact mandatory sentence, use
contains("that exact sentence") or extract+contains — never extract_bool alone.

Bind where to the Field/Location item (intent checklist match or report.*),
not to a whole section, unless the GI says "every test / all checkpoints".

Photo rules → photo_count or photo_captions or photo_content — never product_label.
External booking/spec/email/SOP → out_of_report:<kind>, check: null.
If unsure: set where to the closest real field and check: null.

Hallmark-specific tips:
  - HCLP / HA are checklist items: match [hclp] or [high, attention]; values Yes/No.
  - When HCLP=Yes: photos must be absent / blank placeholder ("HCLP, no photo").
  - SR / FR / Documents Availability are checklist items with result PASS/FAIL.
  - Prefer intent bindings:
      where:
        - kind: checklist
          match: [sr, test, report]
          field: result
  - Do NOT invent report fields outside the closed list provided.
  - Many Hallmark rules need the spec sheet / IRF / booking → honest out_of_report + check:null.
  - Prefer checkable ops when evidence is in-report (result, values, photo_count, present, equals, in_set, count_at_most, scan_absent, contains).

Use only operators from the operators list and fields from the fields list.
"""


def _load_library_bundle() -> str:
    parts = []
    for name in ("operators.yaml", "report_fields.yaml"):
        parts.append(f"===== {name} =====\n{(LIBRARY / name).read_text(encoding='utf-8')}")
    # Shortened authoring contract (skip long gold examples to save tokens)
    fmt = (LIBRARY / "check_format.yaml").read_text(encoding="utf-8")
    # keep first ~120 lines of contract
    lines = fmt.splitlines()
    parts.append("===== check_format.yaml (excerpt) =====\n" + "\n".join(lines[:120]))
    return "\n\n".join(parts)


def _sample_checklist_names() -> list[str]:
    if not SAMPLE_REPORT.is_file():
        return []
    report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    sem = parse_semantic_report(report)
    return sorted({(i.item_name or "").strip() for i in sem.checklist_items if (i.item_name or "").strip()})


def _parse_entries(markdown: str) -> list[dict[str, str]]:
    idx = markdown.find("## Executable check blocks")
    if idx < 0:
        raise ValueError("Executable check blocks section not found")
    section = markdown[idx:]
    parts = re.split(r"(?=\*\*ID:\*\*)", section)
    entries: list[dict[str, str]] = []
    for part in parts:
        m = re.match(r"\*\*ID:\*\*\s*(.+)", part)
        if not m:
            continue
        cid = m.group(1).strip()
        field = re.search(r"\*\*Field / Location:\*\*\s*(.+)", part)
        what = re.search(r"\*\*What to check:\*\*\s*(.+)", part)
        scope = re.search(r"\*\*Scope:\*\*\s*`?([^`\n]+)`?", part)
        block = re.search(r"```check\n(.*?)```", part, re.S)
        entries.append(
            {
                "id": cid,
                "field": field.group(1).strip() if field else "",
                "what": what.group(1).strip() if what else "",
                "scope": scope.group(1).strip() if scope else "",
                "old_check": block.group(1).strip() if block else "",
            }
        )
    return entries


def _normalize_check_yaml(raw: str) -> str:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:check|yaml)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Ensure three keys exist
    if "where:" not in text:
        raise ValueError("missing where")
    if "when:" not in text:
        text = text.rstrip() + "\nwhen: null"
    if "check:" not in text:
        text = text.rstrip() + "\ncheck: null"
    return text.strip() + "\n"


def _validate_authored(cp_id: str, check_yaml: str) -> list[str]:
    try:
        block = parse_check_block_text(check_yaml)
    except Exception as exc:  # noqa: BLE001
        return [f"parse: {exc}"]
    return [f"{e.get('field')}: {e.get('message')}" for e in validate_block(block, checkpoint_id=cp_id)]


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    raw = (text or "").strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # Find outermost array
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end < 0:
        raise ValueError(f"No JSON array in model response: {raw[:200]!r}")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, list):
        raise TypeError("expected JSON array")
    return data


def _author_batch(
    client: genai.Client,
    *,
    model: str,
    library: str,
    checklist_names: list[str],
    batch: list[dict[str, str]],
) -> dict[str, str]:
    payload = [
        {
            "id": e["id"],
            "field_location": e["field"],
            "what_to_check": e["what"],
            "scope": e["scope"],
            "current_check": e["old_check"],
        }
        for e in batch
    ]
    user = (
        f"{library}\n\n"
        f"===== Sample Hallmark checklist item names (from a real report) =====\n"
        f"{json.dumps(checklist_names, indent=2)}\n\n"
        f"===== Checkpoints to author ({len(batch)}) =====\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Rewrite each checkpoint's check block. Return JSON array only."
    )
    response = client.models.generate_content(
        model=model,
        contents=user,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    rows = _extract_json_array(response.text or "")
    out: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("id") or "").strip()
        check = row.get("check")
        if not cid or check is None:
            continue
        out[cid] = _normalize_check_yaml(str(check))
    return out


def _patch_rules_md(markdown: str, new_blocks: dict[str, str]) -> str:
    """Replace ```check ... ``` blocks for known IDs in the executable section."""

    def replacer(match: re.Match[str]) -> str:
        header = match.group(1)
        cid_m = re.search(r"\*\*ID:\*\*\s*([^\n]+)", header)
        if not cid_m:
            return match.group(0)
        cid = cid_m.group(1).strip()
        if cid not in new_blocks:
            return match.group(0)
        body = new_blocks[cid].rstrip() + "\n"
        return f"{header}```check\n{body}```"

    # From executable section onward: each entry is header + check fence
    idx = markdown.find("## Executable check blocks")
    if idx < 0:
        raise ValueError("Executable section missing")
    head, tail = markdown[:idx], markdown[idx:]
    pattern = re.compile(
        r"(\*\*ID:\*\*[^\n]*\n(?:(?!```check)[^\n]*\n)*?)```check\n.*?```",
        re.S,
    )
    new_tail = pattern.sub(replacer, tail)
    return head + new_tail


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=AUTHOR_MODEL)
    parser.add_argument("--limit", type=int, default=0, help="Only first N checkpoints (0=all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only-null", action="store_true", help="Only rewrite check:null entries")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    markdown = RULES_MD.read_text(encoding="utf-8")
    entries = _parse_entries(markdown)
    if args.only_null:
        entries = [e for e in entries if re.search(r"check:\s*null", e["old_check"])]
    if args.limit:
        entries = entries[: args.limit]

    library = _load_library_bundle()
    names = _sample_checklist_names()
    client = genai.Client(api_key=api_key)

    print(f"Rewriting {len(entries)} Hallmark checks with {args.model}")
    print(f"Sample checklist names: {len(names)}")

    authored: dict[str, str] = {}
    failed: list[str] = []

    for i in range(0, len(entries), args.batch_size):
        batch = entries[i : i + args.batch_size]
        ids = [e["id"] for e in batch]
        print(f"  batch {i // args.batch_size + 1}: {ids[0]} … {ids[-1]}", flush=True)
        try:
            result = _author_batch(
                client,
                model=args.model,
                library=library,
                checklist_names=names,
                batch=batch,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"    FAIL batch: {exc}")
            failed.extend(ids)
            time.sleep(2)
            continue

        for e in batch:
            cid = e["id"]
            if cid not in result:
                failed.append(cid)
                print(f"    missing {cid}")
                continue
            errs = _validate_authored(cid, result[cid])
            if errs:
                # keep if parseable; soft-warn
                print(f"    warn {cid}: {errs[:2]}")
            authored[cid] = result[cid]
        time.sleep(0.4)

    print(f"Authored {len(authored)} / {len(entries)}; failed {len(failed)}")
    if args.dry_run:
        preview = list(authored.items())[:3]
        for cid, body in preview:
            print(f"--- {cid} ---\n{body}")
        return 0

    # Backup then patch
    backup = RULES_MD.with_suffix(".md.bak_pre_rewrite")
    backup.write_text(markdown, encoding="utf-8")
    patched = _patch_rules_md(markdown, authored)
    RULES_MD.write_text(patched, encoding="utf-8")
    print(f"Wrote {RULES_MD}")
    print(f"Backup {backup}")

    summary = {
        "model": args.model,
        "authored": len(authored),
        "failed": failed,
        "sample_checklist_names": names,
    }
    out = ROOT / "data/clients/hallmark/gi/rewrite_checks_summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Summary {out}")
    return 0 if authored else 1


if __name__ == "__main__":
    raise SystemExit(main())
