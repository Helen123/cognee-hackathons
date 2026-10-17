"""Build the xitkit outcomes suite from the public issue files.

One case per issue. ``prompt`` is the Part A text verbatim. ``expected`` holds the
single held-out claim the adapter must make (``status = implemented``); the real
gate is ``verify``: the visible-suite failure target and the private grader.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

HEADER_RE = re.compile(
    r"^Type: (?P<type>.+?) · Expected visible-suite failures after this issue: "
    r"\*\*(?P<failures>\d+)\*\* · Depends on: (?P<deps>.+)$",
    re.M,
)
TITLE_RE = re.compile(r"^# Issue (?P<number>\d+) — (?P<title>.+)$", re.M)

XITKIT_REPO = "https://github.com/hoechstleistungshaartrockner/xitkit.git"
XITKIT_REVISION = "2fd55de4d3d7e49f10b92eadec252cfc40688dab"
BASELINE_FAILURES = 11
BASELINE_PASSED = 769


@dataclass(frozen=True)
class Issue:
    number: int
    slug: str
    title: str
    type: str
    failures_after: int
    depends_on: str
    text: str

    @property
    def case_id(self) -> str:
        return f"issue-{self.number:02d}"


def load_issues(issues_dir: Path) -> list[Issue]:
    issues = []
    for path in sorted(issues_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = TITLE_RE.search(text)
        header = HEADER_RE.search(text)
        if not title or not header:
            raise ValueError(f"{path.name}: missing title or header line")
        issues.append(
            Issue(
                number=int(title["number"]),
                slug=path.stem,
                title=title["title"].strip(),
                type=header["type"].strip(),
                failures_after=int(header["failures"]),
                depends_on=header["deps"].strip(),
                text=text,
            )
        )
    numbers = [i.number for i in issues]
    if numbers != list(range(1, len(issues) + 1)):
        raise ValueError(f"issues must be numbered 1..n without gaps, got {numbers}")
    return issues


def expected_claims() -> dict:
    # No memory is seeded, so there is no false fact to adopt: false_values stays empty and
    # the evaluator's false_memory_adoption_rate reads 0 for every arm.
    return {"status": {"value": "implemented", "sources": [], "false_values": []}}


def verify_argv(issue: Issue) -> list[str]:
    # The harness interpreter: the stock runner and the sequencer both exec this argv
    # with the workspace as cwd, where no `python3` has memoff installed.
    return [sys.executable, "-m", "memoff.verify", "--issue", str(issue.number)]


def build_suite(
    issues: list[Issue],
    *,
    model: str,
    max_tokens: int,
    variants: list[str],
    repository_path: str | None = None,
    variant_config: dict | None = None,
) -> dict:
    suite = {
        "model": model,
        "max_tokens": max_tokens,
        "variants": variants,
        "variant_config": variant_config or {},
        "memoff": {
            "xitkit_repo": XITKIT_REPO,
            "xitkit_revision": XITKIT_REVISION,
            "baseline": {"failed": BASELINE_FAILURES, "passed": BASELINE_PASSED},
            "chained": True,
            "note": (
                "Cases are a chained sequence: the sequencer keeps the accepted code of "
                "issue n as the starting state of issue n+1 and ends the agent session "
                "between them. The stock `outcomes run` command treats cases as "
                "independent; use `memoff run` for the chain and `outcomes run` only for "
                "single-issue pilots."
            ),
        },
        "cases": [
            {
                "id": issue.case_id,
                "number": issue.number,
                "title": issue.title,
                "type": issue.type,
                "failures_after": issue.failures_after,
                "prompt": issue.text,
                "memory": [],
                "expected": expected_claims(),
                "verify": verify_argv(issue),
            }
            for issue in issues
        ],
    }
    if repository_path:
        suite["repository"] = {"path": repository_path, "revision": XITKIT_REVISION}
    return suite


def issues_summary(issues: list[Issue]) -> list[dict]:
    return [
        {k: v for k, v in asdict(i).items() if k != "text"} | {"case_id": i.case_id}
        for i in issues
    ]


def write_suite(suite: dict, out: Path) -> None:
    out.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
