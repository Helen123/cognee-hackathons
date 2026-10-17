"""Load and validate an entrant's ``memory.yml``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
import yaml

SCHEMA_FILE = Path(__file__).with_name("memory.schema.json")
RESERVED = {"no_memory", "cognee"}


@dataclass
class Arm:
    name: str
    folder: Path
    manifest: dict = field(default_factory=dict)

    def script(self, key: str) -> Path | None:
        rel = self.manifest.get(key)
        return (self.folder / rel) if rel else None

    @property
    def plugin_dirs(self) -> list[Path]:
        return [self.folder / p for p in self.manifest.get("plugin_dirs", [])]

    @property
    def is_control(self) -> bool:
        return self.name == "no_memory"


def load_schema() -> dict:
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def validate_manifest(data: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in validator.iter_errors(data)]
    for key in ("install", "wipe", "wait"):
        if key in data and not isinstance(data[key], str):
            errors.append(f"{key}: must be a script path")
    if data.get("preindex") and not data.get("preindex_script"):
        errors.append("preindex_script: required when preindex is true")
    return errors


def load_arm(path: Path) -> Arm:
    path = Path(path).resolve()
    if path.is_dir():
        path = path / "memory.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = validate_manifest(data)
    if errors:
        raise ValueError(f"{path}: invalid memory.yml:\n  " + "\n  ".join(errors))
    arm = Arm(name=data["name"], folder=path.parent, manifest=data)
    for key in ("install", "wipe", "wait", "preindex_script", "receipt", "usage", "wipe_check"):
        script = arm.script(key)
        if script is not None and not script.is_file():
            raise ValueError(f"{path}: {key} points to a missing file {script}")
    return arm


def control_arm() -> Arm:
    """The built-in no-memory control: no scripts, no plugins."""
    return Arm(
        name="no_memory",
        folder=Path(__file__).with_name("data"),
        manifest={
            "name": "no_memory",
            "version": "n/a",
            "hooks": ["none"],
            "install": "", "wipe": "", "wait": "",
            "storage": "none", "network": [], "preindex": False,
            "llm": {"provider": "none", "model": "none"},
        },
    )
