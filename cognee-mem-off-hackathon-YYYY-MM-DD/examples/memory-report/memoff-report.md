---
type: memoff-memory-report
event: Mem Off (example — synthetic, from a smoke run)
team: example-team
system: none / control (smoke)
agent: claude-code   cognee_plugin: absent
first_green_run: never   runs: 1   smoke_runs: 1
---

# Summary
One smoke run of the harness (`memoff run --smoke --only 1 2`, two arms, two repeats) on the
real xitkit checkout. No model ran, so no issue passed and no memory effect can be claimed.
The run proves the pipeline: real pytest counts (11 failed / 769 passed vs targets 6 and 5),
evaluator records accepted by `summarize`, receipts and verify output written. The one number
for a judge: none yet — smoke output is orchestration proof only.

# Runs
| time | command | out dir | arms | issues | repeats | all pass | median cost | turns | injected chars | smoke |
|---|---|---|---|---|---|---|---|---|---|---|
| 08:36 | memoff run --smoke --only 1 2 | memoff-runs/smoke | no_memory, cognee (no-op fixture) | 1, 2 | 2 | no | 0.000 (no_model_smoke) | unmeasured | 0 | yes |

# Scorecard (cognee-report)
n/a — cognee plugin not installed on this machine during the example.

# Recall observations
| time | issue/task | item kind | rank | helped | reason |
|---|---|---|---|---|---|
| — | — | — | — | — | no agent session ran (smoke) |

# Costs
agent: unmeasured (no model). memory system: 0 reported by the fixture's usage.sh with basis
`no_model_smoke` — a label, not a measurement.

# What did not work
- `injected/issue-01/` and `injected/issue-02/` are empty: the no-op fixture arm writes nothing
  to `MEMOFF_INJECTED_DIR` (expected; a real arm must).
