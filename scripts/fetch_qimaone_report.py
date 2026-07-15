#!/usr/bin/env python3
"""Fetch a QIMAone inspection report JSON into data/clients/_inbox."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qimaone_report_fetch import (  # noqa: E402
    DEFAULT_TENANT_ID,
    DEFAULT_TENANT_PROFILE,
    QspRequest,
    default_output_path,
    fetch_inspection_report_json,
    load_project_env,
    parse_qsp_request_rows,
    qimaone_inspection_report_url,
    resolve_inspection_id,
    write_report_json,
)


def request_from_args(args: argparse.Namespace) -> QspRequest:
    if args.qsp_rows:
        rows = json.loads(args.qsp_rows.read_text(encoding="utf-8"))
        return parse_qsp_request_rows(rows)

    inspection_id = resolve_inspection_id(args.inspection)
    request = QspRequest(
        qsp_inspection_id=inspection_id,
        brand_id=args.brand_id or DEFAULT_TENANT_ID,
        brand_type=args.brand_type or DEFAULT_TENANT_PROFILE,
        request_id=args.request_id or "",
        performed_in=args.performed_in,
    )
    request.validate_for_fetch()
    return request


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch QIMAone inspection report JSON into data/clients/_inbox."
    )
    parser.add_argument(
        "inspection",
        nargs="?",
        help="QSP inspection GUID, numeric QIMAone inspection id, or URL containing one.",
    )
    parser.add_argument("--brand-id", default=DEFAULT_TENANT_ID)
    parser.add_argument("--brand-type", default=DEFAULT_TENANT_PROFILE)
    parser.add_argument("--request-id", default="")
    parser.add_argument("--performed-in", default="QIMAONE")
    parser.add_argument("--qsp-rows", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    load_project_env()
    args = parse_args(argv or sys.argv[1:])
    if not args.qsp_rows and not args.inspection:
        print("error: provide an inspection id/URL or --qsp-rows", file=sys.stderr)
        return 2

    qsp_request = request_from_args(args)
    output_path = args.output or default_output_path(qsp_request, args.output_dir)
    report = fetch_inspection_report_json(qsp_request)
    write_report_json(report, output_path)

    print(f"Fetched {qsp_request.qsp_inspection_id} from {qimaone_inspection_report_url(qsp_request)}")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
