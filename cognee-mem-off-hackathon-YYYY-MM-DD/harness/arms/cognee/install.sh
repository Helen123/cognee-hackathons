#!/bin/sh
# Install the cognee Claude Code plugin from the marketplace. Idempotent.
set -eu
claude plugin marketplace add topoteretes/cognee-integrations >/dev/null 2>&1 || true
claude plugin install cognee-memory@cognee
# Pin: replace the line above with `claude plugin install cognee-memory@cognee@<tag>` once C1 pins it.
