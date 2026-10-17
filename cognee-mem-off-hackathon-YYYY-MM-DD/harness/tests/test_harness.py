import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from memoff import adapter, check_submission, suite, verify
from memoff.manifest import load_arm, validate_manifest

HERE = Path(__file__).resolve().parent
HACK = HERE.parent.parent
ISSUES = HACK / "challenge" / "issues"


def test_issues_load_in_order_with_targets():
    issues = suite.load_issues(ISSUES)
    assert [i.number for i in issues] == list(range(1, 9))
    assert [i.failures_after for i in issues] == [6, 5, 4, 0, 0, 0, 0, 0]
    assert issues[7].depends_on.startswith("Issue 7")


def test_suite_shape():
    s = suite.build_suite(suite.load_issues(ISSUES), model="m", max_tokens=10, variants=["no_memory", "cognee"])
    assert len(s["cases"]) == 8 and s["cases"][0]["id"] == "issue-01"
    assert s["cases"][2]["verify"][-2:] == ["--issue", "3"]
    assert s["cases"][0]["expected"]["status"]["value"] == "implemented"


@pytest.mark.parametrize(
    "line,failed,passed",
    [("11 failed, 769 passed, 1 warning in 3.62s", 11, 769), ("769 passed in 3s", 0, 769), ("2 failed, 1 error, 10 passed", 3, 10)],
)
def test_parse_pytest_summary(line, failed, passed):
    assert verify.parse_pytest_summary("noise\n" + line) == {"failed": failed, "passed": passed}


def test_smoke_adapter_response_conforms(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOFF_SMOKE", "1")
    inj = tmp_path / "inj"
    inj.mkdir()
    (inj / "a.txt").write_text("hello")
    monkeypatch.setenv("MEMOFF_INJECTED_DIR", str(inj))
    req = {"trial_id": "t", "variant": "cognee", "model": "m", "session_id": "s", "dataset_name": "d", "task": {"id": "x", "prompt": "p"}}
    resp = adapter.run(req)
    assert resp["model"] == "m" and resp["session_id"] == "s" and resp["dataset_name"] == "d"
    assert resp["claims"] == [{"id": "status", "value": "not_implemented", "citations": []}]
    assert resp["retrieved_ids"] == [] and resp["recall_ms"] == 0.0
    assert {r["source"] for r in resp["usage"]} == {"client", "server"}
    assert resp["memoff"]["injected_chars"] == 5


def test_status_claim_parsing():
    assert adapter.status_claim("blah\nSTATUS: implemented\nmore") == "implemented"
    assert adapter.status_claim("STATUS: not_implemented") == "not_implemented"
    assert adapter.status_claim("no status line") == "not_implemented"


def test_build_command_has_pins(monkeypatch):
    monkeypatch.setenv("MEMOFF_PLUGIN_DIRS", "/a" + os.pathsep + "/b")
    cmd = adapter.build_command({"model": "claude-x"}, "prompt")
    assert cmd[:3] == ["claude", "-p", "prompt"]
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "claude-x"
    assert cmd.count("--plugin-dir") == 2 and "--dangerously-skip-permissions" in cmd


def test_manifest_fixture_valid_and_control_reserved():
    arm = load_arm(HERE / "fixtures" / "arm-noop")
    assert arm.name == "cognee" and arm.script("wait").is_file()
    errors = validate_manifest({"name": "x"})
    assert any("required" in e for e in errors)


def test_shipped_arm_manifests_validate():
    import yaml

    for folder in (HACK / "harness" / "arms").iterdir():
        data = yaml.safe_load((folder / "memory.yml").read_text())
        assert validate_manifest(data) == [], folder
        for key in ("install", "wipe", "wait"):
            assert (folder / data[key]).is_file(), (folder, key)


def test_check_submission_rules(tmp_path):
    repo = tmp_path
    hack = repo / "hack"
    (hack / "challenge" / "issues").mkdir(parents=True)
    (hack / "challenge" / "issues" / "01-a.md").write_text("# Issue 1 — a")
    team = hack / "submissions" / "team-a"
    team.mkdir(parents=True)
    (team / "SUBMISSION.md").write_text("## Team\n## Track\n## What you entered\n## Reproduction\n## Links\n")
    (team / "issues" / "09-x").mkdir(parents=True)
    (team / "issues" / "09-x" / "ISSUE_PROPOSAL.md").write_text(
        "\n".join(check_submission.PROPOSAL_SECTIONS) + "\nDepends on: Issue 1\n"
    )
    files = ["hack/submissions/team-a/SUBMISSION.md", "hack/submissions/team-a/issues/09-x/ISSUE_PROPOSAL.md"]
    assert check_submission.check(hack, files, repo) == []
    bad = files + ["hack/templates/SUBMISSION.md", "hack/submissions/team-a/.env.example", "hack/submissions/team-a/results/metrics.json"]
    errors = check_submission.check(hack, bad, repo)
    assert any("outside" in e for e in errors)
    assert any(".env" in e for e in errors)
    assert any("results/ is written by the Action" in e for e in errors)
    (team / "issues" / "09-x" / "ISSUE_PROPOSAL.md").write_text("## Issue text\nDepends on: Issue 7\n")
    errors = check_submission.check(hack, files, repo)
    assert any("missing section" in e for e in errors) and any("existing issue" in e for e in errors)


def test_verify_module_entrypoint_runs_from_workspace(tmp_path, monkeypatch):
    """A workspace with a one-test suite: target mismatch → exit 1, JSON written."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "tests" / "test_x.py").write_text("def test_ok():\n    assert True\n")
    monkeypatch.setenv("MEMOFF_ISSUES_DIR", str(ISSUES))
    monkeypatch.setenv("MEMOFF_PYTHON", sys.executable)
    monkeypatch.setenv("MEMOFF_VERIFY_OUT", str(tmp_path / "v.json"))
    monkeypatch.delenv("MEMOFF_PRIVATE_DIR", raising=False)
    rc = subprocess.call([sys.executable, "-m", "memoff.verify", "--issue", "1"], cwd=ws, env=os.environ)
    data = json.loads((tmp_path / "v.json").read_text())
    assert rc == 1 and data["visible"]["failed"] == 0 and data["visible"]["target_failures"] == 6
    assert data["private"]["reason"].startswith("MEMOFF_PRIVATE_DIR unset")
