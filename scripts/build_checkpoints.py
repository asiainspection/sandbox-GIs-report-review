"""Build checkpoints JSON from rules.md (prose + ```check blocks)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from check_block import extract_check_blocks  # noqa: E402
from md_rules_to_json import parse_rules  # noqa: E402
from rules_to_checkpoints import rules_to_checkpoints  # noqa: E402


def build_checkpoints(rules_md: Path) -> dict:
    markdown = rules_md.read_text(encoding="utf-8")
    parsed = parse_rules(markdown)
    blocks = extract_check_blocks(markdown)
    checkpoints = rules_to_checkpoints(parsed["rules"], check_blocks=blocks)
    return {
        "meta": {
            "name": parsed.get("title") or rules_md.stem,
            "source": str(rules_md),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "check_blocks": len(blocks),
            "checkpoint_count": len(checkpoints),
        },
        "checkpoints": checkpoints,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build checkpoints JSON from rules.md")
    parser.add_argument("rules_md", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_checkpoints(args.rules_md)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {payload['meta']['checkpoint_count']} checkpoints ({payload['meta']['check_blocks']} with check blocks) -> {args.output}")


if __name__ == "__main__":
    main()
