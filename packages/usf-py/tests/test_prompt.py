from textwrap import dedent

import pytest

from usf.loader import Skill, InputSpec
from usf.parser import parse
from usf.prompt import build_prompt


def _skill_from(text: str) -> Skill:
    p = parse(text)
    inputs_spec = [
        InputSpec(
            name=i["name"],
            type=i.get("type", "string"),
            required=i.get("required", False),
            default=i.get("default"),
        )
        for i in p.frontmatter.get("inputs", []) or []
    ]
    return Skill(frontmatter=p.frontmatter, sections=p.sections, inputs_spec=inputs_spec)


BASE = dedent(
    """\
    ---
    name: t
    description: t
    inputs:
      - name: code
        required: true
      - name: lang
        required: false
        default: python
    ---

    # Role
    R

    # Task
    Review {{lang}} code: {{code}}

    # Context
    C

    # Constraints
    K

    # Output Format
    O
    """
)


def test_system_user_split():
    skill = _skill_from(BASE)
    cp = skill.build_prompt({"code": "x = 1"})
    assert "R" in cp.system and "C" in cp.system and "K" in cp.system
    assert "Review python code: x = 1" in cp.user


def test_default_applied():
    skill = _skill_from(BASE)
    cp = skill.build_prompt({"code": "x"})
    assert "python" in cp.user


def test_missing_required_raises():
    skill = _skill_from(BASE)
    with pytest.raises(ValueError, match="Missing required"):
        skill.build_prompt({})


def test_deterministic_output():
    skill = _skill_from(BASE)
    cp1 = skill.build_prompt({"code": "x", "lang": "js"})
    cp2 = skill.build_prompt({"code": "x", "lang": "js"})
    assert cp1.system == cp2.system
    assert cp1.user == cp2.user
