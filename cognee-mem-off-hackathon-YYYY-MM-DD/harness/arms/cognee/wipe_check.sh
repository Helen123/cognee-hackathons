#!/bin/sh
# Exit non-zero if the run's dataset already holds data.
set -eu
CLI="$HOME/.cognee-plugin/venv/bin/cognee-cli"
[ -x "$CLI" ] || exit 0
out="$("$CLI" datasets list 2>/dev/null || true)"
case "$out" in *"${MEMOFF_MEMORY_STORE:?}"*) echo "dataset ${MEMOFF_MEMORY_STORE} exists" >&2; exit 1;; esac
exit 0
