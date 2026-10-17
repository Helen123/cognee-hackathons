#!/bin/sh
# Index the repository into cognee's code graph before issue 1 (timed and reported separately).
set -eu
CLI="$HOME/.cognee-plugin/venv/bin/cognee-cli"
"$CLI" remember "${MEMOFF_WORKSPACE:?}" --dataset "${MEMOFF_MEMORY_STORE:?}"
