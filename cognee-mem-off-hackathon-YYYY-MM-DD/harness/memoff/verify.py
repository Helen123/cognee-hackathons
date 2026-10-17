"""Verify one issue inside a workspace: visible-suite failure target + private grader.

Run from the workspace (the sequencer and the outcomes runner both ``cwd`` there)::

    python3 -m memoff.verify --issue 3

Environment:
  MEMOFF_ISSUES_DIR    directory with the public issue files (default: packaged copy)
  MEMOFF_PRIVATE_DIR   directory holding ``graders/test_issue_NN.py`` (optional; when
                       absent only the visible target is checked and the result says so)
  MEMOFF_PYTHON        interpreter that has xitkit's dev extras installed
                       (default: ``.venv/bin/python`` in the workspace, else sys.executable)
  MEMOFF_VERIFY_OUT    write the JSON result there as well as to stderr

Exit status 0 when every gate passes, 1 otherwise. The evaluator ANDs this into
``task_success``; the sequencer also stores the JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SUMMARY_RE = re.compile(r"(?:(?P<failed>\d+) failed)?(?:, )?(?P<passed>\d+) passed")


def parse_pytest_summary(output: str) -> dict:
    """Return {'failed': n, 'passed': m} from pytest's last summary line."""
    failed = passed = None
    for line in reversed(output.splitlines()):
        if " passed" in line or " failed" in line or "no tests ran" in line:
            f = re.search(r"(\d+) failed", line)
            p = re.search(r"(\d+) passed", line)
            e = re.search(r"(\d+) error", line)
            failed = (int(f.group(1)) if f else 0) + (int(e.group(1)) if e else 0)
            passed = int(p.group(1)) if p else 0
            break
    if failed is None:
        raise ValueError("no pytest summary line found")
    return {"failed": failed, "passed": passed}


def default_issues_dir() -> Path:
    env = os.environ.get("MEMOFF_ISSUES_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "challenge" / "issues"
        if cand.is_dir():
            return cand
    raise FileNotFoundError("set MEMOFF_ISSUES_DIR to the challenge/issues directory")


def failure_target(issue: int, issues_dir: Path) -> int:
    from .suite import load_issues

    for item in load_issues(issues_dir):
        if item.number == issue:
            return item.failures_after
    raise ValueError(f"unknown issue {issue}")


def workspace_python(workspace: Path) -> str:
    env = os.environ.get("MEMOFF_PYTHON")
    if env:
        return env
    venv = workspace / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def run_visible_suite(workspace: Path, python: str, timeout: float) -> dict:
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = proc.stdout + "\n" + proc.stderr
    try:
        counts = parse_pytest_summary(out)
    except ValueError:
        counts = {"failed": None, "passed": None}
    return {"returncode": proc.returncode, **counts, "tail": out[-4000:]}


def run_private_grader(workspace: Path, python: str, issue: int, private_dir: Path, timeout: float) -> dict:
    grader = private_dir / "graders" / f"test_issue_{issue:02d}.py"
    if not grader.is_file():
        return {"present": False, "passed": None, "path": str(grader)}
    env = dict(os.environ, MEMOFF_WORKSPACE=str(workspace), PYTHONPATH=str(workspace), MEMOFF_AFTER_ISSUE=str(issue))
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(grader)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return {
        "present": True,
        "passed": proc.returncode == 0,
        "path": str(grader),
        "tail": (proc.stdout + proc.stderr)[-4000:],
    }


def verify(issue: int, workspace: Path, *, timeout: float = 600.0) -> dict:
    issues_dir = default_issues_dir()
    target = failure_target(issue, issues_dir)
    python = workspace_python(workspace)
    visible = run_visible_suite(workspace, python, timeout)
    visible_ok = visible["failed"] == target
    result = {
        "issue": issue,
        "workspace": str(workspace),
        "visible": {**visible, "target_failures": target, "ok": visible_ok},
        "private": {"present": False, "passed": None},
        "ok": visible_ok,
    }
    private_dir = os.environ.get("MEMOFF_PRIVATE_DIR")
    if private_dir:
        grader = run_private_grader(workspace, python, issue, Path(private_dir), timeout)
        result["private"] = grader
        if grader["present"]:
            result["ok"] = visible_ok and bool(grader["passed"])
        else:
            result["ok"] = False
            result["private"]["reason"] = "grader file missing while MEMOFF_PRIVATE_DIR is set"
    else:
        result["private"]["reason"] = "MEMOFF_PRIVATE_DIR unset: visible target only"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args(argv)
    result = verify(args.issue, args.workspace.resolve(), timeout=args.timeout)
    text = json.dumps(result, indent=2)
    out = os.environ.get("MEMOFF_VERIFY_OUT")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text + "\n", encoding="utf-8")
    print(text, file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
