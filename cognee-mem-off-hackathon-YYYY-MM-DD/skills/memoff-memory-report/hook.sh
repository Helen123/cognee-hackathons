#!/bin/sh
# memoff-memory-report checkpoint hook — registered on the agent's `Stop` event by install.sh
# for Claude Code (.claude/settings.json) and Codex (.codex/hooks.json). Project-scoped.
#
# Time gate on turns (no agent has a timer): the first turn ending ≥ INTERVAL seconds after
# the last checkpoint asks the agent to update ./memoff-report.md + .json with the evidence
# found since then. Every other turn exits silently. Never fails the turn.
INTERVAL="${MEMOFF_REPORT_INTERVAL:-900}"
STATE="${MEMOFF_REPORT_STATE:-.memoff-report.state}"
REPORT="memoff-report.md"
RUNS_DIR="${MEMOFF_RUNS_DIR:-./memoff-runs}"

input="$(cat 2>/dev/null)"
if printf '%s' "$input" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then exit 0; fi

now="$(date +%s)"
if [ ! -f "$STATE" ]; then printf '%s\n' "$now" > "$STATE"; exit 0; fi
last="$(cat "$STATE" 2>/dev/null || echo 0)"
[ "$((now - last))" -ge "$INTERVAL" ] || exit 0

# Evidence 1: new harness run folders (any dir holding action-run.json newer than the clock).
new_runs=""; n_runs=0; n_smoke=0
for d in "$RUNS_DIR" "${MEMOFF_EXTRA_RUNS_DIR:-}"; do
  [ -n "$d" ] && [ -d "$d" ] || continue
  found="$(find "$d" -maxdepth 3 -name action-run.json -newer "$STATE" 2>/dev/null)"
  [ -n "$found" ] || continue
  for f in $found; do
    n_runs=$((n_runs + 1))
    grep -q '"smoke": true' "$f" 2>/dev/null && n_smoke=$((n_smoke + 1))
    new_runs="$new_runs $(dirname "$f")"
  done
done

# Evidence 2: the cognee plugin and its cognee-report skill.
plugin=""
for p in "$HOME"/.claude/plugins/*/*/skills/cognee-report "$HOME"/.claude/plugins/*/skills/cognee-report; do
  [ -d "$p" ] && plugin="$(dirname "$(dirname "$p")")" && break
done
stats=""
if [ -n "$plugin" ] && [ -f "$plugin/scripts/_session_stats.py" ]; then
  stats="$(python3 "$plugin/scripts/_session_stats.py" --days 1 2>/dev/null | head -c 300 | tr '\n' ' ')"
fi

printf '%s\n' "$now" > "$STATE"
since="$(date -r "$last" +%H:%M 2>/dev/null || date -d "@$last" +%H:%M 2>/dev/null || echo "the last checkpoint")"
if [ -f "$REPORT" ]; then verb="Update"; else verb="Create"; fi
if [ "$n_runs" -gt 0 ]; then
  evidence="$n_runs new harness run folder(s) since $since ($n_smoke smoke):$new_runs."
else
  evidence="no new harness run since $since."
fi
if [ -n "$plugin" ]; then
  evidence="$evidence cognee plugin present at $plugin${stats:+; session stats: $stats}."
else
  evidence="$evidence cognee plugin not found (scorecard: n/a)."
fi
msg="memoff-report checkpoint (every ~15 min). $evidence $verb ./$REPORT and ./memoff-report.json following the memoff-memory-report skill: one Runs row per new run folder from its metrics.json (label smoke runs); refresh the Scorecard from plugin_eval.py report --format json when the plugin is present; add Recall observations only for items the user acted on or ignored, with rank and a neutral reason; nothing memory-related → change nothing. Keep it short, then stop."
printf '{"decision":"block","reason":"%s"}\n' "$(printf '%s' "$msg" | sed 's/["\\]/\\&/g')"
exit 0
