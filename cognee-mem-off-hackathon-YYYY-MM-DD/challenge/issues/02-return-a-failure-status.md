# Issue 2 — Return a failure status when commands fail

Type: reliability · Expected visible-suite failures after this issue: **5** · Depends on: Issue 1

## Context

`Command.execute` catches errors and returns normally. The terminal may print an error while the process exits with status 0, so scripts cannot distinguish failure from success. Interactive helpers also treat a cancelled Questionary prompt as ordinary data. `RecurTaskCommand` can write new tasks before discovering that the source task has no due date.

Make command results safe and predictable.

## Scope

Included:

- Make errors handled by `Command.execute` produce process exit status 1.
- Keep successful commands at exit status 0.
- Keep Click's own usage errors at its standard exit status 2.
- Treat `None` returned by an active `select_*` or `ask_*` prompt as cancellation. Print `Cancelled.` and exit with status 1.
- Make `RecurTaskCommand` reject a task without a due date before it changes a file.
- Keep `--debug` behavior useful by allowing the original exception to reach the caller.
- Update existing tests that currently expect status 0 together with an error message.

Excluded:

- Rewriting every error message.
- Changing successful command output.
- Restoring or removing the broken `edit` command in this issue.

## Acceptance Criteria

- An `XitError` handled inside a command prints one clear error and the CLI exits with status 1.
- An unexpected error exits with status 1; with `--debug`, the original exception is available to the caller.
- A cancelled interactive prompt prints `Cancelled.`, does not print a `NoneType` error, and exits with status 1.
- Recurring a task with no due date exits with status 1 and leaves the file bytes unchanged.
- Successful commands still exit with status 0, and Click usage errors still exit with status 2.
- No new test fails, and the five unrelated due-date and edit failures remain.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 1 must be complete.

## Rollout / Release

- docs updated: Not required.
- release notes: Record corrected exit statuses when a release is prepared; no release is required for the experiment.
