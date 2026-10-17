# Issue 8 — Add controlled task-file discovery

Type: small feature · Expected visible-suite failures after this issue: **0** · Depends on: Issue 7

## Context

`TaskService.find_task_files` automatically reads every `.xit` and `.md` file below the search root, including files in hidden directories. Users cannot exclude generated, archived, or private task files.

Add a small discovery feature: automatic discovery should focus on `.xit` files and support a root-level `.xitignore` file. Explicit `-f` selections must remain available.

## Scope

Included:

- Automatically discover `.xit` files only.
- Skip any directory whose name starts with `.`.
- Read ignore patterns from `.xitignore` in the search root.
- Match each pattern against the file path relative to the search root, using forward slashes and Python `PurePath.full_match` pattern rules.
- Ignore blank lines and lines whose first non-space character is `#`.
- Apply `.xitignore` only to automatic discovery.
- Keep explicit `-f` selection working for `.md` files and ignored `.xit` files.
- Document automatic discovery, explicit Markdown reads, and `.xitignore` syntax.
- Update repository tests that currently expect automatic Markdown discovery.

Excluded:

- Reading `.gitignore`.
- Supporting negated `!` patterns.
- Searching for `.xitignore` files below the search root.
- Writing to Markdown files.

## Acceptance Criteria

- Automatic discovery returns matching `.xit` files and does not return `.md` files.
- Files below hidden directories are not discovered.
- A root `.xitignore` excludes paths that match its active patterns.
- Blank lines and comment lines in `.xitignore` have no effect.
- `show -f notes.md` still reads Markdown, and `show -f ignored.xit` still reads an ignored file.
- `.gitignore` does not change xitkit discovery.
- The README explains the new behavior, and the full visible test suite passes.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 7 must be complete. This issue builds on the directory behavior from Issue 1.

## Rollout / Release

- docs updated: Document `.xit` discovery, explicit `.md` selection, and `.xitignore` patterns.
- release notes: Record the discovery change when a release is prepared; no release is required for the experiment.
