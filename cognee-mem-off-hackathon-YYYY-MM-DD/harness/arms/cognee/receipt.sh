#!/bin/sh
# Body-free injection receipt for this issue's session: what was injected and why.
set -eu
root="$(dirname "$(dirname "$(claude plugin list --json 2>/dev/null | python3 -c 'import json,sys; [print(p["installPath"]) for p in json.load(sys.stdin) if p.get("name","").startswith("cognee-memory")]' 2>/dev/null | head -1)")")"
[ -n "$root" ] || root="$HOME/.claude/plugins/cache/cognee/cognee-memory"
python3 "$root"/*/scripts/cognee-evidence.py explain --session-key "${MEMOFF_SESSION_ID:?}" --json 2>/dev/null \
  || python3 -c 'import json,os; print(json.dumps({"session": os.environ["MEMOFF_SESSION_ID"], "receipt": "unavailable"}))'
