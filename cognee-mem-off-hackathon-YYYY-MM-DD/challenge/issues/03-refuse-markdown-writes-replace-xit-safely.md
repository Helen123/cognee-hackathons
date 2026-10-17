# Issue 3 — Refuse Markdown writes and replace .xit files safely

Type: data-safety bug fix · Expected visible-suite failures after this issue: **4** · Depends on: Issue 2

## Context

`File.write` rebuilds a file from parsed sections and opens the destination with write mode. This creates three risks:

- Writing a `.md` file deletes its headings, prose, and code fences.
- `Description.set_due_date` moves an existing due date to the end of its task line.
- A failure during writing can leave a truncated file.

This issue prevents destructive Markdown writes and partial `.xit` replacement. It does not make every `.xit` file round-trip byte for byte.

## Scope

Included:

- Refuse every operation that would create or change a `.md` file. Reject a missing Markdown path before xitkit creates an empty file. Reading explicitly selected Markdown files must continue to work.
- Make `Description.set_due_date` replace an existing due date where it already appears. Append a due date only when the description does not already contain one.
- Make successful `.xit` writes use a temporary file in the destination directory and replace the destination only after the complete content is ready.
- Keep the original file unchanged when preparing or replacing the new file fails.
- Keep adding the first task to a new or empty `.xit` file working.
- Update the README to state that Markdown files are read-only.
- Add or update repository tests for this behavior.

Excluded:

- Writing changes back to Markdown files.
- Preserving arbitrary invalid lines in malformed `.xit` files.
- Replacing the current parser with a line-based editor.

## Acceptance Criteria

- A command that would create or change a `.md` file exits with status 1 and names the file. An existing file keeps its bytes, and a missing file is not created.
- Explicit `show -f notes.md` still reads tasks inside Markdown code fences.
- Replacing an existing due date keeps it in the same position within the description.
- If a `.xit` write fails before replacement completes, the destination keeps its original bytes.
- A successful `.xit` write leaves no temporary file behind.
- Adding a task to a new or empty `.xit` file still succeeds.
- The due-date baseline failure passes, no new test fails, and four unrelated edit failures remain.

## Metrics / Instrumentation

Not required in xitkit. The external benchmark runner records experiment metrics.

## Dependencies

Issue 2 must be complete.

## Rollout / Release

- docs updated: State that `.md` files can be read but not changed.
- release notes: Not required for the experiment.
