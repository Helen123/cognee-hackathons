# Mem Off Submission

Copy this file to `submissions/<team-slug>/SUBMISSION.md` and fill every section. Keep the
headings exactly as they are: CI checks for them. Do not edit `templates/SUBMISSION.md`.

## Team

- Team name:
- Participants (GitHub handles):
- Contact for results (GitHub handle or email):

## Track

- [ ] Track 1 — Run a memory system (`memory.yml` + scripts in this folder)
- [ ] Track 2 — Extend the benchmark (`issues/<NN-slug>/ISSUE_PROPOSAL.md` in this folder)

## What you entered

### Track 1 — the memory system

- System name and version/commit:
- Where it lives (repo link) and how the harness installs it (`install.sh` summary):
- Hooks used (SessionStart / UserPromptSubmit / PostToolUse / Stop / SessionEnd / MCP / skills):
- Storage and declared network endpoints:
- The memory system's own model(s): provider, model, embedding model — or `none`:
- Pre-index before issue 1? What does it index and how long does it take?
- How `wipe.sh` empties the store and how `wipe_check.sh` proves it:
- How `wait.sh` knows post-session processing is done:
- What `receipt.sh` reports (ids, ranks, reasons) and what `usage.sh` measures:
- Anything non-default in the configuration, and why it is still fair:

### Track 2 — the proposed issue(s)

One line per proposal; the detail is in each `ISSUE_PROPOSAL.md`.

- `issues/09-<slug>`: title — type — links back to Issue N — pilot run: yes/no

## Recall story (Track 1, for the Best Recall Story award)

From `results/injected/issue-08/` and `results/receipts/issue-08.json`, after the organisers
attach them: what was recalled on issue 8, why it was selected over what was not, and why it
helped (or did not). Quote the dump, not the chat.

## Memory report

Produced by the `memoff-memory-report` skill (install: `skills/memoff-memory-report/install.sh
--event "<event>" --team <team-slug>`; its wrap-up copies the files here). Required for Track 1.

- `report/memoff-report.md` and `report/memoff-report.json` present: yes / no
- Runs recorded (count, of which smoke):
- The one number you would show a judge, and the run folder it comes from:

## Reproduction

```bash
# from the hackathon folder, with the harness installed and the cognee plugin present
memoff run --arms submissions/<team-slug> --repeats 1 --out /tmp/memoff-<team-slug> \
  --xitkit-source /path/to/xitkit --model <pinned model>
```

Environment variables your system needs (names only, never values):

```text
```

## Links

- Repo:
- Demo (Loom / YouTube) or local instructions:
- Slides / write-up:
- Anything else:

## Results

Written by the GitHub Action after the organisers' run. Do not edit `results/` by hand.
