# Issue 7 — Remove the Pomodoro feature

Type: feature removal · Expected visible-suite failures after this issue: **0** · Depends on: Issue 6

## Context

After Issue 6, the Pomodoro timer is isolated behind an optional dependency and a lazy import. It is still a separate terminal application that shares no task-management code with xitkit.

The product decision is now to remove the timer and keep xitkit focused on task files.

## Scope

Included:

- Remove `xitkit/pomodoro.py` and `PomodoroApp`.
- Remove the `pomodoro` Click command, lazy import, and missing-dependency error path from `__main__.py`.
- Remove the `pomodoro` optional dependency and every `textual` dependency from `pyproject.toml`.
- Remove the Pomodoro feature, command, and installation instructions from the README.
- Remove the Pomodoro section from `todo.xit`.
- Remove tests that only cover Pomodoro. Do not skip them.

Excluded:

- Adding a replacement timer.
- Changing task-management commands.
- Removing other optional or development dependencies.

## Acceptance Criteria

- `xit --help` does not list `pomodoro`.
- Running `xit pomodoro` produces Click's normal unknown-command error.
- `xitkit.pomodoro` and `PomodoroApp` no longer exist.
- `pyproject.toml` contains no `textual` dependency or `pomodoro` extra.
- The README and `todo.xit` contain no Pomodoro feature or follow-up work.
- The remaining runtime dependencies are `rich`, `click`, and `questionary`, and the full visible test suite passes.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 6 must be complete. This issue removes the feature boundary created in Issue 6.

## Rollout / Release

- docs updated: Remove the feature, command, and optional installation.
- release notes: Record the feature removal when a release is prepared; no release is required for the experiment.
