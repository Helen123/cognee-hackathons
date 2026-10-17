"""``memoff`` command line."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from . import adapter, check_submission, verify
from .paths import plugin_eval_script
from .sequencer import RunConfig, Sequencer, arms_from_paths
from .suite import build_suite, issues_summary, load_issues, write_suite


def default_issues_dir() -> Path:
    env = os.environ.get("MEMOFF_ISSUES_DIR")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        if (parent / "challenge" / "issues").is_dir():
            return parent / "challenge" / "issues"
    raise SystemExit("set MEMOFF_ISSUES_DIR or run from the hackathon folder")


def cmd_suite(args) -> int:
    issues = load_issues(args.issues_dir)
    suite = build_suite(issues, model=args.model, max_tokens=args.max_tokens, variants=args.variants, repository_path=args.repository)
    if args.out:
        write_suite(suite, args.out)
        print(f"wrote {args.out} with {len(suite['cases'])} cases")
    else:
        print(json.dumps(suite if args.full else issues_summary(issues), indent=2))
    return 0


def cmd_run(args) -> int:
    arms = arms_from_paths(args.arms, include_control=not args.no_control)
    cfg = RunConfig(
        issues_dir=args.issues_dir,
        out_dir=args.out,
        arms=arms,
        model=args.model,
        max_tokens=args.max_tokens,
        repeats=args.repeats,
        seed=args.seed,
        issue_timeout=args.timeout,
        adapter=json.loads(args.adapter) if args.adapter else [sys.executable, "-m", "memoff.adapter"],
        xitkit_source=args.xitkit_source,
        python_version=args.python,
        make_venv=not args.no_venv,
        smoke=args.smoke,
        stop_on_fail=args.stop_on_fail,
        only_issues=args.only,
    )
    result = Sequencer(cfg).run()
    print((args.out / "leaderboard.md").read_text())
    if result["meta"].get("report_skipped"):
        print("note:", result["meta"]["report_skipped"], file=sys.stderr)
    return 0


def cmd_pilot(args) -> int:
    """Single-issue pilot through the stock ``outcomes run`` of the cognee-report skill."""
    issues = [i for i in load_issues(args.issues_dir) if i.number == args.issue]
    if not issues:
        raise SystemExit(f"unknown issue {args.issue}")
    suite = build_suite(issues, model=args.model, max_tokens=args.max_tokens, variants=["no_memory", "cognee"], repository_path=str(args.xitkit_source))
    suite_path = args.out.parent / f"{args.out.name}.suite.json"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_suite(suite, suite_path)
    runner = [sys.executable, "-m", "memoff.adapter"] + (["--smoke"] if args.smoke else [])
    cmd = [sys.executable, str(plugin_eval_script()), "outcomes", "run", "--suite", str(suite_path), "--runner", json.dumps(runner),
           "--repetitions", str(args.repetitions), "--out", str(args.out), "--timeout", str(args.timeout)]
    env = dict(os.environ, MEMOFF_ISSUES_DIR=str(args.issues_dir))
    return subprocess.call(cmd, env=env)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="memoff", description="Mem Off benchmark harness")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("suite", help="print or write the xitkit outcomes suite")
    p.add_argument("--issues-dir", type=Path, default=None)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--variants", nargs="+", default=["no_memory", "cognee"])
    p.add_argument("--repository", default=None, help="local xitkit checkout for the stock runner")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_suite)

    p = sub.add_parser("run", help="run the chained eight-issue sequence per arm and repeat")
    p.add_argument("--issues-dir", type=Path, default=None)
    p.add_argument("--arms", nargs="*", default=[], help="memory.yml files or folders; the control arm is added unless --no-control")
    p.add_argument("--no-control", action="store_true")
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--timeout", type=float, default=3600.0, help="seconds per issue, agent plus verify")
    p.add_argument("--adapter", default=None, help="JSON argv of the agent adapter (default: memoff.adapter)")
    p.add_argument("--xitkit-source", type=Path, default=None, help="existing local xitkit clone (else cloned)")
    p.add_argument("--python", default="3.14", help="python version for the workspace venv")
    p.add_argument("--no-venv", action="store_true", help="skip creating the workspace venv (tests)")
    p.add_argument("--smoke", action="store_true", help="no model: validates the pipeline only")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--only", nargs="*", type=int, default=None, help="issue numbers to run (default all)")
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("pilot", help="one issue through the stock cognee-report `outcomes run`")
    p.add_argument("--issues-dir", type=Path, default=None)
    p.add_argument("--issue", type=int, required=True)
    p.add_argument("--xitkit-source", type=Path, required=True)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--repetitions", type=int, default=2)
    p.add_argument("--timeout", type=float, default=3600.0)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=cmd_pilot)

    p = sub.add_parser("verify", help="verify one issue in the current workspace")
    p.add_argument("--issue", type=int, required=True)
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.set_defaults(func=lambda a: verify.main(["--issue", str(a.issue), "--workspace", str(a.workspace)]))

    p = sub.add_parser("adapter", help="agent adapter (stdin request → stdout response)")
    p.add_argument("--smoke", action="store_true")
    p.set_defaults(func=lambda a: adapter.main(["--smoke"] if a.smoke else []))

    p = sub.add_parser("check-submission", help="CI rules for a submission PR")
    p.add_argument("--hackathon-dir", type=Path, required=True)
    p.add_argument("--base", default="origin/main")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument("--files", nargs="*", default=None)
    p.set_defaults(func=lambda a: check_submission.main(
        ["--hackathon-dir", str(a.hackathon_dir), "--base", a.base] + (["--repo", str(a.repo)] if a.repo else []) + (["--files", *a.files] if a.files is not None else [])))

    args = parser.parse_args(argv)
    if hasattr(args, "issues_dir") and args.issues_dir is None:
        args.issues_dir = default_issues_dir()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
