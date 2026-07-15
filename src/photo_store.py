"""Download and index inspection photos from QIMAone ZIP documents."""

from __future__ import annotations

import io
import os
import re
import zipfile
from pathlib import Path
from typing import Any

import httpx

from qimaone_report_fetch import qimaone_api_token, qimaone_origin
from semantic_report import normalize_name

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
_TRAILING_INDEX = re.compile(r"[-_\s]?\d+$")


def _auth_headers() -> dict[str, str]:
    headers = {
        "ApiToken": qimaone_api_token(),
        "Accept": "*/*",
    }
    tenant = os.environ.get("QIMAONE_TENANT_ID", "1058").strip()
    profile = os.environ.get("QIMAONE_TENANT_PROFILE", "BRAND").strip()
    if tenant:
        headers["TenantId"] = tenant
    if profile:
        headers["TenantProfile"] = profile
    return headers


def normalize_photo_stem(name: str) -> str:
    """Normalize ZIP filename stem for matching checklist / focus terms."""
    stem = Path(name).stem
    stem = _TRAILING_INDEX.sub("", stem).strip()
    return normalize_name(stem)


def photo_cache_dir(project_root: Path, report: dict[str, Any]) -> Path:
    inspection_id = str(report.get("inspectionId") or report.get("reportId") or "unknown")
    return project_root / "data" / "cache" / "photos" / inspection_id


def download_photo_zip(
    report: dict[str, Any],
    dest_dir: Path,
    *,
    force: bool = False,
    timeout_seconds: int = 180,
) -> Path | None:
    """Download `zipDocumentUuid` photos archive and extract into dest_dir.

    Returns dest_dir on success, None when UUID missing or download fails.
    """
    uuid = str(report.get("zipDocumentUuid") or "").strip()
    if not uuid:
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    marker = dest_dir / ".extracted"
    if marker.exists() and not force and any(dest_dir.rglob("*")):
        return dest_dir

    url = f"{qimaone_origin()}/api/inspection/documents/{uuid}"
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=_auth_headers()) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.content
    except Exception:
        return None

    if len(payload) < 100 or not payload[:2] == b"PK":
        # Not a ZIP (HTML error page, etc.)
        return None

    zip_path = dest_dir / "photos.zip"
    zip_path.write_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        zf.extractall(dest_dir)
    marker.write_text(uuid, encoding="utf-8")
    return dest_dir


def index_photos(photo_dir: Path) -> dict[str, list[Path]]:
    """Map normalized stems → image paths under photo_dir."""
    index: dict[str, list[Path]] = {}
    if not photo_dir or not photo_dir.exists():
        return index
    for path in sorted(photo_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _IMAGE_EXTS:
            continue
        key = normalize_photo_stem(path.name)
        if not key:
            continue
        index.setdefault(key, []).append(path)
    return index


def _candidate_names(checkpoint: dict[str, Any], ir: dict[str, Any] | None = None) -> list[str]:
    names: list[str] = []
    for term in checkpoint.get("focus_terms") or []:
        text = str(term).strip()
        if text:
            names.append(text.split("/")[0].strip())
    req = str(checkpoint.get("requirement") or "")
    match = re.match(r"^([^—\-]+)", req)
    if match:
        head = match.group(1).strip()
        if len(head) >= 4:
            names.append(head)
    if ir:
        for node in ir.get("nodes") or []:
            node_name = str(node.get("name") or "")
            if not node_name:
                continue
            for term in names:
                if normalize_name(term) in normalize_name(node_name) or normalize_name(node_name) in normalize_name(
                    term
                ):
                    names.append(node_name)
    # Stable unique
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        key = normalize_name(name)
        if key and key not in seen:
            seen.add(key)
            out.append(name)
    return out


def photos_for_checkpoint(
    checkpoint: dict[str, Any],
    index: dict[str, list[Path]],
    *,
    ir: dict[str, Any] | None = None,
    max_photos: int = 6,
) -> list[Path]:
    """Resolve up to max_photos paths relevant to a checkpoint."""
    if not index:
        return []
    collected: list[Path] = []
    seen: set[Path] = set()
    for name in _candidate_names(checkpoint, ir):
        key = normalize_name(name)
        for stem, paths in index.items():
            if key == stem or key in stem or stem in key:
                for path in paths:
                    if path not in seen:
                        seen.add(path)
                        collected.append(path)
                        if len(collected) >= max_photos:
                            return collected
    # Fallback: if checklist photos are unindexed, return nothing (caller → unable)
    return collected


def ensure_report_photos(
    report: dict[str, Any],
    project_root: Path,
    *,
    enabled: bool | None = None,
) -> dict[str, list[Path]]:
    """Download ZIP when enabled and return stem→paths index (may be empty)."""
    if enabled is None:
        flag = os.environ.get("GI_VISION_ENABLED", "1").strip().lower()
        enabled = flag not in ("0", "false", "no", "off")
    if not enabled:
        return {}
    dest = photo_cache_dir(project_root, report)
    downloaded = download_photo_zip(report, dest)
    if not downloaded:
        return {}
    return index_photos(dest)
