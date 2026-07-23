import os
import glob
import random
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from harness_rules import parse_harness_blocks, block_to_check_block, _slug
from check_block import _compile_call, compile_block

def build_macro_node(cb, rid):
    # Compile a macro check block into a boolean predicate node
    # A macro is basically a "then" node but used as a "when" predicate
    where = cb.get("where", [])
    check = str(cb.get("check") or "")
    try:
        return _compile_call(check, where, f"{rid}.macro")
    except Exception:
        return {"op": "false", "ground": "json"}

def parse_linked_when(text, macros):
    import re
    if not text:
        return None
    if "@" not in text:
        return text
        
    def _resolve(token):
        token = token.strip()
        is_not = False
        if token.upper().startswith("NOT "):
            is_not = True
            token = token[4:].strip()
        if token.startswith("@"):
            token = token[1:]
        ast = macros.get(_slug(token))
        if not ast:
            ast = {"op": "false", "ground": "json"}
        if is_not:
            return {"op": "not", "item": ast, "ground": "json"}
        return ast

    if " OR " in text.upper():
        parts = re.split(r"(?i)\s+OR\s+", text)
        return {"op": "any_of", "items": [_resolve(p) for p in parts], "ground": "json"}
    
    if " AND " in text.upper():
        parts = re.split(r"(?i)\s+AND\s+", text)
        return {"op": "all_of", "items": [_resolve(p) for p in parts], "ground": "json"}

    return _resolve(text)

def main():
    print("Gathering existing rules...")
    files = glob.glob("data/clients/*/gi/rules.md")
    
    all_existing_blocks = []
    for f in files:
        with open(f, "r") as fp:
            blocks = parse_harness_blocks(fp.read())
            all_existing_blocks.extend(blocks)
            
    print(f"Found {len(all_existing_blocks)} existing rules.")
    
    random.seed(42)
    sample_50 = random.sample(all_existing_blocks, min(50, len(all_existing_blocks)))
    
    synthetic_markdown = """
**id:** C1
**row type:** Condition (hidden)
**check:** Check if carton drop failed
**where:** Carton drop test result
**action:** equals
**param:** FAIL

**id:** C2
**row type:** Condition (hidden)
**check:** Check if measurement failed
**where:** Product Dimensions Result
**action:** equals
**param:** FAIL

**id:** C3
**row type:** Condition (hidden)
**check:** Check if client is VIP
**where:** report.client_name
**action:** equals
**param:** VIP_CLIENT

**id:** NEW_1
**row type:** Rule
**check:** Complex AND logic
**where:** Overall result
**action:** equals
**param:** FAIL
**when:** @C1 AND @C2

**id:** NEW_2
**row type:** Rule
**check:** Complex OR logic
**where:** Overall result
**action:** equals
**param:** PENDING
**when:** @C1 OR @C3

**id:** NEW_3
**row type:** Rule
**check:** Iterator with condition
**where:** Defect photo count
**action:** at least N photos
**param:** 1
**for each:** each defect
**when:** @C2

**id:** NEW_4
**row type:** Rule
**check:** Negative condition logic
**where:** Overall result
**action:** equals
**param:** PASS
**when:** NOT @C1 AND NOT @C2

**id:** NEW_5
**row type:** Rule
**check:** Fuzzy matching with typo in where
**where:** Carton Drap Tst
**action:** is present
**param:**

**id:** NEW_6
**row type:** Rule
**check:** Each SKU validation
**where:** item.quantity
**action:** at least N photos
**param:** 1
**for each:** each sku

**id:** C4
**row type:** Condition (hidden)
**check:** check for major
**where:** item.classification
**action:** equals
**param:** MAJOR

**id:** NEW_7
**row type:** Rule
**check:** Nested iterator with condition
**where:** Defect photo count
**action:** at least N photos
**param:** 1
**for each:** each defect
**when:** @C4

**id:** NEW_8
**row type:** Rule
**check:** Vision fallback test
**where:** Carton drop test photos
**action:** needs vision
**param:** Does this show a damaged carton?

**id:** NEW_9
**row type:** Rule
**check:** Value extraction AI fallback
**where:** Remark
**action:** LLM yes/no
**param:** Mentions factory refusal

**id:** NEW_10
**row type:** Rule
**check:** Cross-section references
**where:** Packaging Checklist photo count
**action:** at least N photos
**param:** 3

**id:** NEW_11
**row type:** Rule
**check:** Missing parameter resilience
**where:** Overall result
**action:** equals
**param:** 

**id:** NEW_12
**row type:** Rule
**check:** Unrecognized operator resilience
**where:** Overall result
**action:** magic unknown action
**param:** PASS

**id:** NEW_13
**row type:** Rule
**check:** Extremely long parameter
**where:** Remark
**action:** contains phrase
**param:** A very very very very very very very very very very long parameter that tests the limits

**id:** NEW_14
**row type:** Rule
**check:** Number parsing resilience
**action:** at least N photos
**where:** Defect photo count
**param:** 2

**id:** NEW_15
**row type:** Rule
**check:** Float parsing resilience
**action:** at least N photos
**where:** Defect photo count
**param:** 2.5

**id:** C5
**row type:** Condition (hidden)
**check:** Check missing macro
**where:** Overall result
**action:** equals
**param:** PASS

**id:** NEW_16
**row type:** Rule
**check:** Reference missing macro
**where:** Overall result
**action:** equals
**param:** PASS
**when:** @NON_EXISTENT_MACRO

**id:** NEW_17
**row type:** Rule
**check:** Multiple ANDs
**where:** Overall result
**action:** equals
**param:** PASS
**when:** @C1 AND @C2 AND @C3

**id:** NEW_18
**row type:** Rule
**check:** Macro chaining
**where:** Overall result
**action:** equals
**param:** PASS
**when:** @C1 OR NOT @C2

**id:** NEW_19
**row type:** Rule
**check:** Empty condition string
**where:** Overall result
**action:** equals
**param:** PASS
**when:** 

**id:** NEW_20
**row type:** Rule
**check:** Crazy formatting in when
**where:** Overall result
**action:** equals
**param:** PASS
**when:**    @C1    AND    @C2  
"""
    
    combined_markdown = ""
    for block in sample_50:
        for key in ["id", "row type", "check", "where", "action", "param", "when", "for each", "example"]:
            val = block.get(key)
            if val:
                combined_markdown += f"**{key}:** {val}\n"
        combined_markdown += "\n"
        
    combined_markdown += synthetic_markdown
    
    print("Compiling 50 existing + 20 synthetic rules...")
    
    from harness_rules import when_to_predicate
    
    blocks = parse_harness_blocks(combined_markdown)
    macros = {}
    check_blocks = {}
    
    for b in blocks:
        cb = block_to_check_block(b)
        rid = _slug(b.get("id") or "")
        check_blocks[rid] = cb
        if cb.get("row_type", "").lower().startswith("condition"):
            macros[rid] = build_macro_node(cb, rid)

    compiled_asts = {}
    success_count = 0
    failure_count = 0
    
    for b in blocks:
        rid = _slug(b.get("id") or "")
        cb = check_blocks[rid]
        if cb.get("row_type", "").lower().startswith("condition"):
            continue
            
        when_raw = cb.get("when")
        if isinstance(when_raw, str):
            if "@" in when_raw:
                cb["when"] = parse_linked_when(when_raw, macros)
            else:
                where_raw = (b.get("where") or "").strip()
                cb["when"] = when_to_predicate(when_raw, where_raw)
                
        try:
            req = "unknown"
            if isinstance(cb.get("check"), dict):
                req = cb["check"].get("op", "unknown")
            elif cb.get("check"):
                req = str(cb.get("check"))
            
            ast = compile_block({"id": rid, "requirement": req}, cb)
            compiled_asts[rid] = ast
            success_count += 1
        except Exception as e:
            print(f"Failed to deep-compile {rid}: {e}")
            failure_count += 1
            
    print(f"\nTotal Deep Compiled: {success_count} | Failed: {failure_count}")
    
    print("\n--- Showcasing Edge-Case ASTs ---")
    for rid in ['new_1', 'new_4', 'new_7', 'new_16', 'new_20']:
        if rid in compiled_asts:
            print(f"\nAST for {rid}:")
            print(json.dumps(compiled_asts[rid], indent=2))
        else:
            print(f"\n{rid} failed to compile.")

if __name__ == "__main__":
    main()
