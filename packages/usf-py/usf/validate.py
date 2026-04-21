"""Validate a skill against the JSON schema + structural rules."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from .loader import Skill, load
from .parser import REQUIRED_SECTIONS
from .template import find_variables


@dataclass
class ValidationError(Exception):
    skill: str
    errors: list[str]

    def __str__(self) -> str:
        header = f"{self.skill}:"
        return "\n".join([header] + [f"  - {e}" for e in self.errors])


_SCHEMA_CACHE: dict | None = None


def _repo_root() -> Path:
    # packages/usf-py/usf/validate.py -> repo root
    return Path(__file__).resolve().parents[3]


def get_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        schema_path = _repo_root() / "schema" / "skill.schema.json"
        _SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def validate_skill(skill: Skill) -> list[str]:
    """Return a list of error messages. Empty list = valid."""
    errors: list[str] = []

    # 1. JSON schema on frontmatter
    try:
        jsonschema.validate(skill.frontmatter, get_schema())
    except jsonschema.ValidationError as exc:
        errors.append(f"frontmatter: {exc.message} (at {'/'.join(str(p) for p in exc.path)})")

    # 2. Required sections present
    for s in REQUIRED_SECTIONS:
        if s not in skill.sections:
            errors.append(f"missing required section: # {s}")

    # 3. Inputs declared <-> template variables used
    declared = {i.name for i in skill.inputs_spec}
    used: set[str] = set()
    for body in skill.sections.values():
        used |= find_variables(body)
    undeclared = used - declared
    unused = declared - used
    if undeclared:
        errors.append(f"template uses undeclared input(s): {sorted(undeclared)}")
    if unused:
        errors.append(f"inputs declared but never referenced: {sorted(unused)}")

    return errors


def validate_path(path: str | Path) -> dict[str, list[str]]:
    """Validate every .md in a directory (non-recursive). Returns {name: errors}."""
    p = Path(path)
    results: dict[str, list[str]] = {}
    if p.is_file():
        files = [p]
    else:
        files = sorted(p.glob("*.md"))
    for md in files:
        try:
            skill = load(md)
        except UnicodeDecodeError:
            # Not a text file (e.g. a zipped Claude Skill bundle with .md extension) — skip.
            continue
        except Exception as exc:
            results[str(md)] = [f"parse error: {exc}"]
            continue
        if skill.frontmatter.get("usf") is False:
            continue
        # Only USF-shaped files (have name + description) are validated;
        # everything else is considered non-USF and skipped.
        if "name" not in skill.frontmatter or "description" not in skill.frontmatter:
            continue
        errs = validate_skill(skill)
        if errs:
            results[str(md)] = errs
    return results
