# Protocol: how the harness drives an arm

Mem Off reuses the **`cognee-report` skill's `outcomes` protocol** (file
`skills/cognee-report/scripts/outcome_eval.py` in the cognee Claude Code plugin, schema 1)
and adds two things: an agent adapter and a sequencer. Nothing in the skill is copied; the
harness imports `score`, `usage_totals`, `summarize` and `digest` from it.

## The request / response (unchanged from the skill)

The runner sends one JSON request on stdin to the adapter, with the workspace as cwd:

```json
{"schema": 1, "trial_id": "…", "variant": "cognee", "model": "<pinned>", "max_tokens": 8192,
 "seed": 42, "session_id": "…", "dataset_name": "…", "recall_budget_seconds": 45,
 "workspace": "/…/workspace", "state_dir": "/…/state/issue-03",
 "task": {"id": "issue-03", "prompt": "<Part A text>"}, "memory_seed": [], "variant_config": {}}
```

The adapter answers one JSON object: it echoes `model`, `session_id`, `dataset_name`; gives
`claims` (`[{"id": "status", "value": "implemented" | "not_implemented", "citations": []}]`),
`retrieved_ids` (always `[]`: Mem Off seeds no memory; the entrant's system builds it),
`recall_ms`, `usage` records (one `client` row for the agent, `server` rows for the memory
system) and `usage_complete`.

## The agent adapter (`memoff adapter`)

Runs `claude -p <prompt> --model <pinned> --output-format json --permission-mode
bypassPermissions --max-turns N --max-budget-usd B --append-system-prompt-file <fixed>`
plus `--plugin-dir` for bundled systems, in the workspace. Parses the result for turns,
token classes, cost and duration; reads the `STATUS:` line of the agent's final message for
the claim; counts `$MEMOFF_INJECTED_DIR`. `MEMOFF_SMOKE=1` runs no model.

## The sequencer (`memoff run`)

For each arm and repeat: clone xitkit at the pinned revision, make a Python 3.14 venv,
`install.sh` (once per arm), `wipe.sh` + `wipe_check.sh`, `preindex.sh` if declared, then
for each issue: adapter → `verify` (visible failure target + private grader) → commit →
`wait.sh` → `receipt.sh` → `usage.sh` → one record. Records go to `trials.jsonl`
(evaluator schema) and `issues.jsonl` (per-issue runner metrics); `report.json` is the
skill's `summarize` over the records; `metrics.json` and `leaderboard.md` are the harness's.

Record semantics that differ from independent trials, on purpose:

- `session_id` is the real agent session for that issue (unique).
- `dataset_name` in the *record* is the trial's isolation key, unique as the evaluator
  requires. The store the memory system actually uses is shared across the issues of one
  (arm, repeat) — that is the benchmark — and is reported as `memoff.memory_store`.
- `fixture_hash` is computed from the issue prompt and the *baseline* revision, not each
  arm's current code, so matched blocks compare the same issue.
- `variants` must include `no_memory` and `cognee` for `report.json` to be built; a run
  without both still writes `metrics.json` and says why the report was skipped.

## Single-issue pilots (`memoff pilot`)

Track 2 pilots and quick checks go through the **stock** `plugin_eval.py outcomes run`,
with one issue as the suite's only case, the repository pinned, and the same adapter. That
path treats the issue as independent (fresh clone at the baseline), which is right for a
pilot and wrong for the chain.

## What the `cognee-report` skill adds for the cognee arm

`plugin_eval.py report --since all --format json` (delivery scorecard from the plugin's own
logs) and `cognee-evidence.py explain --session-key <id>` (per-item injection receipt). Both
are cognee-only; other arms provide the equivalent through `receipt.sh`.

## Caveats the skill's docs state and this benchmark repeats

- The bundled smoke runner is deterministic and model-free: orchestration proof only. CI
  refuses a `results/` folder whose trials carry `no_model_smoke`.
- The skill's shipped HTTP adapter measures retrieval and answer claims; coding runs need
  the agent adapter above.
- Live citation metrics are a lower bound; Mem Off does not use citations at all.
