#!/bin/sh
# Empty the memory store for this run. The sequencer passes MEMOFF_MEMORY_STORE / COGNEE_PLUGIN_DATASET,
# a dataset name that does not exist yet, so a fresh run starts empty by construction; this script
# removes any leftover dataset of the same name and the plugin's buffered turns.
set -eu
CLI="$HOME/.cognee-plugin/venv/bin/cognee-cli"
if [ -x "$CLI" ]; then
  "$CLI" forget --dataset "${MEMOFF_MEMORY_STORE:?}" >/dev/null 2>&1 || true
fi
rm -rf "$HOME/.cognee-plugin/claude-code/buffer" 2>/dev/null || true
