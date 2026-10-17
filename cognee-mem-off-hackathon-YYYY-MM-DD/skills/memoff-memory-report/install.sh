#!/bin/sh
# Install the memoff-memory-report skill into the current project (participant's repo or the
# hackathon folder). Same mechanics as agent-skills/cognee-hackathon-feedback/install.sh.
#
# Local:   skills/memoff-memory-report/install.sh --event "Mem Off 2026-MM-DD" --team my-team
# Remote:  curl -fsSL https://raw.githubusercontent.com/topoteretes/cognee-hackathons/main/cognee-mem-off-hackathon-YYYY-MM-DD/skills/memoff-memory-report/install.sh \
#            | sh -s -- --event "Mem Off 2026-MM-DD" --team my-team
#
# Idempotent:
#   1. copies SKILL.md and hook.sh to .claude/skills/ and .agents/skills/
#   2. appends a "memoff report" block to AGENTS.md and CLAUDE.md carrying the event and team
#   3. registers hook.sh on the `Stop` event in .claude/settings.json and .codex/hooks.json
#      (merged; coexists with the cognee-hackathon-feedback hook)
#   4. ignores only the hook's clock (.memoff-report.state); the report files ARE submitted
#   5. starts the checkpoint clock
set -eu

RAW_BASE="https://raw.githubusercontent.com/topoteretes/cognee-hackathons/main/cognee-mem-off-hackathon-YYYY-MM-DD/skills/memoff-memory-report"
NAME="memoff-memory-report"
EVENT="${MEMOFF_EVENT:-}"
TEAM="${MEMOFF_TEAM:-}"

while [ $# -gt 0 ]; do
  case "$1" in
    --event) EVENT="$2"; shift 2 ;;
    --team)  TEAM="$2";  shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown argument: $1" >&2; exit 1 ;;
  esac
done
[ -n "$EVENT" ] || { echo "install.sh: --event is required" >&2; exit 1; }
[ -n "$TEAM" ] || TEAM="<team-slug>"

here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
for dir in .claude/skills .agents/skills; do
  mkdir -p "$dir/$NAME"
  for f in SKILL.md hook.sh; do
    if [ -n "$here" ] && [ -f "$here/$f" ]; then cp "$here/$f" "$dir/$NAME/$f"; else curl -fsSL "$RAW_BASE/$f" -o "$dir/$NAME/$f"; fi
  done
  chmod +x "$dir/$NAME/hook.sh"
done

block="<!-- $NAME -->
## memoff report (hackathon)

This project takes part in \"$EVENT\" as team \"$TEAM\". Follow the \`$NAME\`
skill (\`.claude/skills/$NAME/SKILL.md\`):

- About every 15 minutes a hook ends your turn with a \"memoff-report checkpoint\"
  message: update \`./memoff-report.md\` and \`./memoff-report.json\` from tool output
  (harness run folders, the cognee-report scorecard, recall receipts), briefly, then stop.
- Record numbers from tools, never impressions; no quotes, keys, data or names.
- When I say I'm done or submitting — or run \`/$NAME\` — run the skill's wrap-up and
  copy both files into \`submissions/$TEAM/report/\`. They are submitted with the
  action results.
<!-- /$NAME -->"
for f in AGENTS.md CLAUDE.md; do
  if [ -f "$f" ] && grep -q "<!-- $NAME -->" "$f"; then continue; fi
  [ -f "$f" ] && [ -s "$f" ] && printf '\n' >> "$f"
  printf '%s\n' "$block" >> "$f"
done

hook_claude="sh \"\${CLAUDE_PROJECT_DIR:-.}/.agents/skills/$NAME/hook.sh\""
hook_codex="sh .agents/skills/$NAME/hook.sh"
mkdir -p .claude .codex
python3 - "$NAME" ".claude/settings.json" "$hook_claude" ".codex/hooks.json" "$hook_codex" <<'PY'
import json, pathlib, sys
name, *pairs = sys.argv[1:]
for path, command in zip(pairs[::2], pairs[1::2]):
    p = pathlib.Path(path)
    data = json.loads(p.read_text()) if p.exists() and p.read_text().strip() else {}
    groups = data.setdefault("hooks", {}).setdefault("Stop", [])
    if any(f"{name}/hook.sh" in h.get("command", "") for g in groups for h in g.get("hooks", [])):
        continue
    groups.append({"hooks": [{"type": "command", "command": command, "timeout": 15,
                              "statusMessage": "memoff report checkpoint"}]})
    p.write_text(json.dumps(data, indent=2) + "\n")
PY

touch .gitignore
for f in .memoff-report.state .memoff-scorecard.json; do
  grep -qx "$f" .gitignore || printf '%s\n' "$f" >> .gitignore
done
[ -f .memoff-report.state ] || date +%s > .memoff-report.state

cat <<EOT
$NAME installed for "$EVENT" (team $TEAM).
  skill:        .claude/skills/$NAME/SKILL.md  (+ .agents/skills/)
  instruction:  AGENTS.md, CLAUDE.md  (section "memoff report (hackathon)")
  checkpoint:   .claude/settings.json + .codex/hooks.json → Stop → hook.sh, every ~15 min
  ignored:      .memoff-report.state, .memoff-scorecard.json  (the report files are submitted)
Your agent now keeps ./memoff-report.md and ./memoff-report.json current from tool output.
At wrap-up it copies them into submissions/$TEAM/report/ — include them in your PR.
EOT
