# Submissions

One pull request per team, from a fork, adding **one folder here**:

```text
submissions/<team-slug>/
  SUBMISSION.md                      # from ../templates/SUBMISSION.md, every heading filled
  memory.yml                         # Track 1: entrant manifest (../templates/memory.yml)
  install.sh  wipe.sh  wait.sh       # Track 1: required scripts (+ optional wipe_check.sh, preindex.sh, receipt.sh, usage.sh)
  plugin/                            # Track 1, optional: a bundled Claude Code plugin (named in memory.yml plugin_dirs)
  issues/09-<slug>/ISSUE_PROPOSAL.md # Track 2: one folder per proposal (+ optional grader_sketch.py, pilot-metrics.json)
  results/                           # written by the GitHub Action after the organisers' run — never by hand
```

`<team-slug>`: lowercase letters, digits and dashes.

PR title: `Submission: <team or project> — <one line>` for Track 1, `Benchmark issue: <short
title>` for Track 2, or both joined with ` + `.

## What CI enforces (`memoff check-submission`)

- the PR touches only `submissions/<team-slug>/**`, one slug per PR;
- `SUBMISSION.md` present with the headings `## Team`, `## Track`, `## What you entered`,
  `## Reproduction`, `## Links`;
- Track 1: `memory.yml` validates against the schema and `install` / `wipe` / `wait` exist;
- Track 2: each `ISSUE_PROPOSAL.md` has the seven sections and says `Depends on: Issue N`
  for an existing N;
- no secrets, no `.env*` (not even `.env.example`), no `.DS_Store`, no file over 1 MB;
- `results/` untouched by the PR author, and when present: `metrics.json`,
  `action-run.json`, `outcomes/report.json`, `outcomes/trials.jsonl`, `receipts/*.json`,
  and no `no_model_smoke` trials (smoke output is not evidence).

## What `results/` contains after the organisers' run

```text
results/
  action-run.json            # harness commit, Claude Code + model pins, repeats, timestamps
  metrics.json               # per-issue and cumulative metrics, medians + min–max, relative to control
  leaderboard.md             # this run's table
  outcomes/
    trials.jsonl             # evaluator-schema records, no answer or memory text
    report.json              # paired wins/losses, P50/P95, from the cognee-report skill's summarize
  cognee-report.json         # cognee arm only: `plugin_eval.py report --since all --format json`
  receipts/issue-NN.json     # injection receipts (cognee-evidence.py explain, or the entrant's receipt.sh)
  injected/issue-NN/*.txt    # the context dumps the runner counted
  transcripts/issue-NN.jsonl # redacted Claude Code transcripts
  verify/issue-NN.json       # visible failure counts vs target, private grader pass/fail
  final.diff                 # the arm's final code against the baseline
```

The action results and the observation-skill outputs are **submitted together**: a PR
whose `results/` lacks `outcomes/` or `receipts/` is marked incomplete and does not enter
the leaderboard until the organisers re-attach them.

## Before you write yours

Read two or three merged submission PRs from earlier events; the folder-per-team pattern is
the same:

- Company Brain, SF Tech Week 2026-10-07: PRs #55–#61
- Cognee Cloud, Berlin 2026-06-19: PRs #34, #38, #43

Common mistakes they show: editing `templates/SUBMISSION.md` in place, a folder at the
repository root, `.env.example` committed, `.DS_Store` committed. CI refuses all four now.
