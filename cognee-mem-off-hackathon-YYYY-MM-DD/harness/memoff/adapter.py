"""Agent adapter: one outcomes-protocol request on stdin → Claude Code run → one response on stdout.

Protocol (schema 1, from the cognee-report skill's ``outcome_eval.run_trials``): the request
carries ``trial_id``, ``variant``, ``model``, ``max_tokens``, ``seed``, ``session_id``,
``dataset_name``, ``workspace``, ``state_dir``, ``task{id,prompt}``, ``memory_seed`` and
``variant_config``. The response must echo ``model``, ``session_id`` and ``dataset_name``,
give ``claims``, ``retrieved_ids`` (subset of the seeded memory ids; empty for Mem Off, whose
memory is built by the entrant's system, not seeded), ``recall_ms``, ``usage`` records and
``usage_complete``.

Mem Off extensions are read from the environment, so the same adapter works under the stock
``outcomes run`` (single-issue pilots) and under ``memoff run`` (the chained sequence):

  MEMOFF_CLAUDE_BIN          claude executable (default ``claude``)
  MEMOFF_MAX_TURNS           per-issue turn cap (default 60)
  MEMOFF_MAX_BUDGET_USD      per-issue dollar cap (default 5)
  MEMOFF_SYSTEM_PROMPT_FILE  appended system prompt (default: packaged ``data/system_prompt.md``)
  MEMOFF_PLUGIN_DIRS         os.pathsep-separated plugin directories to load (entrant systems)
  MEMOFF_SETTING_SOURCES     ``--setting-sources`` value (default ``user,project``)
  MEMOFF_PERMISSION_MODE     default ``bypassPermissions``
  MEMOFF_EXTRA_ARGS          JSON argv array appended to the claude command
  MEMOFF_INJECTED_DIR        where the entrant's hooks write injected context (counted, not created)
  MEMOFF_ARTIFACT_DIR        where to copy claude's raw result JSON and metrics for this call
  MEMOFF_SMOKE=1             do not run a model: write nothing, claim ``not_implemented``

``--smoke`` on the command line is the same as MEMOFF_SMOKE=1.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .claude_result import agent_metrics, parse_result, usage_record

SYSTEM_PROMPT_FILE = Path(__file__).with_name("data") / "system_prompt.md"


def injected_chars(injected_dir: str | None) -> int | None:
    if not injected_dir:
        return None
    root = Path(injected_dir)
    if not root.is_dir():
        return 0
    return sum(len(p.read_text(encoding="utf-8", errors="replace")) for p in root.rglob("*") if p.is_file())


def smoke_response(request: dict) -> dict:
    return {
        "model": request["model"],
        "session_id": request["session_id"],
        "dataset_name": request["dataset_name"],
        "claims": [{"id": "status", "value": "not_implemented", "citations": []}],
        "retrieved_ids": [],
        "recall_ms": 0.0,
        "usage": [
            {
                "id": "answer",
                "source": "client",
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0,
                "token_basis": "no_model_smoke",
                "cost_basis": "no_model_smoke",
            }
        ]
        + (
            []
            if request["variant"] == "no_memory"
            else [
                {
                    "id": "memory-system",
                    "source": "server",
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0,
                    "token_basis": "no_model_smoke",
                    "cost_basis": "no_model_smoke",
                }
            ]
        ),
        "usage_complete": True,
        "memoff": {"smoke": True, "agent": None, "injected_chars": injected_chars(os.environ.get("MEMOFF_INJECTED_DIR"))},
    }


def build_command(request: dict, prompt: str) -> list[str]:
    env = os.environ
    cmd = [
        env.get("MEMOFF_CLAUDE_BIN", "claude"),
        "-p",
        prompt,
        "--model",
        request["model"],
        "--output-format",
        "json",
        "--permission-mode",
        env.get("MEMOFF_PERMISSION_MODE", "bypassPermissions"),
        "--max-turns",
        env.get("MEMOFF_MAX_TURNS", "60"),
        "--max-budget-usd",
        env.get("MEMOFF_MAX_BUDGET_USD", "5"),
        "--setting-sources",
        env.get("MEMOFF_SETTING_SOURCES", "user,project"),
        "--append-system-prompt-file",
        env.get("MEMOFF_SYSTEM_PROMPT_FILE", str(SYSTEM_PROMPT_FILE)),
    ]
    if env.get("MEMOFF_PERMISSION_MODE", "bypassPermissions") == "bypassPermissions":
        cmd.append("--dangerously-skip-permissions")
    for plugin_dir in filter(None, env.get("MEMOFF_PLUGIN_DIRS", "").split(os.pathsep)):
        cmd += ["--plugin-dir", plugin_dir]
    extra = env.get("MEMOFF_EXTRA_ARGS")
    if extra:
        cmd += json.loads(extra)
    return cmd


def status_claim(result_text: str) -> str:
    for line in result_text.splitlines():
        if line.strip().upper().startswith("STATUS:"):
            value = line.split(":", 1)[1].strip().lower()
            return "implemented" if value.startswith("implemented") else "not_implemented"
    return "not_implemented"


def run(request: dict) -> dict:
    if os.environ.get("MEMOFF_SMOKE") == "1":
        return smoke_response(request)
    workspace = Path(request["workspace"])
    state_dir = Path(request["state_dir"])
    state_dir.mkdir(parents=True, exist_ok=True)
    prompt = request["task"]["prompt"]
    cmd = build_command(request, prompt)
    env = dict(
        os.environ,
        CLAUDE_CODE_MEMOFF_TRIAL=request["trial_id"],
        MEMOFF_STATE_DIR=str(state_dir),
        MEMOFF_WORKSPACE=str(workspace),
    )
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, env=env)
    elapsed_ms = (time.monotonic() - started) * 1000
    if proc.returncode and not proc.stdout.strip():
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr[-2000:]}")
    result = parse_result(proc.stdout)
    metrics = agent_metrics(result)
    metrics["wall_ms"] = elapsed_ms
    metrics["injected_chars"] = injected_chars(os.environ.get("MEMOFF_INJECTED_DIR"))
    artifact_dir = os.environ.get("MEMOFF_ARTIFACT_DIR")
    if artifact_dir:
        out = Path(artifact_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "claude-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (out / "claude-stderr.txt").write_text(proc.stderr, encoding="utf-8")
        (out / "agent-metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    client = usage_record(result, request["model"], "agent:" + request["trial_id"])
    usage = [client]
    if request["variant"] != "no_memory":
        # The entrant's own model spend is reported by the sequencer from memory.yml's
        # usage hook; here we only reserve the server slot so totals are "unknown", not zero.
        usage.append({"id": "memory-system:" + request["trial_id"], "source": "server"})
    return {
        "model": request["model"],
        "session_id": request["session_id"],
        "dataset_name": request["dataset_name"],
        "claims": [{"id": "status", "value": status_claim(str(result.get("result", ""))), "citations": []}],
        "retrieved_ids": [],
        # Recall latency for a hook-based system is the SessionStart hook's time; the
        # sequencer overwrites this from the entrant's receipt when one is provided.
        "recall_ms": 0.0,
        "usage": usage,
        "usage_complete": request["variant"] == "no_memory" and client["cost_usd"] is not None,
        "memoff": {"smoke": False, "agent": metrics},
    }


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--smoke" in argv:
        os.environ["MEMOFF_SMOKE"] = "1"
    request = json.load(sys.stdin)
    response = run(request)
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
