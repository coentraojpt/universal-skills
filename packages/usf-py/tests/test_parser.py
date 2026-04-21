from usf.parser import parse, missing_required_sections


SAMPLE = """---
name: demo
description: demo skill
---

# Role
You are X.

# Task
Do Y with {{arg}}.

# Context
Context here.

# Constraints
- c1

# Output Format
format here
"""


def test_parse_frontmatter_and_sections():
    p = parse(SAMPLE)
    assert p.frontmatter["name"] == "demo"
    assert p.frontmatter["description"] == "demo skill"
    assert set(p.sections.keys()) == {"Role", "Task", "Context", "Constraints", "Output Format"}
    assert p.sections["Role"].strip() == "You are X."
    assert "{{arg}}" in p.sections["Task"]


def test_missing_required_sections():
    p = parse("---\nname: x\ndescription: y\n---\n\n# Role\nfoo\n")
    missing = missing_required_sections(p.sections)
    assert "Task" in missing and "Context" in missing


def test_empty_frontmatter():
    p = parse("# Role\nx\n")
    assert p.frontmatter == {}
    assert "Role" in p.sections


def test_invalid_yaml_raises():
    import pytest
    with pytest.raises(ValueError):
        parse("---\nname: [unclosed\n---\n# Role\nx\n")
