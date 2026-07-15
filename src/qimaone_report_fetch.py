#!/usr/bin/env python3
"""Fetch QIMAone inspection report JSON into data/clients/_inbox.

The helper intentionally calls the JSON API only. If a PDF/detail URL is supplied, it is
used only to extract a candidate inspection id; the URL itself is never fetched.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from dotenv import load_dotenv


_QIMAONE_HIGH_LEVEL_API_PREFIX = "/api/high-level"
_GUID_RE = re.compile(
    r"(?i)\b(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b"
)
_NUMERIC_RE = re.compile(r"\b\d{5,}\b")
DEFAULT_TENANT_ID = "1058"
DEFAULT_TENANT_PROFILE = "BRAND"
_QSP_NAME_TO_FIELD = {
    "order_Id": "order_id",
    "qspInspectionId": "qsp_inspection_id",
    "brandId": "brand_id",
    "brandType": "brand_type",
    "requestId": "request_id",
    "performedIn": "performed_in",
}


@dataclass(frozen=True)
class QspRequest:
    order_id: str = ""
    qsp_inspection_id: str = ""
    brand_id: str = DEFAULT_TENANT_ID
    brand_type: str = DEFAULT_TENANT_PROFILE
    request_id: str = ""
    performed_in: str = "QIMAONE"

    def validate_for_fetch(self) -> None:
        missing = [
            name
            for name, value in (
                ("qsp_inspection_id", self.qsp_inspection_id),
            )
            if not str(value).strip()
        ]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")


def snippet(text: str, n: int = 500) -> str:
    return (text or "")[:n]


def project_root() -> Path:
    from clients import project_root as _project_root

    return _project_root()


def load_project_env(root: Optional[Path] = None) -> None:
    load_dotenv((root or project_root()) / ".env")


def qimaone_origin() -> str:
    """QIMAone API origin (scheme + host only) from QIMAONE_HOST."""
    raw = os.environ.get("QIMAONE_HOST", "").strip().rstrip("/")
    if not raw:
        raise RuntimeError(
            "Set QIMAONE_HOST in .env, e.g. https://app.qimaone.com. "
            "Do not use PDF URLs or sso.qima.com here."
        )
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"QIMAONE_HOST must be an absolute app origin, got: {raw!r}")
    if parsed.netloc.lower().startswith("sso."):
        raise RuntimeError("QIMAONE_HOST must be the app origin, e.g. https://app.qimaone.com, not SSO.")
    return f"{parsed.scheme}://{parsed.netloc}"


def qimaone_api_token() -> str:
    for key in ("QIMAONE_API_TOKEN", "QSP_API_TOKEN", "API_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    raise RuntimeError("Set QIMAONE_API_TOKEN (or QSP_API_TOKEN / API_TOKEN) in .env")


def is_native_qimaone_inspection_request(qsp_request: QspRequest) -> bool:
    return (
        qsp_request.performed_in.strip().upper() == "QIMAONE"
        and qsp_request.qsp_inspection_id.strip().isdigit()
    )


def qimaone_inspection_report_url(qsp_request: QspRequest) -> str:
    report_id = qsp_request.qsp_inspection_id.strip()
    url = f"{qimaone_origin()}{_QIMAONE_HIGH_LEVEL_API_PREFIX}/inspections/{report_id}/report"
    if is_native_qimaone_inspection_request(qsp_request):
        url = f"{url}?{urlencode({'resolveBy': 'qimaoneInspectionId'})}"
    return url


def parse_qsp_request_rows(rows: Any) -> QspRequest:
    """Parse QSP inbound [{name, value}, ...] rows into a fetch request."""
    if not isinstance(rows, list):
        raise TypeError(f"QSP request must be a JSON array, got {type(rows).__name__}")

    values: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"QSP request row {index} must be an object, got {type(row).__name__}")
        name = row.get("name")
        value = row.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            raise TypeError(f"QSP request row {index} must have string name and value")
        field = _QSP_NAME_TO_FIELD.get(name.strip())
        if field:
            values[field] = value.strip()

    request = QspRequest(**values)
    request.validate_for_fetch()
    return request


def _query_values(parsed_url: Any, names: Iterable[str]) -> list[str]:
    query = parse_qs(parsed_url.query)
    values: list[str] = []
    for name in names:
        values.extend(query.get(name, []))
    return [value.strip() for value in values if value.strip()]


def resolve_inspection_id(value: str) -> str:
    """Resolve an inspection id from a UUID/numeric id or a URL containing one."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Inspection id or URL is required")

    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        preferred = _query_values(
            parsed,
            (
                "qspInspectionId",
                "qsp_inspection_id",
                "qimaoneInspectionId",
                "inspectionId",
                "inspection_id",
                "productId",
                "product_id",
                "id",
            ),
        )
        for candidate in preferred:
            match = _GUID_RE.search(candidate) or _NUMERIC_RE.search(candidate)
            if match:
                return match.group(0).replace("-", "").upper()

        match = _GUID_RE.search(raw)
        if match:
            return match.group(0).replace("-", "").upper()
        match = _NUMERIC_RE.search(parsed.path)
        if match:
            return match.group(0)
        raise ValueError(f"Could not find a GUID or numeric inspection id in URL: {raw}")

    normalized = raw.replace("-", "")
    if re.fullmatch(r"(?i)[0-9a-f]{32}", normalized):
        return normalized.upper()
    if raw.isdigit():
        return raw
    raise ValueError(f"Expected a GUID, numeric QIMAone id, or URL containing one; got: {raw!r}")


def fetch_inspection_report_json(qsp_request: QspRequest, *, timeout_seconds: int = 60) -> dict[str, Any]:
    qsp_request.validate_for_fetch()
    url = qimaone_inspection_report_url(qsp_request)
    headers = {
        "ApiToken": qimaone_api_token(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
    }
    if qsp_request.brand_id.strip():
        headers["TenantId"] = qsp_request.brand_id.strip()
    if qsp_request.brand_type.strip():
        headers["TenantProfile"] = qsp_request.brand_type.strip()

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"QIMAone report GET failed {response.status_code} for {url}: {snippet(response.text)}"
        ) from exc

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"QIMAone report GET did not return JSON for {url}. "
            f"Check QIMAONE_HOST and ApiToken. Body: {snippet(response.text)}"
        ) from exc

    if not isinstance(data, dict):
        raise TypeError(f"QIMAone report JSON root must be an object, got {type(data).__name__}")
    return data


def default_output_path(qsp_request: QspRequest, output_dir: Optional[Path] = None) -> Path:
    target_dir = output_dir or project_root() / "data" / "Reports"
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", qsp_request.qsp_inspection_id.strip())
    return target_dir / f"{safe_id}_report.json"


def write_report_json(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


