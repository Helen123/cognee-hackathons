#!/bin/sh
# Empty the claude-mem store between repeats. Stops the worker first so SQLite is not mid-write.
set -eu
pkill -f "claude-mem" 2>/dev/null || true
rm -rf "$HOME/.claude-mem/claude-mem.db" "$HOME/.claude-mem/claude-mem.db-wal" "$HOME/.claude-mem/claude-mem.db-shm" "$HOME/.claude-mem/chroma" 2>/dev/null || true
