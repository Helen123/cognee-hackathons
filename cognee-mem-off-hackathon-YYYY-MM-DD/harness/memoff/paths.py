"""Locate the cognee-report skill scripts and import its evaluator."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

SKILL_REL = Path("skills") / "cognee-report" / "scripts"


def candidate_dirs() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("MEMOFF_COGNEE_REPORT_DIR")
    if env:
        out.append(Path(env))
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        out.append(Path(root) / SKILL_REL)
    plugins = Path.home() / ".claude" / "plugins"
    if plugins.is_dir():
        out.extend(sorted(plugins.glob("**/" + SKILL_REL.as_posix()), reverse=True))
    out.append(
        Path.home()
        / "Projects"
        / "cognee-integrations"
        / "integrations"
        / "claude-code"
        / SKILL_REL
    )
    return out


def find_cognee_report_scripts() -> Path:
    for d in candidate_dirs():
        if (d / "outcome_eval.py").is_file():
            return d
    raise FileNotFoundError(
        "cognee-report skill not found. Install the cognee plugin "
        "(`claude plugin marketplace add topoteretes/cognee-integrations && "
        "claude plugin install cognee-memory@cognee`) or set MEMOFF_COGNEE_REPORT_DIR "
        "to its skills/cognee-report/scripts directory."
    )


def load_outcome_eval():
    """Import the skill's ``outcome_eval`` module (scoring, summarising, schema)."""
    scripts = find_cognee_report_scripts()
    spec = importlib.util.spec_from_file_location("outcome_eval", scripts / "outcome_eval.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("outcome_eval", module)
    spec.loader.exec_module(module)
    return module


def plugin_eval_script() -> Path:
    return find_cognee_report_scripts() / "plugin_eval.py"
