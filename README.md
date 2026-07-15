# GI Inspection Report Review

Automated review of QIMAone inspection reports against client General Instructions (GIs).

## Layout

```
src/           library code (flat modules)
scripts/       CLI + fixture builders (run_review, eval_all, make_*, fetch_…)
tests/
data/clients/{id}/   client.json, gi/rules.md, corrected/, flawed/
                     # cemaco, dfi, hallmark, ribkoff, tpw, new_era
data/pipeline/       checkpoints, checkspecs, reports, results, eval, findings
notebooks/gi_eval.ipynb
notebooks/gi_findings_export.ipynb
```

## Production review

```bash
.venv/bin/python scripts/run_review.py \
  --report-json data/clients/ribkoff/corrected/Q2614146161.json \
  --checkpoints data/pipeline/checkpoints/ribkoff_checkpoints.json

# Offline P/R gate (no LLM):
.venv/bin/python scripts/eval_all.py \
  --gis ribkoff hallmark cemaco --arms policy_guard --offline --no-vision
```

Python entrypoint: `from review import review` (alias: `run_production_review`).

## Findings Excel (report-team handoff)

```bash
# open notebooks/gi_findings_export.ipynb
# → writes data/pipeline/findings/{client}_findings_*.xlsx
```

Columns: `Order # | Empty | 1 | What was checked | Checkpoint | Original Content | Non-confirmities | Suggested actions | Finding Verdict | Remark`  
(Verdict + Remark left blank for the report team.)

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -q
```
