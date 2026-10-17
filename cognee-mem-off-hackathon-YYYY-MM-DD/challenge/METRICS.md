# Metrics and scoring

Per issue and cumulative, per arm, median of repeats with min–max.

| Metric | Source |
|---|---|
| pass / fail | visible-suite failure target **and** private grader (`verify/<issue>.json`) |
| agent turns (one model response = one turn) | Claude Code result `num_turns` |
| input / output / cache-read / cache-write tokens | Claude Code result `usage` |
| memory-system tokens and cost | the entrant's `usage.sh` records (`source: server`); null when absent |
| injected context characters | files under `injected/<issue>/` |
| elapsed time (agent) and post-session wait (memory) | runner timestamps, `wait_ms` |
| cost (agent + memory) | `total_cost_usd` from the CLI, else tokens × the pinned price sheet (`harness/memoff/data/prices.json`, labelled `configured_rates`) |
| changed-file count | `git status --porcelain` before the issue's commit |
| paired win/loss vs control, P50/P95 whole-trial and recall latency | `outcomes/report.json` (the skill's `summarize`) |
| recall hit rate, SessionStart latency, injected chars, scorecard grade | `cognee-report.json` (cognee arm only) |
| why each memory was or was not injected | `receipts/<issue>.json` (`cognee-evidence.py explain`, or the entrant's `receipt.sh`) |

## Leaderboard rule

Correctness is a gate. An arm that fails any issue's grader is listed with its resource use
but not ranked on efficiency. Among all-pass arms, rank by **total cost relative to
control**, with turns and tokens beside it. The **memory delta** is the cost on issues 4, 5,
7 and 8 (the ones that revisit earlier code) relative to control.

Null means unmeasured, never zero. Never compare raw numbers across issues.

## Published per arm

`metrics.json`, the eight injected-context dumps, the eight receipts, the eight redacted
transcripts, `final.diff`, `outcomes/report.json` and `outcomes/trials.jsonl`.
