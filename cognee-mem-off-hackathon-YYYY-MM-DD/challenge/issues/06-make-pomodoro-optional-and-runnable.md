# Issue 6 — Make Pomodoro optional and runnable

Type: packaging optimization and bug fix · Expected visible-suite failures after this issue: **0** · Depends on: Issue 5

## Context

xitkit imports `PomodoroApp` when any CLI command starts, and `textual` is a required runtime dependency. Users who only manage task files must install and import a terminal UI framework they never use.

The timer command is also broken. It passes the Click `debug` value into `PomodoroApp`, which forwards that unsupported argument to Textual's `App` and raises `TypeError`.

Make the timer runnable, but load its code and dependency only when the user runs `xit pomodoro`.

## Scope

Included:

- Move `textual` from required dependencies to a `pomodoro` optional dependency in `pyproject.toml`.
- Remove the top-level `PomodoroApp` import from `__main__.py` and load it only when the `pomodoro` command runs.
- Keep `xit --help` and all task commands working when `textual` is not installed.
- When `xit pomodoro` runs without the optional dependency, print `Install xitkit[pomodoro] to use the timer.` and exit with status 1.
- Keep the existing `--debug` option for CLI compatibility, but do not pass it into `PomodoroApp`.
- With the optional dependency installed, construct and run `PomodoroApp` with only the requested work and break durations.
- Document `pip install xitkit[pomodoro]` in the README.
- Add or update repository tests for both dependency states.

Excluded:

- Changing the timer controls, display, or timing behavior.
- Changing the supported Python versions.
- Adding a CI matrix.
- Removing the Pomodoro feature.

## Acceptance Criteria

- Plain `pip install xitkit` does not install `textual`; `pip install xitkit[pomodoro]` does.
- Importing the CLI and running task commands works when importing `textual` is blocked.
- `xit --help` still lists `pomodoro` without loading `textual`.
- Running `xit pomodoro` without `textual` prints the installation instruction and exits with status 1.
- With `textual` available, the command builds `PomodoroApp` with the requested work and break durations and does not pass the unsupported `debug` argument.
- The README explains the optional installation, and the full visible test suite passes.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 5 must be complete.

## Rollout / Release

- docs updated: Document the optional Pomodoro installation.
- release notes: Record the dependency change when a release is prepared; no release is required for the experiment.
