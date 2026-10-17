# Issue 4 — Remove the broken edit command

Type: feature removal · Expected visible-suite failures after this issue: **0** · Depends on: Issue 3

## Context

`xit edit` is not usable. Its Click callback rejects its own arguments, `EditTaskCommand` is incomplete, and `TaskService.update_task_description` calls repository methods that do not exist.

Five baseline test cases referred to this path. Issue 2 corrected the shared missing-arguments case. When this issue begins, four dedicated `TestEditCLI` cases still fail.

Remove the unsupported feature instead of adding a new editing design.

## Scope

Included:

- Remove the `edit` Click command from `__main__.py`.
- Remove `EditTaskCommand` and `CommandFactory.create_edit_command`.
- Remove `TaskService.update_task_description`.
- Remove the `edit` example from the README.
- Remove the completed `edit` claim from `todo.xit`.
- Delete the four dedicated `TestEditCLI` cases. Remove `edit` from the shared missing-arguments parameter list. Do not skip either kind of test.

Excluded:

- Adding a replacement edit command.
- Changing `rm`, `mark`, or other task-update commands.
- General command-layer cleanup.

## Acceptance Criteria

- `xit --help` does not list `edit`.
- Running `xit edit` produces Click's normal unknown-command error.
- `EditTaskCommand`, `CommandFactory.create_edit_command`, and `TaskService.update_task_description` no longer exist.
- The README and `todo.xit` no longer say that task descriptions can be edited with `xit edit`.
- The four dedicated `TestEditCLI` cases are removed, and the `edit` case is removed from the shared missing-arguments test.
- The full visible test suite passes.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 3 must be complete.

## Rollout / Release

- docs updated: Remove the command and its example.
- release notes: Record the removal when a release is prepared; no release is required for the experiment.
