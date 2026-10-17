"""The Mem Off sequencer: run the chained eight-issue sequence per arm and repeat.

What the stock ``outcomes run`` does for independent cases this does for the chain:

* one workspace per (arm, repeat), cloned from xitkit at the pinned revision;
* the agent session ends after every issue (``claude -p`` exits), the code is
  committed and kept, the entrant's ``wait`` script is awaited;
* one trial record per issue in the evaluator's schema (``trials.jsonl``), so
  ``plugin_eval.py outcomes report --trials`` rebuilds ``report.json``;
* the extra per-issue runner metrics (turns, tokens, injected chars, wait time,
  changed files, verify details) go to ``issues.jsonl`` and ``metrics.json``.

Record semantics that differ from independent trials, on purpose:

* ``session_id`` is the real agent session for that issue (unique).
* ``dataset_name`` in the *record* is the trial's isolation key
  ``memoff-<arm>-r<rep>-issue-NN`` (unique, as the evaluator requires). The memory
  store the entrant's system actually uses is shared across the issues of one
  (arm, repeat) — that is the benchmark — and is reported as ``memoff.memory_store``.
* ``fixture_hash`` is computed from the issue prompt and the *baseline* revision,
  not from each arm's current code, so matched blocks compare the same issue.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

from . import __version__
from .manifest import Arm, control_arm, load_arm
from .paths import load_outcome_eval
from .suite import XITKIT_REPO, XITKIT_REVISION, build_suite, load_issues

SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{12,}|ghp_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{16,})")


@dataclass
class RunConfig:
    issues_dir: Path
    out_dir: Path
    arms: list[Arm]
    model: str
    max_tokens: int = 8192
    repeats: int = 1
    seed: int = 42
    issue_timeout: float = 3600.0
    adapter: list[str] = field(default_factory=lambda: [sys.executable, "-m", "memoff.adapter"])
    xitkit_source: Path | None = None
    python_version: str = "3.14"
    make_venv: bool = True
    smoke: bool = False
    stop_on_fail: bool = False
    only_issues: list[int] | None = None


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    kw.setdefault("check", True)
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    return subprocess.run(cmd, **kw)


def run_script(script: Path | None, env: dict, cwd: Path, timeout: float, log: Path) -> dict:
    """Run an entrant script; never raise, always return a timing/status dict."""
    if script is None:
        return {"ran": False, "ms": 0.0, "returncode": None}
    started = time.monotonic()
    try:
        proc = subprocess.run(["sh", str(script)], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        status = {"ran": True, "returncode": proc.returncode, "timeout": False}
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
        status["stdout"] = proc.stdout[-4000:]
    except subprocess.TimeoutExpired:
        status = {"ran": True, "returncode": None, "timeout": True}
    status["ms"] = (time.monotonic() - started) * 1000
    return status


def ensure_source(cfg: RunConfig) -> tuple[Path, str]:
    if cfg.xitkit_source:
        source = Path(cfg.xitkit_source).resolve()
    else:
        source = cfg.out_dir / "_source"
        if not source.exists():
            sh(["git", "clone", "--quiet", XITKIT_REPO, str(source)])
    revision = sh(["git", "-C", str(source), "rev-parse", "--verify", XITKIT_REVISION + "^{commit}"]).stdout.strip()
    return source, revision


def make_workspace(source: Path, revision: str, workspace: Path, branch: str) -> None:
    workspace.parent.mkdir(parents=True, exist_ok=True)
    sh(["git", "clone", "--quiet", "--no-checkout", "--", str(source), str(workspace)])
    sh(["git", "-C", str(workspace), "checkout", "--quiet", "-B", branch, revision])
    sh(["git", "-C", str(workspace), "config", "user.email", "memoff@localhost"])
    sh(["git", "-C", str(workspace), "config", "user.name", "memoff"])


def make_venv(workspace: Path, python_version: str) -> str:
    sh(["uv", "venv", "-q", "-p", python_version, str(workspace / ".venv")])
    py = str(workspace / ".venv" / "bin" / "python")
    sh(["uv", "pip", "install", "-q", "-p", py, "-e", ".[dev]"], cwd=workspace)
    return py


def reinstall(workspace: Path, py: str) -> None:
    """pyproject may change (issues 6/7); keep the venv consistent before verifying."""
    try:
        sh(["uv", "pip", "install", "-q", "-p", py, "-e", ".[dev]"], cwd=workspace)
    except subprocess.CalledProcessError:
        pass


def changed_files(workspace: Path) -> int:
    out = sh(["git", "-C", str(workspace), "status", "--porcelain"]).stdout
    return len([line for line in out.splitlines() if line.strip() and not line.endswith("/.venv/") and "/.venv" not in line])


def commit_state(workspace: Path, message: str) -> str:
    sh(["git", "-C", str(workspace), "add", "-A", "--", ".", ":!.venv"], check=False)
    sh(["git", "-C", str(workspace), "commit", "-q", "--allow-empty", "-m", message])
    return sh(["git", "-C", str(workspace), "rev-parse", "HEAD"]).stdout.strip()


def redact(text: str) -> str:
    return SECRET_RE.sub("[REDACTED]", text)


def copy_transcript(session_id: str | None, workspace: Path, dest: Path) -> bool:
    if not session_id:
        return False
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return False
    for candidate in projects.glob(f"*/{session_id}.jsonl"):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(redact(candidate.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        return True
    return False


class Sequencer:
    def __init__(self, cfg: RunConfig):
        self.cfg = cfg
        self.oe = load_outcome_eval()
        self.issues = load_issues(cfg.issues_dir)
        if cfg.only_issues:
            self.issues = [i for i in self.issues if i.number in cfg.only_issues]
        names = [a.name for a in cfg.arms]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate arm names: {names}")
        self.variants = names
        self.suite = build_suite(self.issues, model=cfg.model, max_tokens=cfg.max_tokens, variants=self.variants)
        self.cases = {c["id"]: c for c in self.suite["cases"]}
        self.records: list[dict] = []
        self.issue_rows: list[dict] = []

    # ------------------------------------------------------------------ run
    def run(self) -> dict:
        cfg = self.cfg
        cfg.out_dir.mkdir(parents=True, exist_ok=False)
        source, revision = ensure_source(cfg)
        self.revision = revision
        meta = {
            "harness": "memoff " + __version__,
            "schema": self.oe.SCHEMA,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "model": cfg.model,
            "max_tokens": cfg.max_tokens,
            "repeats": cfg.repeats,
            "seed": cfg.seed,
            "arms": {a.name: {"version": a.manifest.get("version"), "folder": str(a.folder)} for a in cfg.arms},
            "xitkit": {"repo": XITKIT_REPO, "revision": revision},
            "issues": [c["id"] for c in self.suite["cases"]],
            "smoke": cfg.smoke,
            "claude_code": self._claude_version(),
            "private_graders": bool(os.environ.get("MEMOFF_PRIVATE_DIR")),
        }
        (cfg.out_dir / "action-run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        (cfg.out_dir / "suite.json").write_text(json.dumps(self.suite, indent=2) + "\n", encoding="utf-8")
        for arm in cfg.arms:
            self._install(arm)
            for rep in range(cfg.repeats):
                self._run_sequence(arm, rep, source)
        meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        report = self._write_reports(meta)
        return report

    def _claude_version(self) -> str | None:
        try:
            return sh([os.environ.get("MEMOFF_CLAUDE_BIN", "claude"), "--version"]).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    def _arm_env(self, arm: Arm, store: str, extra: dict) -> dict:
        env = dict(os.environ)
        env.update(
            MEMOFF_ARM=arm.name,
            MEMOFF_MEMORY_STORE=store,
            COGNEE_PLUGIN_DATASET=store,
            MEMOFF_ISSUES_DIR=str(self.cfg.issues_dir),
            MEMOFF_HARNESS_VERSION=__version__,
        )
        if arm.plugin_dirs:
            env["MEMOFF_PLUGIN_DIRS"] = os.pathsep.join(str(p) for p in arm.plugin_dirs)
        if self.cfg.smoke:
            env["MEMOFF_SMOKE"] = "1"
        env.update(extra)
        return env

    def _install(self, arm: Arm) -> None:
        if arm.is_control or self.cfg.smoke and arm.script("install") is None:
            return
        log = self.cfg.out_dir / arm.name / "install.log"
        status = run_script(arm.script("install"), self._arm_env(arm, "memoff_install", {}), arm.folder, 1800, log)
        if status.get("returncode") not in (None, 0):
            raise RuntimeError(f"{arm.name}: install failed, see {log}")

    def _run_sequence(self, arm: Arm, rep: int, source: Path) -> None:
        cfg = self.cfg
        root = cfg.out_dir / arm.name / f"r{rep}"
        workspace = root / "workspace"
        store = f"memoff_{arm.name}_r{rep}_{uuid.uuid4().hex[:8]}"
        make_workspace(source, self.revision, workspace, f"memoff/{arm.name}/r{rep}")
        py = make_venv(workspace, cfg.python_version) if cfg.make_venv else sys.executable
        base_env = self._arm_env(arm, store, {"MEMOFF_WORKSPACE": str(workspace), "MEMOFF_PYTHON": py})
        wipe = run_script(arm.script("wipe"), base_env, arm.folder, 600, root / "logs" / "wipe.log")
        wipe_check = run_script(arm.script("wipe_check"), base_env, arm.folder, 120, root / "logs" / "wipe_check.log")
        if wipe_check.get("ran") and wipe_check.get("returncode") not in (0,):
            raise RuntimeError(f"{arm.name}: store not empty after wipe")
        preindex = {"ran": False, "ms": 0.0}
        if arm.manifest.get("preindex"):
            preindex = run_script(arm.script("preindex_script"), base_env, workspace, 3600, root / "logs" / "preindex.log")
        (root / "run.json").write_text(
            json.dumps({"arm": arm.name, "repeat": rep, "memory_store": store, "wipe": wipe, "wipe_check": wipe_check, "preindex": preindex}, indent=2),
            encoding="utf-8",
        )
        for case in self.suite["cases"]:
            row = self._run_issue(arm, rep, case, workspace, root, store, base_env, py)
            if not row["outcome"]["task_success"] and cfg.stop_on_fail:
                break
        diff = sh(["git", "-C", str(workspace), "diff", self.revision, "HEAD", "--", ".", ":!.venv"], check=False).stdout
        (root / "final.diff").write_text(redact(diff), encoding="utf-8")

    def _run_issue(self, arm: Arm, rep: int, case: dict, workspace: Path, root: Path, store: str, base_env: dict, py: str) -> dict:
        cfg = self.cfg
        number = case["number"]
        tag = f"issue-{number:02d}"
        trial_id = uuid.uuid4().hex
        session_id = f"memoff_{arm.name}_r{rep}_{tag}_{trial_id[:8]}"
        isolation_key = f"memoff-{arm.name}-r{rep}-{tag}-{trial_id[:8]}"
        seed = cfg.seed + rep
        injected_dir = root / "injected" / tag
        artifact_dir = root / "artifacts" / tag
        injected_dir.mkdir(parents=True, exist_ok=True)
        env = dict(
            base_env,
            MEMOFF_ISSUE=str(number),
            MEMOFF_SESSION_ID=session_id,
            COGNEE_SESSION_ID=session_id,
            MEMOFF_INJECTED_DIR=str(injected_dir),
            MEMOFF_ARTIFACT_DIR=str(artifact_dir),
            MEMOFF_VERIFY_OUT=str(root / "verify" / f"{tag}.json"),
        )
        request = {
            "schema": self.oe.SCHEMA,
            "trial_id": trial_id,
            "variant": arm.name,
            "model": cfg.model,
            "max_tokens": cfg.max_tokens,
            "seed": seed,
            "session_id": session_id,
            "dataset_name": isolation_key,
            "recall_budget_seconds": self.oe.RECALL_BUDGET_SECONDS,
            "workspace": str(workspace),
            "state_dir": str(root / "state" / tag),
            "task": {"id": case["id"], "prompt": case["prompt"]},
            "memory_seed": [],
            "variant_config": {},
            "memoff": {"issue": number, "memory_store": store, "arm": arm.name, "repeat": rep},
        }
        response, status, verify_result = {}, "ok", None
        started = time.monotonic()
        try:
            proc = subprocess.run(cfg.adapter, input=json.dumps(request), capture_output=True, text=True, cwd=workspace, env=env, timeout=cfg.issue_timeout)
            (artifact_dir).mkdir(parents=True, exist_ok=True)
            (artifact_dir / "adapter-stderr.txt").write_text(redact(proc.stderr), encoding="utf-8")
            if proc.returncode:
                raise ValueError("adapter failed")
            response = json.loads(proc.stdout)
            if not isinstance(response, dict):
                response = {}
                raise ValueError("adapter response must be an object")
            if response.get("model") != cfg.model:
                raise ValueError("adapter changed the pinned model")
            if response.get("session_id") != session_id or response.get("dataset_name") != isolation_key:
                raise ValueError("adapter did not echo the trial identity")
            if not self.oe.number(response.get("recall_ms")) or response["recall_ms"] > 45000:
                raise ValueError("recall latency missing or over budget")
            if response.get("retrieved_ids"):
                raise ValueError("retrieved_ids must be empty: Mem Off seeds no memory")
            outcome = self.oe.score(case, response)
            if cfg.make_venv:
                reinstall(workspace, py)
            remaining = max(1.0, cfg.issue_timeout - (time.monotonic() - started))
            check = subprocess.run(case["verify"], cwd=workspace, env=env, capture_output=True, text=True, timeout=remaining)
            outcome["task_success"] &= check.returncode == 0
            verify_path = Path(env["MEMOFF_VERIFY_OUT"])
            verify_result = json.loads(verify_path.read_text()) if verify_path.exists() else {"ok": check.returncode == 0, "tail": check.stderr[-2000:]}
        except subprocess.TimeoutExpired:
            status = "timeout"
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError):
            status = "invalid_or_failed"
        latency_ms = (time.monotonic() - started) * 1000
        if status != "ok":
            outcome = self.oe.score(case, {})
            response["retrieved_ids"] = []
        files_changed = changed_files(workspace)
        commit = commit_state(workspace, f"memoff: {tag} ({arm.name} r{rep}) success={outcome['task_success']}")
        wait = run_script(arm.script("wait"), env, arm.folder, 1800, root / "logs" / f"wait-{tag}.log")
        receipt = run_script(arm.script("receipt"), env, arm.folder, 120, root / "logs" / f"receipt-{tag}.log")
        if receipt.get("ran") and receipt.get("returncode") == 0:
            (root / "receipts").mkdir(parents=True, exist_ok=True)
            (root / "receipts" / f"{tag}.json").write_text(receipt.get("stdout", ""), encoding="utf-8")
        rows = response.get("usage", []) if isinstance(response, dict) else []
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            rows = []
        usage_script = run_script(arm.script("usage"), env, arm.folder, 120, root / "logs" / f"usage-{tag}.log")
        if usage_script.get("ran") and usage_script.get("returncode") == 0:
            try:
                server_rows = json.loads(usage_script.get("stdout") or "[]")
                rows = [r for r in rows if r.get("source") != "server"] + [r for r in server_rows if isinstance(r, dict)]
            except json.JSONDecodeError:
                pass
        try:
            usage = self.oe.usage_totals(rows)
        except (ValueError, TypeError, AttributeError, KeyError):
            usage = self.oe.usage_totals([])
        complete = response.get("usage_complete") is True and "client" in usage["sources"]
        complete &= arm.is_control or "server" in usage["sources"]
        complete &= usage["total_tokens"] is not None and usage["cost_usd"] is not None
        if not complete:
            usage["total_tokens"] = usage["cost_usd"] = None
        agent = (response.get("memoff") or {}).get("agent") or {}
        transcript_copied = copy_transcript(agent.get("session_id"), workspace, root / "transcripts" / f"{tag}.jsonl")
        injected_chars = sum(len(p.read_text(encoding="utf-8", errors="replace")) for p in injected_dir.rglob("*") if p.is_file())
        record = {
            "schema": self.oe.SCHEMA,
            "case_id": case["id"],
            "repetition": rep,
            "variant": arm.name,
            "variants": self.variants,
            "model": cfg.model,
            "seed": seed,
            "max_tokens": cfg.max_tokens,
            "session_id": session_id,
            "dataset_name": isolation_key,
            "fixture_hash": self.oe.digest({"prompt": case["prompt"], "files": {}, "repository_revision": self.revision}),
            "memory_hash": self.oe.digest([]),
            "recall_budget_seconds": self.oe.RECALL_BUDGET_SECONDS,
            "status": status,
            "outcome": outcome,
            "latency_ms": latency_ms,
            "recall_ms": response.get("recall_ms") if self.oe.number(response.get("recall_ms")) else None,
            "retrieved_items": 0,
            "usage": usage,
            "usage_complete": bool(complete),
            "memoff": {"issue": number, "memory_store": store, "chained": True},
        }
        self.records.append(record)
        with (cfg.out_dir / "trials.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, allow_nan=False) + "\n")
        row = {
            "arm": arm.name,
            "repeat": rep,
            "issue": number,
            "case_id": case["id"],
            "status": status,
            "task_success": outcome["task_success"],
            "verify": verify_result,
            "turns": agent.get("turns"),
            "input_tokens": agent.get("input_tokens"),
            "output_tokens": agent.get("output_tokens"),
            "cache_read_input_tokens": agent.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": agent.get("cache_creation_input_tokens"),
            "agent_cost_usd": agent.get("total_cost_usd"),
            "memory_cost_usd": usage["measured_cost_usd"] - (agent.get("total_cost_usd") or 0) if usage.get("measured_cost_usd") is not None else None,
            "total_cost_usd": usage["cost_usd"],
            "total_tokens": usage["total_tokens"],
            "agent_duration_ms": agent.get("duration_ms"),
            "elapsed_ms": latency_ms,
            "wait_ms": wait.get("ms"),
            "injected_chars": injected_chars,
            "changed_files": files_changed,
            "commit": commit,
            "transcript": transcript_copied,
            "receipt": bool(receipt.get("ran") and receipt.get("returncode") == 0),
            "outcome": outcome,
        }
        self.issue_rows.append(row)
        with (cfg.out_dir / "issues.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, allow_nan=False) + "\n")
        return row

    # -------------------------------------------------------------- reports
    def _write_reports(self, meta: dict) -> dict:
        out = self.cfg.out_dir
        metrics = build_metrics(self.issue_rows, self.variants, meta)
        (out / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        report = None
        if {"no_memory", "cognee"} <= set(self.variants):
            try:
                report = self.oe.summarize(self.records)
                (out / "outcomes").mkdir(exist_ok=True)
                shutil.copy(out / "trials.jsonl", out / "outcomes" / "trials.jsonl")
                (out / "outcomes" / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            except ValueError as exc:
                meta["report_error"] = str(exc)
        else:
            meta["report_skipped"] = "outcomes report needs both no_memory and cognee arms in one run"
        (out / "leaderboard.md").write_text(render_leaderboard(metrics), encoding="utf-8")
        (out / "action-run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        return {"metrics": metrics, "report": report, "meta": meta}


# ---------------------------------------------------------------- metrics
NUMERIC = ("turns", "input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
           "agent_cost_usd", "memory_cost_usd", "total_cost_usd", "total_tokens", "agent_duration_ms", "elapsed_ms",
           "wait_ms", "injected_chars", "changed_files")


def _agg(values: list) -> dict | None:
    nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not nums:
        return None
    return {"median": median(nums), "min": min(nums), "max": max(nums), "n": len(nums)}


def build_metrics(rows: list[dict], variants: list[str], meta: dict) -> dict:
    per_arm = {}
    for arm in variants:
        arm_rows = [r for r in rows if r["arm"] == arm]
        issues = {}
        for issue in sorted({r["issue"] for r in arm_rows}):
            irows = [r for r in arm_rows if r["issue"] == issue]
            issues[f"issue-{issue:02d}"] = {
                "repeats": len(irows),
                "pass_rate": sum(r["task_success"] for r in irows) / len(irows),
                **{k: _agg([r[k] for r in irows]) for k in NUMERIC},
            }
        reps = sorted({r["repeat"] for r in arm_rows})
        cumulative = {k: _agg([sum((r[k] or 0) for r in arm_rows if r["repeat"] == rep) for rep in reps]) for k in NUMERIC}
        all_pass = bool(arm_rows) and all(r["task_success"] for r in arm_rows)
        per_arm[arm] = {"all_pass": all_pass, "issues": issues, "cumulative": cumulative,
                        "linked_issues_cost": _agg([sum((r["total_cost_usd"] or 0) for r in arm_rows if r["repeat"] == rep and r["issue"] in (4, 5, 7, 8)) for rep in reps])}
    control = per_arm.get("no_memory", {}).get("cumulative", {})
    for arm, data in per_arm.items():
        rel = {}
        for k in ("total_cost_usd", "turns", "total_tokens"):
            c = (control.get(k) or {}).get("median")
            a = (data["cumulative"].get(k) or {}).get("median")
            rel[k] = (a / c) if c and a is not None else None
        data["relative_to_control"] = rel
    return {"kind": "memoff_metrics", "model": meta.get("model"), "xitkit": meta.get("xitkit"), "arms": per_arm,
            "note": "Medians over repeats; cost is the agent's plus the memory system's reported spend; null means unmeasured, never zero."}


def render_leaderboard(metrics: dict) -> str:
    lines = ["# Mem Off leaderboard (this run)", "", "Correctness is a gate: arms that fail any issue are listed but not ranked.", "",
             "| arm | all pass | total cost (median) | vs control | turns (median) | linked issues 4/5/7/8 cost |", "|---|---|---|---|---|---|"]
    ranked = sorted(metrics["arms"].items(), key=lambda kv: (not kv[1]["all_pass"], (kv[1]["cumulative"].get("total_cost_usd") or {}).get("median") or float("inf")))
    for arm, d in ranked:
        cost = (d["cumulative"].get("total_cost_usd") or {}).get("median")
        turns = (d["cumulative"].get("turns") or {}).get("median")
        rel = d["relative_to_control"].get("total_cost_usd")
        linked = (d.get("linked_issues_cost") or {}).get("median")
        fmt = lambda v, p="": ("unmeasured" if v is None else f"{v:.3f}{p}")
        lines.append(f"| {arm} | {'yes' if d['all_pass'] else 'no'} | {fmt(cost)} | {fmt(rel, 'x')} | {fmt(turns)} | {fmt(linked)} |")
    return "\n".join(lines) + "\n"


def arms_from_paths(paths: list[str], include_control: bool) -> list[Arm]:
    arms = [control_arm()] if include_control else []
    arms += [load_arm(Path(p)) for p in paths]
    return arms
