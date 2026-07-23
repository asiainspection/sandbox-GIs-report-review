# Harness — Where mapping (ops + AI)

Closed lists. Do **not** invent suffixes or cover places.

**Rule:** Where = **place** + **suffix** (for checklist items).  
Cover / external places need **no** suffix.

---

## 1. Suffix dropdown (checklist only — pick exactly one)

| Suffix (write this) | Maps to | Use for |
|---|---|---|
| result | `result` | Pass / Fail / N/A |
| comment | `comment` | free-text comment |
| values | `values` | Yes / No / selected answers |
| photo count | `photo_count` | **how many** photos |
| photo caption | `photo_captions` | caption **text** |
| photo content | `photo_content` | **what the image shows** (vision) |
| file name | `attachment_filenames` | attachment file **names** |
| file content | `attachment_content` | Excel/PDF **body** (pending) |

**Write:** `<checkpoint name from report> <suffix>`

| Correct | Wrong |
|---|---|
| `Carton drop test photo count` | `Carton drop test photos` |
| `Carton drop test result` | `Carton drop test` (no suffix) |
| `Stitch density check comment` | `Stitch density check` |
| `Stitch density check photo content` | `Stitch density check photo` |
| `Approval Sample Comparison photo caption` | `Approval Sample Comparison caption` |
| `Product Dimensions Result file name` | `Product Dimensions Result file` |
| `Are the QIMA documents signed? photo count` | `… photos` |

---

## 2. Cover places dropdown (no suffix)

| Where (write this) | Maps to |
|---|---|
| Factory address | `report.factory_address` |
| Factory name | `report.factory_name` |
| Supplier name | `report.supplier_name` |
| Production site | `report.production_site` |
| Inspector remark | `report.global_remark` |
| Overall result | `report.overall_result` |
| Inspection type | `report.inspection_type` |
| PO reference | `report.po_reference` |
| Product name | `report.product_label` |
| SKU | `report.sku` |
| Ordered quantity | `product._first.ordered_quantity` |
| Packed quantity | `product._first.real_packed_quantity` |
| Produced quantity | `product._first.real_produced_quantity` |
| Unit | `product._first.unit` |
| Major AQL | `workmanship.aql_level_major` |
| Minor AQL | `workmanship.aql_level_minor` |
| Critical AQL | `workmanship.aql_level_critical` |
| Workmanship result | `workmanship.result` |
| Defects | `report.defects` |
| Defect count | `report.defect_count` |
| Full report text | `report.inspector_text` |
| All captions | `report.all_captions` |

**ratio at least:** Where = `Packed quantity` (harness also binds Ordered quantity).

---

## 3. External places dropdown (Action must be **manual review**)

| Where (write this) | Maps to |
|---|---|
| Booking | `out_of_report:booking` |
| Spec sheet | `out_of_report:spec_sheet` |
| Email | `out_of_report:email` |
| SOP | `out_of_report:sop` |

---

## 3b. When / Applies when (Excel: Condition rows)

**Production Excel:** do not write free-text when. Create a **Condition (hidden)** row
(same Look at / Check part / Rule type / Value), then set the Rule’s Applies when to
`@C1` or `@C1 AND @C2`.

Legacy markdown may still use `when: <place> <comparator> <value>`:

| Comparator (write this) | Meaning | Example |
|---|---|---|
| is | equals | `when: Overall result is FAIL` |
| is not | not equal | `when: Workmanship result is not Passed` |
| is one of | in a set (comma list) | `when: Overall result is one of FAIL, N/A` |
| includes | list/text contains value | `when: Defects includes dirt` |
| greater than | numeric > | `when: Carton drop test photo count greater than 0` |
| less than | numeric < | `when: Packed quantity less than 100` |

**Inspection type Values:** use the exact report string, usually
`Pre-Shipment Inspection` or `During Production Inspection` (not `PSI` / `DUPRO`).

Notes:
- Empty when = always applies.
- Anything the compiler cannot map is **skipped with a warning** (never silent-always).

---

## 4. How to choose (for LLM / ops)

1. Is evidence on a **checklist item**? → place = exact name from the sample report + **suffix from §1**.
2. Is it a **cover / AQL / defects** field? → pick from §2 only (no suffix).
3. Is it **outside the report**? → pick from §3 + Action **manual review**.

---

## Hard bans

- Do not use vague words: `photos`, `photo`, `caption`, `file` alone as suffix — use the full suffix from §1.
- Do not omit the suffix on a checklist Where.
- Do not map photo-count / photo-content rules to Product name or SKU.
- Do not invent places. If unsure → **manual review** + Booking / Spec sheet / closest real place.
