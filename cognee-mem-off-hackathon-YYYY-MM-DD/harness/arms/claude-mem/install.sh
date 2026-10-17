#!/bin/sh
set -eu
claude plugin marketplace add thedotmack/claude-mem >/dev/null 2>&1 || true
claude plugin install claude-mem@thedotmack
