# GI Excel authoring — ops + AI examples

Companion to the **Checks** sheet in `gi_authoring_*.xlsx`.  
Use with `harness_compile_prompt.md`, `harness_actions.md`, `harness_where.md`.

---

## One sentence

A **Rule** is what must be true. A **Condition** is when it runs (`@C1`).  
**Repeat for** is only when the same check must hold for every item in a list.

---

## Value dropdown (suggestions — soft)

For **Must equal** / **Must be one of**, pick when possible:

| Value | Typical Look at |
|---|---|
| `PASS` / `FAIL` / `Pending` | checkpoint `result`, Overall result |
| `N/A` / `NOT_APPLICABLE` | checkpoint `result` (often a GI *violation* if logo etc.) |
| `PASS, FAIL` / `PASS, FAIL, Pending` | Must be one of |
| `Pre-Shipment Inspection` | Inspection type (exact report string — not `PSI`) |
| `During Production Inspection` | Inspection type (DUPRO full name) |

For counts: `0`, `1`, `2`, `3`, `5`.

You may still type custom Values (AI questions, `Measurement Chart-{style}.xlsx`).

---

## Examples

### Always — factory address

| id | row_type | applies_when | for_each | look_at | check_part | rule_type | value |
|---|---|---|---|---|---|---|---|
| A.1.1 | Rule | | | Factory address | | AI yes/no (flag if false) | Does this address include street/building, city, country, and a postal/zip code? |

### Condition — PSI

| id | row_type | look_at | rule_type | value |
|---|---|---|---|---|
| C_psi | Condition (hidden) | Inspection type | Must equal | Pre-Shipment Inspection |

Then every PSI-only Rule: `applies_when = @C_psi`.

### Condition — drop test passed → no photos

| id | row_type | applies_when | look_at | check_part | rule_type | value |
|---|---|---|---|---|---|---|
| C2 | Condition (hidden) | | Carton drop test | result | Must equal | PASS |
| A.5.1 | Rule | @C2 | Carton drop test | photo count | At most N | 0 |

### Two named checkpoints → two rows

| id | look_at | check_part | rule_type | value |
|---|---|---|---|---|
| B.1 | Quantity Packed | result | Must equal | PASS |
| B.2 | Quantity Shipped | result | Must equal | PASS |

### Repeat for — each defect ≤5 photos

| id | for_each | look_at | rule_type | value |
|---|---|---|---|---|
| A.3.4 | each defect | Defects | At most N | 5 |

Prefer this over AI “Does every defect type have at most 5 photos?”.

### Compound — PSI AND FAIL

| id | row_type | look_at | rule_type | value |
|---|---|---|---|---|
| C3 | Condition (hidden) | Inspection type | Must equal | Pre-Shipment Inspection |
| C4 | Condition (hidden) | Overall result | Must equal | FAIL |

Rule: `applies_when = @C3 AND @C4`.

---

## Common mistakes

| Don’t | Do |
|---|---|
| Value = `PSI` | `Pre-Shipment Inspection` (from sample report) |
| Applies when = `when the drop test passed` | Condition + `@C2` |
| Repeat for = PSI | Condition on Inspection type |
| One Look at = `Quantity` for a family | One exact name per row |
| Example text on Condition rows | Leave Example blank |

---

## Decision tree

```
Only for some reports (PSI, FAIL, defects exist)?
  → Condition(s) + applies_when = @C1 / @C1 AND @C2

Every item in a list must pass the same count?
  → for_each = each defect (+ At least/At most N)

Can we count or compare without prose/photos?
  → Must equal / At least N / At most N / File name matches
  → else AI yes/no or AI photo check
```
