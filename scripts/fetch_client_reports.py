#!/usr/bin/env python3
"""One-off: fetch the batch of QIMAone reports supplied per client into corrected/.

The first GUID in each report.files.qima.com PDF path is the QIMAone fetch id.
Reports are saved under data/clients/<client>/corrected/<name>.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qimaone_report_fetch import (  # noqa: E402
    QspRequest,
    fetch_inspection_report_json,
    load_project_env,
)

# (client, fetch_guid, save_name_or_None). None name -> derive Q-number from JSON.
JOBS: list[tuple[str, str, str | None]] = [
    ("cemaco", "5E2F5E417ED24ED99485CD5355397BF0", "Q2605650175"),
    ("cemaco", "7E0CB6AAB45E479E80A3D3CAB88BA0BA", "Q2601959645"),
    ("cemaco", "23E70B1D7B9F4941908915149A3F3DF6", "Q2610766318"),
    ("new_era", "72627A2137AC4E7AA6F20A00D7636C6C", "Q2616262288"),
    ("new_era", "3ECCA7D117814A4EB6631DA21A03D65B", "Q2616292623"),
    ("new_era", "EC4EC22EBBE1443BBBCD3FECEDF0D160", "Q2616171227"),
    ("tpw", "661C171D125E42DD9FA1474E7B6BD2BA", "Q2614472847_4"),
    ("tpw", "CBEE289AC72C4A50AD9DB431AE452B66", "Q2614472847_2"),
    ("tpw", "C4B82D32E5BB449D893D2931CE872BA3", "Q2611142925"),
    ("dfi", "1C524C2CC0244EAFBD9850893F408630", "Q2615301660"),
    ("dfi", "66DD4D08AD054FE09B06A92B8D8501C2", "Q2616195180"),
    ("dfi", "4F9436DFC8204CA7BFD6F868B21FD5CA", "Q2614313993"),
    # Hallmark PDFs have no Q-number in the filename -> derive from JSON.
    ("hallmark", "1AFA51F5DC3A4748B43A6A1B649A4D84", None),
    ("hallmark", "439D7524649C4CD193EA1D44D02DDB18", None),
    ("hallmark", "F21D107921604CB1A01C1723B7E17E54", None),
]


def _derive_q_number(data: dict) -> str | None:
    blob = json.dumps(data)
    matches = re.findall(r"Q\d{9,10}", blob)
    return matches[0] if matches else None


def main() -> None:
    load_project_env()
    for client, guid, name in JOBS:
        req = QspRequest(qsp_inspection_id=guid, performed_in="QIMAONE")
        print(f"...   {client:8} {guid} fetching", flush=True)
        try:
            data = fetch_inspection_report_json(req, timeout_seconds=25)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {client:8} {guid} -> {exc!r}"[:200], flush=True)
            continue
        save_name = name or _derive_q_number(data) or f"report_{guid[:8]}"
        out = ROOT / "data/clients" / client / "corrected" / f"{save_name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        prods = data.get("products") or []
        print(f"OK    {client:8} {save_name:16} status={data.get('status')} result={data.get('result')} products={len(prods)}")


if __name__ == "__main__":
    main()
