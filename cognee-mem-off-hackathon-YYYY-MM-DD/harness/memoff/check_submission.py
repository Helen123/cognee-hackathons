"""CI check for a submission pull request.

Rules (README §Submissions):
  * every changed file lives under ``<hackathon>/submissions/<team-slug>/``, one slug per PR;
  * ``SUBMISSION.md`` exists and every required heading is filled (no empty "- key:" lines
    left from the template under required headings);
  * Track 1: ``memory.yml`` validates and ``install``/``wipe``/``wait`` scripts exist;
  * Track 2: each ``issues/*/ISSUE_PROPOSAL.md`` has the seven sections and names a
    dependency on an existing issue number;
  * no secrets, no ``.env*``, no OS junk, no binaries over 1 MB;
  * ``results/`` is written by the Action only: a PR that touches it by hand is flagged,
    and a present ``results/`` must be complete (metrics + outcomes + receipts) and not
    produced by the smoke adapter;
  * ``report/memoff-report.md`` and ``report/memoff-report.json`` (from the
    ``memoff-memory-report`` skill) are required for Track 1 and must contain only tool
    output: the JSON must parse and carry ``type: memoff-memory-report``.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from .manifest import validate_manifest

REQUIRED_SUBMISSION_HEADINGS = ["## Team", "## Track", "## What you entered", "## Memory report", "## Reproduction", "## Links"]
REPORT_FILES = ("report/memoff-report.md", "report/memoff-report.json")
PROPOSAL_SECTIONS = [
    "## Issue text",
    "## Memory hypothesis",
    "## Type",
    "## Expected failure count",
    "## Private grader sketch",
    "## Evidence it is solvable",
    "## Pilot",
]
JUNK = {".DS_Store", "Thumbs.db", "desktop.ini"}
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
MAX_BINARY = 1_000_000


def changed_files(base: str, repo: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, check=True).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def check(hackathon_dir: Path, files: list[str], repo: Path) -> list[str]:
    errors: list[str] = []
    hack = hackathon_dir.name
    prefix = f"{hack}/submissions/"
    slugs = set()
    for f in files:
        if not f.startswith(prefix):
            errors.append(f"{f}: outside {prefix}<team-slug>/ — a submission PR touches only its own folder")
            continue
        rest = f[len(prefix):]
        slug = rest.split("/", 1)[0]
        slugs.add(slug)
        if not SLUG_RE.match(slug):
            errors.append(f"{f}: team slug '{slug}' must be lowercase letters, digits and dashes")
        name = Path(f).name
        if name in JUNK:
            errors.append(f"{f}: remove OS junk files")
        if name.startswith(".env"):
            errors.append(f"{f}: never commit .env files (not even .env.example)")
        path = repo / f
        if path.is_file():
            if path.stat().st_size > MAX_BINARY:
                errors.append(f"{f}: larger than 1 MB")
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = ""
            if SECRET_RE.search(text):
                errors.append(f"{f}: looks like it contains a secret")
        if rest.split("/")[1:2] == ["results"]:
            errors.append(f"{f}: results/ is written by the Action, not by hand")
    if len(slugs) > 1:
        errors.append(f"one team folder per PR, found {sorted(slugs)}")
    for slug in slugs:
        errors += check_folder(hackathon_dir / "submissions" / slug, hackathon_dir)
    return errors


def check_report(folder: Path) -> list[str]:
    """The memoff-memory-report skill's two files: required for Track 1, submitted with results."""
    errors = []
    for rel in REPORT_FILES:
        if not (folder / rel).is_file():
            errors.append(f"{folder.name}/{rel}: missing — run the memoff-memory-report skill's wrap-up (it copies both files here)")
    md = folder / REPORT_FILES[0]
    if md.is_file():
        text = md.read_text(encoding="utf-8")
        if "type: memoff-memory-report" not in text:
            errors.append(f"{folder.name}/{REPORT_FILES[0]}: not a memoff-memory-report file (front matter missing)")
        if SECRET_RE.search(text):
            errors.append(f"{folder.name}/{REPORT_FILES[0]}: looks like it contains a secret")
    js = folder / REPORT_FILES[1]
    if js.is_file():
        try:
            data = json.loads(js.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("type") != "memoff-memory-report":
                errors.append(f"{folder.name}/{REPORT_FILES[1]}: JSON must carry type = memoff-memory-report")
        except json.JSONDecodeError as exc:
            errors.append(f"{folder.name}/{REPORT_FILES[1]}: invalid JSON ({exc})")
    return errors


def check_folder(folder: Path, hackathon_dir: Path) -> list[str]:
    errors = []
    sub = folder / "SUBMISSION.md"
    if not sub.is_file():
        return [f"{folder.name}: SUBMISSION.md missing (copy templates/SUBMISSION.md)"]
    text = sub.read_text(encoding="utf-8")
    for heading in REQUIRED_SUBMISSION_HEADINGS:
        if heading not in text:
            errors.append(f"{folder.name}/SUBMISSION.md: missing heading '{heading}'")
    track1 = (folder / "memory.yml").exists()
    track2 = (folder / "issues").is_dir()
    if not track1 and not track2:
        errors.append(f"{folder.name}: neither memory.yml (Track 1) nor issues/ (Track 2) present")
    if track1:
        try:
            data = yaml.safe_load((folder / "memory.yml").read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            data, errors = {}, errors + [f"{folder.name}/memory.yml: not valid YAML ({exc})"]
        for err in validate_manifest(data) if data else []:
            errors.append(f"{folder.name}/memory.yml: {err}")
        if data.get("name") in {"no_memory"}:
            errors.append(f"{folder.name}/memory.yml: 'no_memory' is the control arm; pick another name")
        for key in ("install", "wipe", "wait", "preindex_script", "receipt", "usage", "wipe_check"):
            rel = data.get(key)
            if rel and not (folder / rel).is_file():
                errors.append(f"{folder.name}/memory.yml: {key} -> {rel} missing")
        errors += check_report(folder)
    if track2:
        known = {int(p.name[:2]) for p in (hackathon_dir / "challenge" / "issues").glob("[0-9][0-9]-*.md")}
        proposals = list((folder / "issues").glob("*/ISSUE_PROPOSAL.md"))
        if not proposals:
            errors.append(f"{folder.name}/issues: no ISSUE_PROPOSAL.md found")
        for prop in proposals:
            ptext = prop.read_text(encoding="utf-8")
            for section in PROPOSAL_SECTIONS:
                if section not in ptext:
                    errors.append(f"{prop.relative_to(folder)}: missing section '{section}'")
            deps = re.findall(r"Depends on:\s*Issue (\d+)", ptext)
            if not deps:
                errors.append(f"{prop.relative_to(folder)}: state 'Depends on: Issue N' in the issue text")
            elif any(int(d) not in known for d in deps):
                errors.append(f"{prop.relative_to(folder)}: dependency must be an existing issue {sorted(known)}")
    results = folder / "results"
    if results.is_dir():
        for required in ("metrics.json", "action-run.json", "outcomes/report.json", "outcomes/trials.jsonl"):
            if not (results / required).is_file():
                errors.append(f"{folder.name}/results: incomplete, {required} missing")
        if not any((results / "receipts").glob("*.json")) if (results / "receipts").is_dir() else True:
            errors.append(f"{folder.name}/results: receipts/ missing or empty")
        trials = results / "outcomes" / "trials.jsonl"
        if trials.is_file() and "no_model_smoke" in trials.read_text(encoding="utf-8"):
            errors.append(f"{folder.name}/results: produced by the smoke adapter, not evidence")
    return errors


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hackathon-dir", type=Path, required=True)
    parser.add_argument("--base", default="origin/main", help="git ref to diff against")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--files", nargs="*", help="override the changed-file list (tests)")
    args = parser.parse_args(argv)
    repo = (args.repo or args.hackathon_dir.parent).resolve()
    files = args.files if args.files is not None else changed_files(args.base, repo)
    errors = check(args.hackathon_dir.resolve(), files, repo)
    print(json.dumps({"files": files, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
