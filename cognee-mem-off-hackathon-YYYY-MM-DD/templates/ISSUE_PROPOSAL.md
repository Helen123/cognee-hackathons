# Benchmark issue proposal — Issue 9: <short title>

Copy to `submissions/<team-slug>/issues/09-<slug>/ISSUE_PROPOSAL.md`. One file per proposed
issue. Keep the seven `##` sections: CI checks for them. The issue text below follows the
exact format of `challenge/issues/*.md` so an accepted proposal drops into the sequence as-is.

## Issue text

# Issue 9 — <short title>

Type: <bug fix | reliability | data-safety | removal | performance | packaging | feature | new type> · Expected visible-suite failures after this issue: **0** · Depends on: Issue <N>

### Context

<What is wrong or missing today, in xitkit's real names (`TaskService.find_task_files`,
`File.write`, …). No implementation hints.>

### Scope

Included:

- …

Excluded:

- …

### Acceptance Criteria

- …
- The full visible test suite passes (or: exactly N unrelated failures remain).

### Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

### Dependencies

Issue <N> must be complete. <Which earlier change it builds on.>

### Rollout / Release

- docs updated: …
- release notes: …

## Memory hypothesis

<One paragraph: why memory should matter here and which earlier issue it links back to.
"It is hard" is not enough; "it needs the atomic-write boundary from issue 3 and the ignore
rules from issue 8 together" is.>

## Type

<One of the eight types, or a new one with a justification, e.g. *cross-session preference*:
the user stated a convention in issue 2 the agent must honour unprompted here.>

## Expected failure count

- Visible-suite failures after the issue: <n>
- Visible tests the issue is expected to add, change or remove: <list>

## Private grader sketch

<What the grader asserts, in the style of the eight private graders: fixtures it builds,
calls it makes, bytes it compares. A full `pytest` file in this folder (`grader_sketch.py`)
earns more than prose. It stays in the public PR; it is not a v1 grader.>

## Evidence it is solvable

<Link to a branch or attach a diff. The visible-suite result after your change
(`N failed, M passed`). An unsolved proposal is a feature request, not a benchmark issue.>

## Pilot

<Optional. `memoff pilot --issue 9 …` output (`pilot-metrics.json` in this folder): control
vs one memory arm, repetitions, task success, turns, tokens, cost. A pilot that shows a
memory delta is the strongest possible submission. Say "not run" if not run.>
