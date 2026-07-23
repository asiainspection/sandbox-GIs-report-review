# Harness — compile prompt (Excel authoring for ops + AI)

You fill **GI authoring Excel rows** (or equivalent TSV). You only choose from closed lists
below. You do **not** invent Rule types, Check parts, or cover Look-at labels.

## Inject these library files (in order)

| # | File | Why |
|---|---|---|
| 1 | `data/library/harness_compile_prompt.md` | **This file** — output shape + bans |
| 2 | `data/library/harness_actions.md` | Rule type ↔ action + common Values |
| 3 | `data/library/harness_where.md` | Cover places + Check part suffixes |
| 4 | `data/library/gi_excel_authoring.md` | Ops examples (Conditions, Repeat for) |

## Also inject (per client job)

5. **Golden / human GI intent** (comments, old rules, Confluence notes)  
6. **One sample report** (simplified JSON or checklist name list) — for **exact** checkpoint titles and exact `Inspection type` string  
7. Optional: empty or template `gi_authoring_*.xlsx` column headers  

Do **not** invent checkpoint names. Copy them from the sample report.

---

## Mental model

- **Rule** = what must be true (ships to review).  
- **Condition (hidden)** = when a Rule runs; link with `@C1` / `@C1 AND @C2`.  
- **Repeat for** = iterator only (`each defect` …). **Not** PSI / product type.  
- Prefer deterministic Rule types; AI only when you cannot count/compare.

---

## Output — one Excel row (TSV or markdown table)

Emit rows with these columns (same as the Excel **Checks** sheet):

`id | row_type | section | rule | applies_when | for_each | look_at | check_part | rule_type | value | example`

### row_type

`Rule` · `Condition (hidden)`

### applies_when

- Blank = always  
- Or `@C1` · `@C1 AND @C2` · `@C1 OR @C2` · `NOT @C1`  
- **Never** free prose (`when defects are found`, `when the drop test passed`)

### for_each (Repeat for)

Blank · `each defect` · `each SKU / reference` · `each PO` · `each photo` · `each checkpoint in section`  

Use `each defect` + **At most N** / **At least N** when every defect row must pass a count check.  
Otherwise leave blank.

### look_at

- Cover / external: exact label from `harness_where.md` §2/§3 (e.g. `Inspection type`, `Factory address`, `Defects`, `Defect count`)  
- Checklist: **exact** checkpoint name from the sample report (e.g. `Carton drop test`)

### check_part

Blank for cover fields. Else one of:

`result` · `comment` · `values` · `photo count` · `photo caption` · `photo content` · `file name` · `file content`

| If rule_type is… | check_part must be… |
|---|---|
| At least N / At most N | `photo count` (or count field) |
| AI photo check | `photo content` |
| File name matches | `file name` |
| Must equal / Must be one of on a test | `result` |

### rule_type (Excel labels)

Map to harness actions in `harness_actions.md`. Prefer:

`Must be filled in` · `Must be in English` · `Must equal` · `Must be one of` · `Must contain text` · `Must not contain text` · `Number greater than` · `Number less than` · `Defect type includes` · `At least N` · `At most N` · `Ratio at least` · `File name matches` · `AI yes/no (flag if false)` · `AI photo check (flag if false)` · `Manual review`

### value — closed suggestions when possible

For **Must equal** / **Must be one of**, prefer:

`PASS` · `FAIL` · `Pending` · `N/A` · `NOT_APPLICABLE` · `PASS, FAIL` · `PASS, FAIL, Pending` · `Pre-Shipment Inspection` · `During Production Inspection`

For **At least N** / **At most N**, prefer: `0` · `1` · `2` · `3` · `5`

**Inspection type:** copy the **exact** string from the sample report (usually `Pre-Shipment Inspection`, **not** `PSI`).

Custom values are allowed for AI questions and filename patterns.

### example

`Wrong: … · Right: …` on Rules. **Leave blank** on Condition rows.

---

## Condition pattern (required for gated rules)

**PSI-only pack**

```
C_psi | Condition (hidden) | … | Inspection type | | Must equal | Pre-Shipment Inspection |
A.x   | Rule | … | @C_psi | | <look_at> | <part> | <rule_type> | <value> |
```

**No photos when carton drop passed**

```
C2    | Condition (hidden) | … | Carton drop test | result | Must equal | PASS |
A.5.1 | Rule | … | @C2 | | Carton drop test | photo count | At most N | 0 |
```

**Per-defect photo ceiling (deterministic)**

```
A.3.4 | Rule | … | | each defect | Defects | | At most N | 5 |
```

Do **not** encode “every defect …” only inside an AI question when At most N + each defect works.

---

## Priority

1. Deterministic (Must equal, At least/At most N, File name matches, …)  
2. AI yes/no / AI photo check  
3. Manual review (evidence **outside** the report only)

---

## Hard bans

- No free-text **applies_when**  
- No invented Rule types or Check parts  
- No regex in Value  
- No “does this satisfy the GI / is this correct?” AI questions  
- No putting PSI / product type in **for_each** — use a Condition  
- No approximate checkpoint names — copy from sample report  
- Do not put two checkpoint names in one Look at — emit **two Rule rows**
