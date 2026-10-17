# Issue 5 — Write marked tasks once per file

Type: performance and maintenance · Expected visible-suite failures after this issue: **0** · Depends on: Issue 4

## Context

The current path through `UpdateCommand._execute`, `MarkTaskCommand._edit_task`, `Task.save`, and `File.write` writes the full file once for every marked task. Marking ten tasks in one file therefore writes that file ten times.

Change the `mark` batch so it saves each changed file once.

## Scope

Included:

- Apply all requested status changes in memory before saving them.
- Save each file changed by one `mark` command exactly once.
- Keep one success message per changed task and the existing batch summary.
- Print success messages only after the related file has been saved successfully.
- Add or update repository tests for single-file and multi-file batches.

Excluded:

- Changing write behavior for `move`, `recur`, `rm`, `prio`, `tag`, `untag`, or `reschedule`.
- Adding rollback across several files.
- Changing task IDs.

## Acceptance Criteria

- Marking three tasks in one file persists all three changes and calls `File.write` once for that file.
- Marking tasks from two files calls `File.write` once for each changed file.
- The command prints one confirmation per changed task and one batch summary.
- A single-task `mark` still behaves as before.
- The full visible test suite passes.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 4 must be complete. This issue relies on the safe `File.write` behavior from Issue 3.

## Rollout / Release

- docs updated: Not required.
- release notes: Not required.
