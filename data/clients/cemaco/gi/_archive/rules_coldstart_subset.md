# Cemaco — Inspection Report Review Rules (cold-start subset)

> Derived from `Cemaco_GIs.md` §9.3–9.4 and validated review findings on Q2519476686.
> Full operational GI remains in `Cemaco_GIs.md`; this file is the PolicyGuard review-rule shape.

---

## Section 9 – Report writing / photo metadata

---

**ID:** 9.3.1
**Field / Location:** Outer Packing & Shipping Marks: Front & Side — Tests checklist / report photos
**What to check:** Add captions to all outer packing photos as per GI (TAG / SKU captions), not just on 1 photo. Every uploaded outer-packing photo must have a non-blank caption.
**Scope:** `QUESTION` — check photo captions on Outer Packing & Shipping Marks: Front & Side
**Error example:** 47 outer packing photos uploaded but only 1 has a caption/TAG
**Correct example:** Every outer packing photo has a SKU/TAG caption
**Severity:** `BLOCKING`

---

**ID:** 9.3.2
**Field / Location:** Product Dimensions Result — Tests checklist / report photos
**What to check:** Measurement photos also need captions as per GI. Every uploaded measurement / product-dimensions photo must have a non-blank caption.
**Scope:** `QUESTION` — check photo captions on Product Dimensions Result
**Error example:** Measurement photos uploaded with blank captions
**Correct example:** Every measurement photo has a descriptive caption (e.g. size check / SKU)
**Severity:** `BLOCKING`

---

**ID:** 9.3.3
**Field / Location:** Product Dimensions Result — Tests checklist / report photos
**What to check:** Spotlight the measurement screenshot instead of leaving measurement images without spotlight. When measurement photos are present, at least one must be marked as spotlight.
**Scope:** `QUESTION` — check spotlight flag on Product Dimensions Result photos
**Error example:** Measurement screenshot present but none marked spotlight
**Correct example:** Measurement screenshot is spotlighted in Product Dimensions Result
**Severity:** `BLOCKING`

---
