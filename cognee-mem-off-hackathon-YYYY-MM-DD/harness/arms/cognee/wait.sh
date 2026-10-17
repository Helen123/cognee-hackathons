#!/bin/sh
# Block until the plugin's post-session work (final sync + background improve) has finished.
# The plugin logs `sync.sync_once_released` and `auto.improve_fired`/`auto.improve_error` events;
# we wait for the session's sync marker to disappear, with a bound.
set -eu
deadline=$(( $(date +%s) + ${MEMOFF_WAIT_SECONDS:-600} ))
phase_dir="$HOME/.cognee-plugin/claude-code/phase"
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ! ls "$phase_dir" 2>/dev/null | grep -q .; then exit 0; fi
  sleep 2
done
echo "wait.sh: plugin still busy after ${MEMOFF_WAIT_SECONDS:-600}s" >&2
exit 1
