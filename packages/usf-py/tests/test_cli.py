from pathlib import Path

from click.testing import CliRunner

from usf.cli import main

REPO = Path(__file__).resolve().parents[3]


def test_validate_all_skills_green():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(REPO / "skills")])
    assert result.exit_code == 0, result.output


def test_list_shows_skills():
    runner = CliRunner()
    result = runner.invoke(main, ["list", str(REPO / "skills")])
    assert result.exit_code == 0
    assert "code-reviewer" in result.output
    assert "refactorer" in result.output


def test_render_dryrun_openai():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["render", "code-reviewer", "--provider", "openai",
         "--input", "code=print(1)", "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0
    assert '"model"' in result.output
    assert "print(1)" in result.output


def test_run_dryrun_anthropic():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["run", "code-reviewer", "--provider", "anthropic", "--dry-run",
         "--input", "code=print(1)", "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0
    assert '"system"' in result.output


def test_missing_required_input_errors():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["render", "code-reviewer", "--provider", "openai", "--path", str(REPO / "skills")],
    )
    assert result.exit_code != 0


def test_export_claude_format(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--format", "claude",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0
    skill_md = tmp_path / "code-reviewer" / "SKILL.md"
    assert skill_md.exists()
    content = skill_md.read_text(encoding="utf-8")
    assert "name: " in content
    assert "description: " in content
    assert "# Role" in content


def test_export_cursor_format(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--format", "cursor",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0, result.output
    mdc = tmp_path / ".cursor" / "rules" / "code-reviewer.mdc"
    assert mdc.exists()
    content = mdc.read_text(encoding="utf-8")
    assert "description:" in content
    assert "alwaysApply: false" in content
    assert "# Role" in content


def test_export_vscode_format(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--format", "vscode",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0, result.output
    inst = tmp_path / ".github" / "instructions" / "code-reviewer.instructions.md"
    assert inst.exists()
    content = inst.read_text(encoding="utf-8")
    assert "name:" in content
    assert "applyTo:" in content
    assert "# Role" in content


def test_export_opencode_format(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--format", "opencode",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0, result.output
    md = tmp_path / ".opencode" / "code-reviewer.md"
    assert md.exists()
    assert "# Role" in md.read_text(encoding="utf-8")
    config = tmp_path / "opencode.json"
    assert config.exists()
    data = __import__("json").loads(config.read_text(encoding="utf-8"))
    assert ".opencode/code-reviewer.md" in data["instructions"]


def test_export_trae_format(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--format", "trae",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0, result.output
    md = tmp_path / ".trae" / "rules" / "code-reviewer.md"
    assert md.exists()
    assert "# Role" in md.read_text(encoding="utf-8")


def test_export_all_flag(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export", "code-reviewer", "--all",
         "--out", str(tmp_path), "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "code-reviewer" / "SKILL.md").exists()
    assert (tmp_path / ".cursor" / "rules" / "code-reviewer.mdc").exists()
    assert (tmp_path / ".github" / "instructions" / "code-reviewer.instructions.md").exists()
    assert (tmp_path / ".opencode" / "code-reviewer.md").exists()
    assert (tmp_path / ".trae" / "rules" / "code-reviewer.md").exists()


def test_init_creates_config_and_syncs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["init", "--skills", str(REPO / "skills"),
         "--formats", "cursor,vscode", "--yes"],
        catch_exceptions=False,
        env={"USERPROFILE": str(tmp_path), "HOME": str(tmp_path)},
    )
    # init writes .usf.json in CWD — use mix_stderr=False to isolate
    # The CliRunner changes CWD to a temp dir; we just check exit code + output.
    assert result.exit_code == 0, result.output
    assert "synced 11 skills" in result.output
    assert "cursor" in result.output
    assert "vscode" in result.output


def test_sync_reads_config(tmp_path):
    import json as _json
    config = {
        "skills": str(REPO / "skills"),
        "formats": ["cursor", "trae"],
    }
    (tmp_path / ".usf.json").write_text(_json.dumps(config), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["sync", "--project", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert "synced 11 skills" in result.output
    assert (tmp_path / ".cursor" / "rules" / "code-reviewer.mdc").exists()
    assert (tmp_path / ".trae" / "rules" / "code-reviewer.mdc").exists() or \
           (tmp_path / ".trae" / "rules" / "code-reviewer.md").exists()


def test_sync_missing_config_exits_nonzero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--project", str(tmp_path)])
    assert result.exit_code != 0


def test_diff_two_providers():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["diff", "code-reviewer", "--provider", "openai", "--provider", "anthropic",
         "--input", "code=x", "--path", str(REPO / "skills")],
    )
    assert result.exit_code == 0
    # There should be differences between openai and anthropic payloads
    assert "---" in result.output or "+++" in result.output or "system" in result.output
