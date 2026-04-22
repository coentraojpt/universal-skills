from pathlib import Path

import pytest

from usf.loader import load
from usf.validate import validate_path, validate_skill, get_schema

REPO = Path(__file__).resolve().parents[3]


def test_schema_bundled_with_package():
    """skill.schema.json must be resolvable from the installed package, not the repo root."""
    import usf.validate as _v
    schema_path = Path(_v.__file__).parent / "skill.schema.json"
    assert schema_path.exists(), f"schema not found at {schema_path} — not bundled in wheel"
    schema = get_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema


def test_all_skills_valid():
    results = validate_path(REPO / "skills")
    assert results == {}, results


def test_all_templates_valid():
    # Templates don't declare descriptions constrained by real inputs; they should parse + validate.
    results = validate_path(REPO / "templates")
    assert results == {}, results


def test_undeclared_template_var_rejected(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text(
        "---\nname: bad\ndescription: d\n---\n\n"
        "# Role\nr\n# Task\nuse {{undeclared}}\n# Context\nc\n# Constraints\nk\n# Output Format\no\n",
        encoding="utf-8",
    )
    skill = load(p)
    errs = validate_skill(skill)
    assert any("undeclared" in e for e in errs)


def test_unused_declared_input_rejected(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text(
        "---\nname: bad2\ndescription: d\ninputs:\n  - name: unused\n---\n\n"
        "# Role\nr\n# Task\nt\n# Context\nc\n# Constraints\nk\n# Output Format\no\n",
        encoding="utf-8",
    )
    skill = load(p)
    errs = validate_skill(skill)
    assert any("never referenced" in e for e in errs)


def test_missing_name_rejected(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text(
        "---\ndescription: d\n---\n\n# Role\nr\n# Task\nt\n# Context\nc\n# Constraints\nk\n# Output Format\no\n",
        encoding="utf-8",
    )
    skill = load(p)
    errs = validate_skill(skill)
    assert any("name" in e.lower() for e in errs)
