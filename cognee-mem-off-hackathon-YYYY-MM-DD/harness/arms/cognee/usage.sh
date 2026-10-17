#!/bin/sh
# Print JSON usage records (source=server) for cognee's own LLM/embedding spend in this session.
# Until the local server exposes per-session usage, report an unmeasured server row so totals
# stay "unknown" rather than pretending the memory system was free.
set -eu
printf '[{"id": "cognee-server:%s", "source": "server"}]\n' "${MEMOFF_SESSION_ID:?}"
