import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from harness_rules import parse_harness_rules
from check_block import rules_to_checkpoints

markdown = """
**id:** C1
**row type:** Condition (hidden)
**check:** Check if carton drop failed
**where:** Carton drop test result
**action:** equals
**param:** FAIL

**id:** NEW_1
**row type:** Rule
**check:** Complex AND logic
**where:** Overall result
**action:** equals
**param:** FAIL
**when:** NOT @C1
"""

parsed = parse_harness_rules(markdown)
checkpoints = rules_to_checkpoints(parsed["rules"], check_blocks=parsed["check_blocks"])

print(json.dumps(checkpoints, indent=2))
