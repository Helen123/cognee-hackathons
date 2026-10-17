# Mem Off — Which memory makes a coding agent cheaper?

📍 **Date and venue: TBD · 10:30 – 18:30 (local time)** · 🧠 **claude-mem × cognee × HelixDB × you**

> Folder name: rename `cognee-mem-off-hackathon-YYYY-MM-DD` to the event date before merging.

Memory systems for coding agents all claim the same thing: the agent stops re-discovering
the codebase on every session. Nobody has measured it on a fixed task where the answer is
known. Mem Off fixes the agent, the model, the repository and a sequence of eight issues,
**kills the agent's session after every issue**, and lets only the memory system carry
context forward. If memory works, issue 8 (which returns to the method changed in issue 1)
costs fewer turns, tokens and dollars than for an agent with no memory.

The leaderboard is **correctness-gated efficiency relative to a no-memory control**.

**First thing to do, before anything else** (everyone, both tracks):

```bash
claude plugin marketplace add topoteretes/cognee-integrations
claude plugin install cognee-memory@cognee          # brings the cognee-report observation skill
cd harness && uv venv && uv pip install -e ".[dev]" # the Mem Off harness
memoff pilot --smoke --issue 1 --repetitions 2 \
  --xitkit-source /path/to/xitkit --out /tmp/memoff-smoke   # proves the harness runs on your machine
```

The smoke run calls no model. Its numbers prove orchestration, never a memory effect.

## What is compared

| Arm | What runs |
|---|---|
| **Control** (`no_memory`) | Claude Code, no memory plugin, fresh session per issue |
| **claude-mem** | [`thedotmack/claude-mem`](https://github.com/thedotmack/claude-mem), pinned release, default settings |
| **cognee** | [cognee memory plugin for Claude Code](https://github.com/topoteretes/cognee-integrations/tree/main/integrations/claude-code), pinned release, local mode, repository pre-indexed into the code graph |
| **HelixDB** | HelixDB is a graph + vector + BM25 database; the HelixDB team fields the memory layer that runs on it (their `cmem` fork of claude-mem, Graphify-on-HelixDB, or a purpose-built plugin) |
| **Open track** | Any system that satisfies the [entrant contract](challenge/CONTRACT.md) |

The agent is **Claude Code** for v1. One model, one Claude Code version, one system prompt,
one Linux image, one Python 3.14, for every arm.

## The task: xitkit, eight issues in sequence

[xitkit](https://github.com/hoechstleistungshaartrockner/xitkit) is a small Python CLI task
manager. At commit `2fd55de` (v2.1.0) its suite reads **11 failed, 769 passed** on Python 3.14.
The eight issues in [`challenge/issues/`](challenge/issues/) are applied in order and keep
earlier code. The agent gets exactly that text, one issue per fresh session.

| # | Issue | Type | Failures after | Memory link |
|---|---|---|---|---|
| 1 | [Search the requested directory reliably](challenge/issues/01-search-the-requested-directory.md) | bug fix | 6 | first |
| 2 | [Return a failure status when commands fail](challenge/issues/02-return-a-failure-status.md) | reliability | 5 | — |
| 3 | [Refuse Markdown writes, replace .xit safely](challenge/issues/03-refuse-markdown-writes-replace-xit-safely.md) | data-safety | 4 | — |
| 4 | [Remove the broken edit command](challenge/issues/04-remove-the-broken-edit-command.md) | removal | 0 | command layer from #2 |
| 5 | [Write marked tasks once per file](challenge/issues/05-write-marked-tasks-once-per-file.md) | performance | 0 | `File.write` from #3 |
| 6 | [Make Pomodoro optional and runnable](challenge/issues/06-make-pomodoro-optional-and-runnable.md) | packaging + fix | 0 | — |
| 7 | [Remove the Pomodoro feature](challenge/issues/07-remove-the-pomodoro-feature.md) | removal | 0 | removes the boundary #6 created |
| 8 | [Add controlled task-file discovery](challenge/issues/08-add-controlled-task-file-discovery.md) | feature | 0 | `find_task_files` from #1 |

Each issue passes only when the visible suite hits its failure target **and** a private
grader passes. The graders, the reference implementation and the review notes stay with the
organisers until after the event. Issues 4, 5, 7 and 8 return to code changed earlier: they
are where memory should matter most, and they are the headline **memory delta** metric.

## How a run works

```text
for arm, for repeat:
  fresh workspace: xitkit @ 2fd55de, Python 3.14 venv
  install memory system · wipe its store (verified) · optional pre-index (timed separately)
  for issue 1..8:
    fresh Claude Code session, fixed system prompt, the issue text
    agent works until it stops (turn and dollar caps)
    visible suite -> failure target?   private grader -> pass?
    record pass/fail + metrics BEFORE looking at efficiency
    commit the code · end the session (SessionEnd/Stop hooks fire) · wait for the memory system
```

Three repeats per arm minimum; medians and min–max are reported. The day fits one repeat;
the others run overnight and the final leaderboard lands the next morning.

The harness is built on the **`cognee-report` skill's `outcomes` protocol** (part of the
cognee plugin). Mem Off adds an *agent adapter* that drives Claude Code and a *sequencer*
that chains the eight issues; scoring and reporting are the skill's own, so
`plugin_eval.py outcomes report --trials results/outcomes/trials.jsonl` rebuilds any
submission's report. Details: [`challenge/PROTOCOL.md`](challenge/PROTOCOL.md),
[`harness/README.md`](harness/README.md).

## Metrics

Per issue and cumulative, per arm (median of repeats): pass/fail, agent turns, input /
output / cache tokens, the memory system's own tokens, injected-context characters, elapsed
time and post-session wait, cost (agent + memory), changed files; plus the evaluator's paired
wins/losses against control, P50/P95 latency, and the cognee arm's own `cognee-report`
scorecard. Full table and sources: [`challenge/METRICS.md`](challenge/METRICS.md).

**Correctness is a gate.** An arm that fails any grader is listed with its resource use but
not ranked. Never compare raw numbers across issues: they are not equally hard.

## Two tracks

### Track 1 — Run a memory system

Satisfy the [entrant contract](challenge/CONTRACT.md): a Claude Code plugin or hook bundle,
`install.sh` / `wipe.sh` / `wait.sh`, a `memory.yml` manifest, and a dump of every string
your system injects into the agent's context. The organisers run every entrant on the
frozen harness; nobody runs their own numbers.

Awards: **Leaderboard** (automatic), **Best Memory Delta** (issues 4/5/7/8), **Best Recall
Story** (what was recalled on issue 8, why it was selected, why it helped: the injected dump
and the receipt are the evidence, not a screenshot of "I remember"), **Most Portable**.

### Track 2 — Extend the benchmark

The eight issues are one opinion of what memory should buy an agent. If you believe a
harder or different kind of problem belongs here, propose **issue 9+** with
[`templates/ISSUE_PROPOSAL.md`](templates/ISSUE_PROPOSAL.md): the issue in the exact Part A
format, a *memory hypothesis* naming which earlier issue it links back to, its type, the
expected failure count, a private-grader sketch, evidence that you solved it on a branch,
and (optionally) a pilot run on the harness. The organisers publish a
[list of known gaps](challenge/KNOWN_GAPS.md) that are open to proposals.

Awards: **Best New Issue** (merged into the next edition's sequence, credited) and **Best
Pilot Evidence**. Accepted issues join the private v2 sequence after the event; the frozen v1
sequence never changes mid-day.

## Submissions: one pull request per team

Like every earlier cognee hackathon, a submission is a **PR to this repository from a
fork** adding one folder:

```text
cognee-mem-off-hackathon-<date>/submissions/<team-slug>/
  SUBMISSION.md                 # from templates/SUBMISSION.md
  memory.yml install.sh wipe.sh wait.sh    # Track 1
  issues/09-<slug>/ISSUE_PROPOSAL.md       # Track 2 (one folder per proposal)
  results/                      # written by the GitHub Action, never by hand
```

Read two or three merged submission PRs from earlier events before writing yours
([Company Brain SF](https://github.com/topoteretes/cognee-hackathons/pulls?q=is%3Apr+Submission+2026-10-07),
[Cognee Cloud Berlin](https://github.com/topoteretes/cognee-hackathons/pulls?q=is%3Apr+Submission+2026-06-19)).
About a third of past PRs edited the template in place, dropped a folder at the repository
root, or committed `.env.example`; a CI check now refuses those. Rules and the exact
`results/` contents: [`submissions/README.md`](submissions/README.md).

## Schedule — 10:30 to 18:30

| Time | What |
|---|---|
| 10:30 | Doors, laptops, runner access. Everyone installs the cognee plugin for the `cognee-report` skill and runs the offline smoke once. Organisers hand out the control-arm results and the pinned arms' `memory.yml` |
| 11:00 | Opening: the protocol, why the session is killed between issues, how the leaderboard is gated. Five-minute write/read-path talks: claude-mem, cognee, HelixDB |
| 11:45 | Hacking. Track 1: get `install → wipe → issue 1 → wait` green on the runner. Track 2: pick a gap, draft the issue, solve it on a branch |
| 13:00 | Lunch. Organisers start the first repeat for every green Track 1 entrant |
| 14:00 | Office hours per arm (one maintainer each). Track 2 pilots on idle runner slots |
| 16:00 | **Submission PRs open** — CI green by 16:45 |
| 16:45 | Freeze. First repeats finish; the Action attaches `results/` to each PR |
| 17:00 | Demos, three minutes each. Track 1 shows the issue-8 injected dump and the delta; Track 2 shows the issue, the memory hypothesis and pilot numbers |
| 18:00 | Preliminary leaderboard (one repeat), Best Recall Story, Best New Issue, Best Pilot Evidence |
| 18:30 | Close. Repeats two and three run overnight; the final leaderboard is published here and on each PR next morning |

## Fairness rules, short form

- Same Claude Code version, model, system prompt, permission mode, turn and dollar caps,
  Python and container image for every arm. No network except the memory system's declared
  endpoints and the LLM API.
- Pre-indexing the repository before issue 1 is allowed, timed, and reported as its own row.
- The memory system's own LLM and embedding spend is a first-class column. Saving 20 % of
  agent tokens by spending 30 % in an observer model is not a win.
- Disqualifying: reading `/benchmark/private/`, shipping xitkit-specific hints inside the
  system, using the memory system's LLM to solve the issue, or persisting anything across
  repeats (the runner verifies the wipe).

## Links

- [Cognee on GitHub](https://github.com/topoteretes/cognee) · [Documentation](https://docs.cognee.ai/) · [Discord](https://discord.gg/NQPKmU5CCg)
- [claude-mem](https://github.com/thedotmack/claude-mem) · [HelixDB](https://github.com/HelixDB/helix-db) · [xitkit](https://github.com/hoechstleistungshaartrockner/xitkit)
- The `cognee-hackathon-feedback` agent skill is installed in this folder: your coding agent keeps a private record of how cognee behaved for you. Hand `cognee-feedback.md` to the organisers at the end.
