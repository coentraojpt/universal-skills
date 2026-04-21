from pathlib import Path

from usf.loader import load, load_dir

REPO = Path(__file__).resolve().parents[3]


def test_load_code_reviewer():
    skill = load(REPO / "skills" / "code-reviewer.md")
    assert skill.name == "code-reviewer"
    assert skill.frontmatter["recommended_temperature"] == 0.1
    assert {"Role", "Task", "Context", "Constraints", "Output Format"} <= set(skill.sections.keys())
    assert any(i.name == "code" and i.required for i in skill.inputs_spec)


def test_load_dir_skips_memory_notes_with_usf_false():
    skills = load_dir(REPO / "skills" / "_memory")
    assert skills == []  # both have usf: false


def test_load_dir_main_catalog_has_nine():
    skills = load_dir(REPO / "skills")
    names = {s.name for s in skills}
    expected = {
        "code-reviewer", "api-designer", "debug-assistant", "technical-writer",
        "startup-validator", "commit-message-writer", "sql-optimizer",
        "security-auditor", "refactorer",
    }
    assert expected <= names
