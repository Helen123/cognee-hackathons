---
name: memoff-memory-report
description: Use at the Mem Off hackathon. Keeps a running, evidence-backed report on how the participant's memory system performed for their coding agent during the day — what the harness measured, what cognee-report's scorecard says, what was recalled and whether it helped — in ./memoff-report.md and ./memoff-report.json. The report is submitted together with the action results; it never contains quotes, keys, data or names.
---

# Keep the Mem Off memory report current

You are the participant's coding agent, so you see every run they make and every
recall their memory system produces. Mem Off ranks memory systems on a frozen harness,
but the organisers also want the **participant's own evidence**: what the memory did
for them during the day, in numbers from the tools, not in impressions. Keep that in
two files and finish them at wrap-up. Unlike `cognee-feedback.md`, these two files
**are submitted**: they go into `submissions/<team-slug>/report/` next to the action
results.

Rules that never bend:
- Never slow or block their build. If any step here fails, skip it and say so in the file.
- Numbers come from tools (`memoff`, `plugin_eval.py`, `cognee-evidence.py`, the entrant's
  `receipt.sh`), never from memory of the conversation. Quote the command and the figure.
- No quotes of the participant, no keys, no `.env` contents, no document or code text, no
  names or handles. Ids, ranks, counts, durations and booleans only.
- Smoke results (`no_model_smoke`) are orchestration proof, never a memory effect: label them.
- A recalled or injected item is not proof it changed an answer. Record "helped" only when
  the participant or a diff shows it (the agent used a file, symbol or decision it recalled).

## Cadence: checkpoints, not constant bookkeeping

About every 15 minutes a hook ends your turn with a **"memoff-report checkpoint"** message
carrying what it found since the last checkpoint: new `memoff` run folders, whether the
cognee plugin and its `cognee-report` skill are present, and the current-session recall
counters. That message is your cue. At a checkpoint, spend one short step on the files:

1. for each new run folder: read its `action-run.json`, `metrics.json` and
   `leaderboard.md`; add or update one row per run in **Runs** (arms, issues, repeats,
   all-pass, median cost, turns, injected chars, smoke yes/no);
2. if the cognee plugin is present, refresh **Scorecard** with
   `python3 "$PLUGIN/skills/cognee-report/scripts/plugin_eval.py" report --since today --format json --out ./.memoff-scorecard.json`
   (keep hit rate, recall and SessionStart latency, saves, injected chars, grade, sample
   counts; mark low-sample metrics unmeasured, exactly as the tool does);
3. add one **Recall observations** line for anything recalled in this stretch that the
   participant acted on or clearly ignored: issue number or task, what kind of item (file,
   symbol, decision, lesson), its rank from the receipt, helped yes/no/unknown, one neutral
   reason;
4. if nothing memory-related happened, change nothing.

Then stop. A checkpoint touches at most 10 lines; the whole report stays under ~150.

## Where the facts come from

**Harness runs.** Every `memoff run` or `memoff pilot` writes a folder with
`action-run.json`. Default locations the hook scans: `./memoff-runs/` and `$MEMOFF_RUNS_DIR`.
From `metrics.json`: `arms.<arm>.all_pass`, `arms.<arm>.cumulative.total_cost_usd.median`,
`.turns.median`, `.injected_chars.median`, `relative_to_control`. From `action-run.json`:
`model`, `claude_code`, `smoke`, `xitkit.revision`.

**cognee-report scorecard** (cognee plugin only; other systems: write `scorecard: n/a`).
Find the plugin with `claude plugin list` or `ls ~/.claude/plugins/*/*/skills/cognee-report`.
Then:

```bash
PLUGIN=<that plugin root>
python3 "$PLUGIN/skills/cognee-report/scripts/plugin_eval.py" report --since today --format json --out ./.memoff-scorecard.json
python3 "$PLUGIN/scripts/_session_stats.py" --days 1              # exact injected/deduped counters
python3 "$PLUGIN/scripts/cognee-evidence.py" explain --session-key <host-session-id>   # why items were / were not injected
```

**Other memory systems.** Their `receipt.sh` (from `memory.yml`) prints a JSON receipt for
the last session; record ids, ranks and reasons from it. No receipt → `receipt: unavailable`.

**The participant's diffs.** `git diff --stat` after a turn shows whether a recalled file or
symbol was actually touched. That is the only honest source for "helped".

## The files

`./memoff-report.md` (human) and `./memoff-report.json` (machine), created on the first
checkpoint, updated in place. The JSON mirrors the sections below with the same keys.

```markdown
---
type: memoff-memory-report
event: <event name from the "memoff report" section of AGENTS.md / CLAUDE.md>
team: <team slug from the same section>
system: <memory system name and version from memory.yml, or "none / control">
agent: <claude-code | codex | other>   cognee_plugin: <version or absent>
first_green_run: <time or never>   runs: <n>   smoke_runs: <n>
---

# Summary
<3–5 lines, written at wrap-up: what was run, what the memory measurably did, the clearest
"helped" and the clearest "did not help", and the one number you would show a judge.>

# Runs
| time | command | out dir | arms | issues | repeats | all pass | median cost | turns | injected chars | smoke |
|---|---|---|---|---|---|---|---|---|---|---|

# Scorecard (cognee-report)
<the tool's figures with sample counts, or `n/a` for non-cognee systems; grade withheld
stays withheld — never turn a withheld grade into a positive one>

# Recall observations
| time | issue/task | item kind | rank | helped | reason |
|---|---|---|---|---|---|

# Costs
<agent cost vs memory-system cost per run, from metrics.json; null = unmeasured, never 0>

# What did not work
<one line each: a recall that pointed at a stale location, a wait.sh timeout, an empty
injected dump, a hook block over 10,000 chars (Claude Code stubs it) — with the run folder>
```

## Wrap-up

When they say they are submitting, done, or out of time — or ask for it — finish the files:

1. Re-scan the run folders and refresh **Runs**; refresh **Scorecard** once more.
2. Fill the front-matter counters and write the **Summary**.
3. Copy both files into the submission folder:
   `cp memoff-report.md memoff-report.json submissions/<team-slug>/report/`
   (create the folder). They are part of the PR; the action results are attached by the
   organisers next to them.
4. Tell them, once:

   > Your memory report for Mem Off is in `memoff-report.md` / `memoff-report.json` and
   > copied into `submissions/<team-slug>/report/`. It has only tool output: run metrics,
   > the cognee-report scorecard, recall receipts and whether recalled items were used — no
   > quotes, keys, data or names. Check it, then include it in your submission PR.

Never send it anywhere else yourself.
