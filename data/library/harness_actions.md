# Harness — Actions (ops + AI)

Closed list. Pick **one** Action per check. Do not invent new Actions.

**Rule:** Action = what must hold. Param = N / plain phrase / value — **never a regex**.

Only add a new Action when the **same need appears across multiple clients**. Prefer reusing LLM yes/no until then.

---

## Actions → operators

| Action (write this) | Operator | Needs param? | Use when |
|---|---|---|---|
| is present | `present` | no | field must not be blank |
| is in English | `no_language(chinese)` | no | no Chinese / CJK characters |
| equals | `equals(X)` | yes — exact value | result or field must be exactly X |
| is one of | `in_set(A, B, …)` | yes — allowed values | PASS/FAIL/N/A etc. |
| contains phrase | `contains("…")` | yes — exact phrase | mandatory wording (exact words) |
| at least N photos | `count_at_least(N)` | yes — N | checklist **photo count** min |
| at most N photos | `count_at_most(N)` | yes — N | checklist **photo count** max (0 = none) |
| ratio at least | `ratio_at_least(X)` | yes — X e.g. 0.8 | packed/ordered etc. |
| filename matches | `filename_matches("…")` | yes — simple pattern with `*` | attachment name |
| term must not appear | `scan_absent("…")` | yes — plain term | banned wording |
| LLM quote then match | `extract` + `contains` | yes — phrase to find | free-form text must include a phrase |
| LLM yes/no | `extract_bool("…")` | yes — one factual yes/no | free-form / multi-row judgment on a bound field |
| needs vision | `vision("…")` | yes — what the photo must show | Where ends with **photo content** |
| manual review | `check: null` | no | evidence **outside** the report only |

---

## Common Values (param) — prefer these exact strings

When Action is **equals** / **is one of** (Excel: Must equal / Must be one of):

| Value (write this) | Use when |
|---|---|
| `PASS` | checkpoint / overall passed |
| `FAIL` | failed |
| `Pending` | pending |
| `N/A` | not applicable (short) |
| `NOT_APPLICABLE` | platform N/A enum (aliases to N/A in eval) |
| `PASS, FAIL` | is one of — exclude N/A |
| `PASS, FAIL, Pending` | is one of — exclude N/A |
| `Pre-Shipment Inspection` | Inspection type (PSI full name — copy from sample report) |
| `During Production Inspection` | Inspection type (DUPRO full name) |

When Action is **at least N photos** / **at most N photos**: prefer `0`, `1`, `2`, `3`, `5`.

Do **not** write `PSI` or `DUPRO` as equals Values unless the sample report literally stores that string.

---

## Priority

1. Deterministic  
2. LLM quote then match / LLM yes/no  
3. needs vision  
4. manual review (out-of-report only)

---

## Hard bans

- **No regex** in Param. Use **LLM yes/no** or **contains phrase**.
- Do not invent Actions for one client. If unsure → **LLM yes/no** on the right Where.
- Do not use **manual review** for in-report evidence.
- Do not use needs vision unless Where ends with **photo content**.
- Do not ask “does this satisfy the GI / is this correct?”.
