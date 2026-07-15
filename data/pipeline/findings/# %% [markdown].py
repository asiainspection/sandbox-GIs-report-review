# %% [markdown]
# # Markdown Rules + Report JSON Pipeline
# 
# This notebook runs the full local review pipeline:
# 
# 1. Parse inspection review rules from Markdown.
# 2. Convert those parsed rules into `gi_review` checkpoints.
# 3. Convert one or many QIMAone report JSON files into LLM-friendly report Markdown.
# 4. Run Gemini review for each report and output flagged comments.
# 
# Set `REPORT_INPUTS` to a JSON file, a directory of JSON files, or a list mixing both. If you only have a signed PDF URL, fetch the JSON first with `src/qimaone_report_fetch.py`, then point `REPORT_INPUTS` at the created file or folder.

# %%
from pathlib import Path
import json
import re
import sys
from datetime import datetime

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from md_rules_to_json import parse_rules
from report_to_md import convert_report_to_markdown
from gi_review import format_cost_summary, load_env, run_all_checkpoints

# Pick one JSON file, one directory of JSON files, or a list mixing files/directories.
REPORT_INPUTS = PROJECT_ROOT / "data/reports/ribkoff"

# Pick the Markdown rulebook to test.
RULES_MD = PROJECT_ROOT / "data/GI/Joseph_Ribkoff_Inspection_Rules_Reference.md"

# Keep this small while iterating. Set to None for all generated checkpoints.
CHECKPOINT_LIMIT = 10
MAX_WORKERS = 4

GENERATED_DIR = PROJECT_ROOT / "data/output/notebook_pipeline"
REPORT_MD_DIR = GENERATED_DIR / "reports_md"
RESULTS_DIR = GENERATED_DIR / "results"
COMMENTS_DIR = GENERATED_DIR / "comments"
RULES_JSON = GENERATED_DIR / f"{RULES_MD.stem}_parsed_rules.json"
CHECKPOINTS_JSON = GENERATED_DIR / f"{RULES_MD.stem}_checkpoints.json"
AGGREGATE_RESULTS_JSON = GENERATED_DIR / f"{RULES_MD.stem}_aggregate_review_results.json"
AGGREGATE_COMMENTS_MD = GENERATED_DIR / f"{RULES_MD.stem}_aggregate_comments.md"

for directory in (GENERATED_DIR, REPORT_MD_DIR, RESULTS_DIR, COMMENTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def resolve_report_inputs(inputs) -> list[Path]:
    if isinstance(inputs, (str, Path)):
        candidates = [Path(inputs)]
    else:
        candidates = [Path(item) for item in inputs]

    report_paths: list[Path] = []
    for candidate in candidates:
        candidate = candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
        if candidate.is_dir():
            report_paths.extend(sorted(candidate.glob("*.json")))
        elif candidate.is_file():
            report_paths.append(candidate)
        else:
            raise FileNotFoundError(f"Report input not found: {candidate}")

    unique_paths = list(dict.fromkeys(path.resolve() for path in report_paths))
    if not unique_paths:
        raise FileNotFoundError(f"No report JSON files found in: {inputs}")
    return unique_paths


REPORT_JSONS = resolve_report_inputs(REPORT_INPUTS)

print("Project root:", PROJECT_ROOT)
print("Report inputs:", REPORT_INPUTS)
print("Reports found:", len(REPORT_JSONS))
for report_path in REPORT_JSONS:
    print(" -", report_path.relative_to(PROJECT_ROOT))
print("Rules MD:", RULES_MD)
print("Checkpoint limit:", CHECKPOINT_LIMIT)
print("Output dir:", GENERATED_DIR)

# %% [markdown]
# ## 1. Parse Markdown Rules
# 
# `md_rules_to_json.py` produces a deterministic `rules` array. The review runner expects `checkpoints`, so the next cell saves both the parsed rules and an adapted checkpoint file.

# %%
from rules_to_checkpoints import rules_to_checkpoints

parsed_rules = parse_rules(RULES_MD.read_text(encoding="utf-8"))
parsed_rules["source_file"] = str(RULES_MD)
checkpoints = rules_to_checkpoints(parsed_rules["rules"])

checkpoint_payload = {
    "meta": {
        "name": parsed_rules.get("title") or RULES_MD.stem,
        "source": str(RULES_MD),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "schema": [
            "id",
            "section",
            "requirement",
            "context",
            "lookup_table",
            "md_sections",
            "fail_if",
            "never_flag_if",
            "examples",
        ],
    },
    "checkpoints": checkpoints,
}

RULES_JSON.write_text(json.dumps(parsed_rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
CHECKPOINTS_JSON.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"Parsed rules: {parsed_rules['rule_count']}")
print(f"Generated checkpoints: {len(checkpoints)}")
print("Rules JSON:", RULES_JSON)
print("Checkpoints JSON:", CHECKPOINTS_JSON)
print("First checkpoint:")
print(json.dumps(checkpoints[0], indent=2, ensure_ascii=False) if checkpoints else "No checkpoints")

# %% [markdown]
# ## 2. Convert Report JSON To Markdown
# 
# The review model reads the compact Markdown representation, not raw report JSON. This cell writes one `*_llm.md` file per report under `output/notebook_pipeline/reports_md/`.

# %%
report_md_paths: dict[Path, Path] = {}

for report_json in REPORT_JSONS:
    with report_json.open(encoding="utf-8") as handle:
        raw_report = json.load(handle)

    report_md = convert_report_to_markdown(raw_report)
    report_md_path = REPORT_MD_DIR / f"{report_json.stem}_llm.md"
    report_md_path.write_text(report_md, encoding="utf-8")
    report_md_paths[report_json] = report_md_path

    print(f"{report_json.name}: json_bytes={report_json.stat().st_size:,} md_chars={len(report_md):,}")
    print("  ->", report_md_path.relative_to(PROJECT_ROOT))

first_report = REPORT_JSONS[0]
first_preview = report_md_paths[first_report].read_text(encoding="utf-8")[:1500]
print("\n--- First Report Preview:", first_report.name, "---\n")
print(first_preview)

# %% [markdown]
# ## 3. Run Review
# 
# This calls `gi_review.run_all_checkpoints` for each report. Keep `CHECKPOINT_LIMIT` small while debugging cost and prompt behavior; set it to `None` when you want all generated checkpoints for every report.

# %%
# Requires PROJECT_ROOT/.env with GEMINI_API_KEY and optional GEMINI_MODEL.
api_key, model = load_env(PROJECT_ROOT)
print("Model:", model)

all_summaries: list[dict] = []

for report_json in REPORT_JSONS:
    report_md_path = report_md_paths[report_json]
    print(f"\n=== Reviewing {report_json.name} ===")

    run = run_all_checkpoints(
        report_md_path,
        CHECKPOINTS_JSON,
        project_root=PROJECT_ROOT,
        limit=CHECKPOINT_LIMIT,
        max_workers=MAX_WORKERS,
    )
    summary = format_cost_summary(run)
    summary["inputs"] = {
        "report_json": str(report_json),
        "report_md": str(report_md_path),
        "rules_md": str(RULES_MD),
        "rules_json": str(RULES_JSON),
        "checkpoints_json": str(CHECKPOINTS_JSON),
    }

    results_json = RESULTS_DIR / f"{report_json.stem}_review_results.json"
    summary["outputs"] = {"results_json": str(results_json)}
    results_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    all_summaries.append(summary)

    print(f"Checkpoints run: {summary['checkpoints_run']}")
    print(f"Flags: {summary['flags_count']}")
    print(f"Errors: {len(summary['errors'])}")
    print("Cache created:", summary["cache_created"])
    print("Results JSON:", results_json.relative_to(PROJECT_ROOT))
    print("Total estimated cost USD:", round(summary["cost_usd"]["total"]["total_cost_usd"], 6))

aggregate = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "rules_md": str(RULES_MD),
    "reports_count": len(all_summaries),
    "checkpoint_limit": CHECKPOINT_LIMIT,
    "summaries": all_summaries,
}
AGGREGATE_RESULTS_JSON.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("\nAggregate results:", AGGREGATE_RESULTS_JSON.relative_to(PROJECT_ROOT))

# %% [markdown]
# ## 4. Output Comments
# 
# The model output is normalized into comments from flagged checkpoints. This cell writes one Markdown comments file per report and one aggregate comments file.

# %%
def comments_markdown(summary: dict) -> str:
    report_json = Path(summary["inputs"]["report_json"])
    flags = summary.get("flags", [])
    error_ids = summary.get("errors", [])

    lines = [
        f"# Review Comments: {report_json.stem}",
        "",
        f"- Report JSON: `{report_json.relative_to(PROJECT_ROOT)}`",
        f"- Rules MD: `{RULES_MD.relative_to(PROJECT_ROOT)}`",
        f"- Checkpoints run: {summary['checkpoints_run']}",
        f"- Flags: {summary['flags_count']}",
        f"- Errors: {len(error_ids)}",
        "",
    ]

    if flags:
        lines.append("## Flagged Comments")
        lines.append("")
        for index, flag in enumerate(flags, start=1):
            lines.extend(
                [
                    f"### {index}. {flag['checkpoint_id']}",
                    "",
                    f"**Section:** {flag.get('section', '')}",
                    "",
                    f"**Comment:** {flag.get('reason', '')}",
                    "",
                    f"**Evidence:** {flag.get('evidence', '')}",
                    "",
                ]
            )
    else:
        lines.extend(["## Flagged Comments", "", "No flagged comments.", ""])

    if error_ids:
        lines.append("## Checkpoint Errors")
        lines.append("")
        for checkpoint_id in error_ids:
            lines.append(f"- {checkpoint_id}")
        lines.append("")

    return "\n".join(lines)


aggregate_lines = [
    f"# Aggregate Review Comments: {RULES_MD.stem}",
    "",
    f"- Reports reviewed: {len(all_summaries)}",
    f"- Checkpoint limit: {CHECKPOINT_LIMIT}",
    "",
]

for summary in all_summaries:
    report_json = Path(summary["inputs"]["report_json"])
    comments_md = COMMENTS_DIR / f"{report_json.stem}_comments.md"
    text = comments_markdown(summary)
    comments_md.write_text(text, encoding="utf-8")
    summary.setdefault("outputs", {})["comments_md"] = str(comments_md)

    aggregate_lines.extend([
        f"## {report_json.stem}",
        "",
        f"- Comments file: `{comments_md.relative_to(PROJECT_ROOT)}`",
        f"- Flags: {summary['flags_count']}",
        f"- Errors: {len(summary.get('errors', []))}",
        "",
    ])
    aggregate_lines.extend(text.splitlines()[8:])
    aggregate_lines.append("")

AGGREGATE_COMMENTS_MD.write_text("\n".join(aggregate_lines), encoding="utf-8")
AGGREGATE_RESULTS_JSON.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("Aggregate comments MD:", AGGREGATE_COMMENTS_MD.relative_to(PROJECT_ROOT))
for summary in all_summaries:
    print("-", Path(summary["outputs"]["comments_md"]).relative_to(PROJECT_ROOT))
print("\n".join(aggregate_lines[:100]))

# %% [markdown]
# ## Optional: Fetch Report JSON First
# 
# If you have a signed PDF URL but not the JSON yet, run this in a terminal from the repo root before using the notebook:
# 
# ```bash
# .venv/bin/python src/qimaone_report_fetch.py "<signed PDF URL>" -o data/reports/ribkoff/<QREF>_Jun29.json
# ```
# 
# Then set `REPORT_INPUTS = PROJECT_ROOT / "data/reports/ribkoff"` to review every JSON in that folder. The helper uses `QIMAONE_HOST` and `QIMAONE_API_TOKEN` from `.env`, and this repo currently defaults to `TenantId=1058`, `TenantProfile=BRAND`.


