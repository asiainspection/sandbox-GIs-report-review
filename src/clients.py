"""Client discovery and path helpers for the GI review repo.

Canonical layout:
  data/clients/{id}/client.json
  data/clients/{id}/gi/rules.md (+ optional hand_specs.json, source_gi.md)
  data/clients/{id}/corrected/*.json
  data/clients/{id}/flawed/*_flawed.json
  data/clients/{id}/pdfs/*.pdf   (optional)
  data/pipeline/{checkpoints,checkspecs,reports,results,semantic,eval}/
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """Directory that contains the ``data/`` tree.

    Resolution order:
      1. ``GI_DATA_ROOT`` env var (folder that contains ``data/``)
      2. nearest ancestor of this file with ``data/clients``
      3. nearest ancestor of cwd with ``data/clients``
      4. parent of ``src/`` (normal checkout)
    """
    env = os.environ.get("GI_DATA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "data" / "clients").is_dir():
            return parent
    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        if (parent / "data" / "clients").is_dir():
            return parent
    return here.parents[1]


def clients_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "clients"


def pipeline_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "pipeline"


@dataclass(frozen=True)
class ClientConfig:
    """Normalized per-client input + derived pipeline paths."""

    id: str
    name: str
    root_dir: Path
    gi_rules: Path
    hand_specs: Path | None
    source_gi: Path | None
    corrected_dir: Path
    flawed_dir: Path
    pdfs_dir: Path | None
    introduced_checkpoints: dict[str, dict[str, str]] = field(default_factory=dict)
    holdout_keys: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def checkpoints_path(self) -> Path:
        return pipeline_dir() / "checkpoints" / f"{self.id}_checkpoints.json"

    @property
    def checkspecs_path(self) -> Path:
        return pipeline_dir() / "checkspecs" / f"{self.id}_checkspecs.json"

    def corrected_reports(self) -> list[Path]:
        if not self.corrected_dir.exists():
            return []
        return sorted(p for p in self.corrected_dir.glob("*.json") if p.is_file())

    def flawed_reports(self) -> list[tuple[Path, str]]:
        """Return (path, label_key) for flawed JSON reports."""
        if not self.flawed_dir.exists():
            return []
        out: list[tuple[Path, str]] = []
        labels = self.introduced_checkpoints
        for path in sorted(self.flawed_dir.glob("*_flawed.json")):
            stem = path.stem  # e.g. Q2614146161_flawed
            key = f"report_{stem.lower()}"
            if key not in labels:
                # stem already ends with _flawed → report_q..._flawed
                # also try without double-suffix drift
                alt = f"report_{path.stem.replace('_flawed', '').lower()}_flawed"
                key = alt if alt in labels else (key if key in labels else path.stem)
            # DFI-style: bare key without report_ prefix
            if key not in labels and path.stem in labels:
                key = path.stem
            if key not in labels:
                # last resort: stem without _flawed if present
                bare = path.stem
                if bare in labels:
                    key = bare
            out.append((path, key))
        return out

    def label_ids(self, label_key: str) -> set[str]:
        raw = self.introduced_checkpoints.get(label_key) or {}
        if isinstance(raw, dict):
            return set(raw.keys())
        if isinstance(raw, list):
            return set(str(x) for x in raw)
        return set()


def list_clients(root: Path | None = None) -> list[str]:
    base = clients_dir(root)
    if not base.exists():
        return []
    return sorted(
        p.name
        for p in base.iterdir()
        if p.is_dir() and (p / "client.json").exists()
    )


def load_client(client_id: str, root: Path | None = None) -> ClientConfig:
    root = root or project_root()
    client_root = clients_dir(root) / client_id
    meta_path = client_root / "client.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing client.json for {client_id}: {meta_path}")
    data = json.loads(meta_path.read_text(encoding="utf-8"))

    gi_rules_rel = data.get("gi_rules") or data.get("rules_md") or "gi/rules.md"
    gi_rules = _resolve(client_root, root, gi_rules_rel)
    if not gi_rules.exists():
        # Convention fallback
        candidate = client_root / "gi" / "rules.md"
        if candidate.exists():
            gi_rules = candidate

    hand_specs = None
    hand_rel = data.get("hand_specs")
    if hand_rel:
        hand_specs = _resolve(client_root, root, hand_rel)
    else:
        default_hand = client_root / "gi" / "hand_specs.json"
        if default_hand.exists():
            hand_specs = default_hand

    source_gi = None
    if data.get("source_gi"):
        source_gi = _resolve(client_root, root, data["source_gi"])
    elif (client_root / "gi" / "source_gi.md").exists():
        source_gi = client_root / "gi" / "source_gi.md"

    corrected = client_root / str(data.get("corrected_dir") or "corrected")
    flawed = client_root / str(data.get("flawed_dir") or "flawed")
    pdfs = client_root / "pdfs"
    pdfs_dir = pdfs if pdfs.exists() else None

    extra = {
        k: v
        for k, v in data.items()
        if k
        not in {
            "id",
            "name",
            "gi_rules",
            "rules_md",
            "hand_specs",
            "source_gi",
            "corrected_dir",
            "flawed_dir",
            "introduced_checkpoints",
            "holdout_keys",
        }
    }

    return ClientConfig(
        id=str(data.get("id") or client_id),
        name=str(data.get("name") or client_id),
        root_dir=client_root,
        gi_rules=gi_rules,
        hand_specs=hand_specs,
        source_gi=source_gi,
        corrected_dir=corrected,
        flawed_dir=flawed,
        pdfs_dir=pdfs_dir,
        introduced_checkpoints=dict(data.get("introduced_checkpoints") or {}),
        holdout_keys=list(data.get("holdout_keys") or []),
        meta=extra,
    )


def load_all_clients(root: Path | None = None, ids: list[str] | None = None) -> list[ClientConfig]:
    root = root or project_root()
    wanted = ids or list_clients(root)
    return [load_client(cid, root) for cid in wanted]


def ensure_pipeline_dirs(root: Path | None = None) -> Path:
    pipe = pipeline_dir(root)
    for name in ("checkpoints", "checkspecs", "reports", "results", "semantic", "eval", "findings"):
        (pipe / name).mkdir(parents=True, exist_ok=True)
    return pipe


def checkspecs_cache_path(checkpoints_path: Path, root: Path | None = None) -> Path:
    """Derive checkspecs path from a checkpoints file stem under data/pipeline/checkspecs/."""
    stem = checkpoints_path.stem.replace("_checkpoints", "")
    # Normalize ribkoff_v2 → ribkoff when migrating
    if stem.endswith("_v2"):
        stem = stem[:-3]
    return pipeline_dir(root) / "checkspecs" / f"{stem}_checkspecs.json"


def _resolve(client_root: Path, project: Path, rel: str) -> Path:
    path = Path(rel)
    if path.is_absolute():
        return path
    # Prefer paths relative to the client folder (gi/rules.md)
    under_client = client_root / path
    if under_client.exists() or not str(rel).startswith("data/"):
        if under_client.exists() or "/" in rel or rel.startswith("gi/"):
            return under_client
    # Legacy absolute-from-repo paths (data/GI/...)
    return project / path
