# Benchmark issue proposal — Issue 9: Honour the project's error-message convention

An **example** of a filled proposal, to show the level of detail expected. It is not part of
the v1 sequence and has not been solved on a reference branch (see "Evidence").

## Issue text

# Issue 9 — Honour the project's error-message convention

Type: cross-session preference · Expected visible-suite failures after this issue: **0** · Depends on: Issue 2

### Context

Issue 2 made every handled error exit with status 1 and print one clear message. Since then
the maintainers have adopted a convention, stated in `CONTRIBUTING.md` (added by this issue's
fixture): every user-facing error starts with `xit: ` and names the file it concerns when
there is one. `FileParser.parse_file` and `TaskService.find_task_files` still raise messages
without the prefix, and the Markdown-write refusal from Issue 3 names the file but has no
prefix either.

### Scope

Included:

- Prefix every `XitError` message printed by `Command.execute` with `xit: `.
- Include the file path in errors raised while reading, parsing or refusing to write a file.
- Add or update tests for the prefix and the file name.

Excluded:

- Changing exit statuses.
- Changing Click usage errors.
- Rewording messages beyond the prefix and the file name.

### Acceptance Criteria

- Every handled error printed by the CLI starts with `xit: `.
- Errors about a specific file include its path.
- Successful output is unchanged, and the full visible test suite passes.

### Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

### Dependencies

Issue 2 must be complete. This issue builds on the error path it introduced.

### Rollout / Release

- docs updated: `CONTRIBUTING.md` states the convention.
- release notes: Not required.

## Memory hypothesis

The convention is stated once, in a file added with this issue's fixture, but the *shape* of
the error path was built by the agent in issue 2 and touched again in issue 3 (the Markdown
refusal). An agent with memory of where errors are formatted (one place, `Command.execute`,
after issue 2) applies the prefix in one edit; an agent without memory rediscovers the
command layer and tends to prefix messages at each raise site, which the grader catches as
double prefixes. Links back to Issue 2 and Issue 3.

## Type

New type, *cross-session preference*: a convention stated in the project that must be
honoured unprompted in code the agent itself wrote in an earlier session.

## Expected failure count

- Visible-suite failures after the issue: 0
- Visible tests expected to change: `tests/test_cli.py` error-message assertions (about 12 cases) gain the `xit: ` prefix.

## Private grader sketch

Parametrise one handled error per command family; assert stdout/stderr starts with `xit: `
exactly once (no `xit: xit: `), includes the fixture file path for file errors, exit status
is 1; assert a successful `show` prints no `xit: ` anywhere; assert `CONTRIBUTING.md` exists
and names the convention.

## Evidence it is solvable

Not yet solved on a branch. **A real proposal must include this**: a branch link and the
suite result after the change. This example is incomplete on purpose so nobody copies it as
a finished submission.

## Pilot

Not run.
