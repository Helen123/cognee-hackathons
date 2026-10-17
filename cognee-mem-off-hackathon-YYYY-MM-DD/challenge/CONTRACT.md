# Entrant contract (Track 1)

Applies to the three named systems and every open-track entrant alike. The common
denominator is Claude Code's hook lifecycle, so that is the contract.

## You ship

1. **A Claude Code plugin or hook bundle** using any of `SessionStart`, `UserPromptSubmit`,
   `PostToolUse`, `Stop`, `SessionEnd`, `PreCompact`, optionally MCP tools and skills.
   Nothing else touches the agent. Marketplace-installed plugins need no `plugin_dirs`;
   a bundle in your submission folder is passed with `claude --plugin-dir`.
2. **Scripts**, relative to your submission folder, all run with `sh`:
   - `install.sh` — installs the system on a clean Linux container. Idempotent.
   - `wipe.sh` — empties the memory store. `wipe_check.sh` (optional but recommended) exits
     non-zero when the store is not empty; the runner calls it after `wipe.sh`.
   - `wait.sh` — blocks until post-session processing (observer model, sync, improve) is
     done; exits non-zero on timeout. The runner calls it after every issue.
   - `preindex.sh` (if `preindex: true`) — indexes the repository before issue 1.
   - `receipt.sh` (optional) — prints a JSON receipt for the last session: what was injected
     and why (ids, ranks, reasons; no bodies). This is the Best Recall Story evidence.
   - `usage.sh` (optional) — prints JSON usage records for your system's own model and
     embedding spend since the last call: `[{"id": "...", "source": "server",
     "tokens_in": n, "tokens_out": n, "cost_usd": x, "token_basis": "...", "cost_basis": "..."}]`.
     Without it your spend is **unmeasured** (null), never zero, and totals stay unknown.
3. **`memory.yml`** validating against `harness/memoff/memory.schema.json`
   (template: `templates/memory.yml`).
4. **Injected-context logging.** Every string your system adds to the agent's context goes
   to `$MEMOFF_INJECTED_DIR` (one file per injection). The runner counts characters there.
   Claude Code silently replaces a hook block over roughly 10,000 characters with a stub;
   the dumps are checked for it.
5. **The `cognee-report` skill installed** (it comes with the cognee plugin). Its `outcomes`
   adapter protocol drives every entrant; its receipts and scorecard are part of the
   submission. See `PROTOCOL.md`.
6. **The `memoff-memory-report` skill installed** in your repo
   (`skills/memoff-memory-report/install.sh --event … --team …`). It produces
   `report/memoff-report.md` and `.json` from tool output; both are required in the
   submission and are read next to the Action's `results/`.

## Environment the runner gives you

| Variable | Meaning |
|---|---|
| `MEMOFF_ARM` | your `name` from `memory.yml` |
| `MEMOFF_MEMORY_STORE` / `COGNEE_PLUGIN_DATASET` | the store name for this (arm, repeat): shared across its eight issues, never across repeats |
| `MEMOFF_SESSION_ID` / `COGNEE_SESSION_ID` | the agent session for this issue |
| `MEMOFF_ISSUE` | 1..8 |
| `MEMOFF_WORKSPACE` | the xitkit checkout |
| `MEMOFF_INJECTED_DIR` | where to write injected context |
| `MEMOFF_STATE_DIR` | scratch space you may use per issue |
| `MEMOFF_WAIT_SECONDS` | bound for `wait.sh` (default 600) |

## Disqualifying

Reading `/benchmark/private/` or anything under the runner's results directory; shipping
solution text or xitkit-specific hints inside the system; calling an LLM to solve the issue
rather than to manage memory; persisting anything across repeats; a `wipe.sh` that does not
wipe (the runner checks).

## Cost accounting

The leaderboard ranks total cost: the agent's spend (from Claude Code's result) plus your
system's spend (from `usage.sh`). A system that saves agent tokens by spending more in an
observer model has not won.
