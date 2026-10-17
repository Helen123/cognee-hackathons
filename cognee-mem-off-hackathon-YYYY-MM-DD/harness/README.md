# Mem Off harness (`memoff`)

An agent adapter and a sequencer on top of the `cognee-report` skill's `outcomes` protocol.
Requires the cognee Claude Code plugin (for the skill), Claude Code, `uv`, Python 3.10+ for
the harness and Python 3.14 for xitkit's workspace venvs.

```bash
claude plugin marketplace add topoteretes/cognee-integrations
claude plugin install cognee-memory@cognee
cd harness && uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest -q tests
```

| Command | What |
|---|---|
| `memoff suite [--out suite.json]` | print the eight cases (Part A text, targets, verify argv) or write the suite |
| `memoff run --arms <memory.yml|folder>... --repeats N --out DIR [--xitkit-source PATH] [--smoke] [--only 1 2]` | the chained sequence; the control arm is added unless `--no-control` |
| `memoff pilot --issue N --xitkit-source PATH --out DIR [--smoke]` | one issue through the stock `plugin_eval.py outcomes run` |
| `memoff verify --issue N` | in a workspace: visible failure target + private grader |
| `memoff adapter [--smoke]` | the agent adapter (stdin → stdout) |
| `memoff check-submission --hackathon-dir DIR --base origin/main` | the CI rules |

Environment: `MEMOFF_ISSUES_DIR` (defaults to `../challenge/issues`), `MEMOFF_PRIVATE_DIR`
(the organisers' graders: `graders/test_issue_NN.py`; without it only the visible target is
checked and `verify/*.json` says so), `MEMOFF_COGNEE_REPORT_DIR` (if the skill is not found
under `~/.claude/plugins`), `MEMOFF_CLAUDE_BIN`, `MEMOFF_MAX_TURNS` (60), `MEMOFF_MAX_BUDGET_USD`
(5), `MEMOFF_SYSTEM_PROMPT_FILE`, `MEMOFF_WAIT_SECONDS` (600).

Output layout of `memoff run --out DIR`:

```text
DIR/action-run.json  suite.json  trials.jsonl  issues.jsonl  metrics.json  leaderboard.md
DIR/outcomes/{trials.jsonl,report.json}        # when both no_memory and cognee arms ran
DIR/<arm>/install.log
DIR/<arm>/r<rep>/{run.json, workspace/, verify/, injected/, receipts/, transcripts/, artifacts/, logs/, final.diff}
```

`arms/` holds the organisers' manifests for the named arms. They are **drafts** until
workstream C pins versions and validates `wipe`/`wait` on the runner; the tests only check
that they validate. `tests/fixtures/arm-noop` is a no-op arm named `cognee` for smoke runs.

Smoke (no model): `memoff run --smoke --arms tests/fixtures/arm-noop --only 1 2 --out /tmp/x
--xitkit-source /path/to/xitkit`. Smoke output carries `no_model_smoke` and is never evidence.

`Dockerfile` builds the runner image (Python 3.14, uv, Node, Claude Code).
