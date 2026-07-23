# GI authoring structure (ops)

One check = one block (or one Excel row). LLM / ops **only choose** from dropdowns in `harness_actions.md` and `harness_where.md`.

## Fields

| Field | Required | How to fill |
|---|---|---|
| id | yes | e.g. `A.1.1` |
| check | yes | one **should…** sentence |
| where | yes | cover place **or** `<checkpoint name> <suffix>` |
| action | yes | **dropdown only** |
| param | when Action needs it | N / phrase / value |
| when | no | omit if always |
| example | no | optional ✗ / ✓ |

## Suffix dropdown (checklist Where)

`result` · `comment` · `values` · `photo count` · `photo caption` · `photo content` · `file name` · `file content`

| Suffix | Means |
|---|---|
| photo count | how many photos |
| photo caption | caption text |
| photo content | what the image shows (vision) |

## Example block

```markdown
**id:** A.5.1
**check:** Carton-drop photos should not be included when the test passed
**where:** Carton drop test photo count
**action:** at most N photos
**param:** 0
**when:** when the drop test passed
```

## Companion files

- `harness_actions.md` — Action dropdown  
- `harness_where.md` — Where places + suffix dropdown  
- `harness_compile_prompt.md` — LLM: choose only from lists  
- `gi_authoring_template.xlsx` — Excel dropdowns  
- `gi_authoring_schema.json` — future UI  
