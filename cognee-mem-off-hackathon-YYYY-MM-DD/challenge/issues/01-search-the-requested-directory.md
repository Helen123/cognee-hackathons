# Issue 1 — Search the requested directory reliably

Type: bug fix · Expected visible-suite failures after this issue: **6** · Depends on: none (first issue)

## Context

`TaskService.find_task_files(directory)` finds `.xit` and `.md` files, then makes every path relative to the process working directory. A search fails when `directory` is outside that working directory. It can also fail when macOS exposes the same temporary directory through `/var` and `/private/var`.

The command should search the directory the user supplied. Its result must not depend on where xitkit was started.

## Scope

Included:

- Make `TaskService.find_task_files` return sorted, absolute file paths from the requested directory.
- Keep recursive discovery of both `.xit` and `.md` files for now.
- Make `xit show --directory <path>` and `xit stats --directory <path>` work when `<path>` is outside the current working directory.
- Add or update repository tests for this behavior.

Excluded:

- Changing which file extensions are discovered.
- Adding ignore rules.
- Changing file parsing or writing.

## Acceptance Criteria

- `TaskService.find_task_files(search_root)` returns sorted, absolute paths below `search_root` when the current working directory is somewhere else.
- The result includes recursively discovered `.xit` and `.md` files, but not unrelated extensions.
- `show --directory` and `stats --directory` succeed for an existing directory outside the current working directory.
- The five baseline tests related to directory discovery pass, no new test fails, and six unrelated baseline failures remain.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

None. This is the first issue.

## Rollout / Release

- docs updated: Not required.
- release notes: Not required.
