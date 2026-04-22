"""USF CLI — `skill` command."""
from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

import click

from . import __version__
from .adapters import available_providers
from .loader import Skill, load, load_dir
from .obsidian import load_vault
from .validate import validate_path, validate_skill


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skill")
def main() -> None:
    """Universal Skills Framework — portable LLM skills."""


@main.command("validate")
@click.argument("path", type=click.Path(exists=True), default="skills")
def validate_cmd(path: str) -> None:
    """Validate a skill file or directory."""
    results = validate_path(path)
    if not results:
        click.echo(click.style("OK  all skills valid", fg="green"))
        return
    for file, errs in results.items():
        click.echo(click.style(f"FAIL  {file}", fg="red"))
        for e in errs:
            click.echo(f"    {e}")
    sys.exit(1)


@main.command("list")
@click.argument("path", type=click.Path(exists=True), default="skills")
def list_cmd(path: str) -> None:
    """List skills in a directory."""
    skills = load_dir(path)
    if not skills:
        click.echo("no skills found")
        return
    name_w = max(len(s.name) for s in skills)
    for s in skills:
        tags = ",".join(s.frontmatter.get("tags", []) or [])
        click.echo(f"{s.name.ljust(name_w)}  {s.description}  [{tags}]")


@main.command("show")
@click.argument("name")
@click.option("--path", default="skills", type=click.Path(exists=True))
def show_cmd(name: str, path: str) -> None:
    """Show a skill's sections."""
    skill = _find(name, path)
    click.echo(click.style(f"# {skill.name}", bold=True))
    click.echo(skill.description)
    click.echo()
    for section, body in skill.sections.items():
        click.echo(click.style(f"## {section}", fg="cyan"))
        click.echo(body)
        click.echo()


@main.command("render")
@click.argument("name")
@click.option("--provider", required=True, type=click.Choice(available_providers()))
@click.option("--input", "inputs", multiple=True, help="key=value or key=@file.txt")
@click.option("--json", "json_file", type=click.Path(exists=True))
@click.option("--model", default=None)
@click.option("--vault", type=click.Path(exists=True), default=None)
@click.option("--path", default="skills", type=click.Path(exists=True))
def render_cmd(
    name: str, provider: str, inputs: tuple[str, ...], json_file: str | None,
    model: str | None, vault: str | None, path: str,
) -> None:
    """Render the provider payload for a skill (dry run — no API call)."""
    skill = _find(name, path)
    ins = _collect_inputs(inputs, json_file)
    vault_obj = load_vault(vault) if vault else None
    payload = skill.render(provider, ins, vault_obj)
    if model:
        payload["model"] = model
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@main.command("run")
@click.argument("name")
@click.option("--provider", required=True, type=click.Choice(available_providers()))
@click.option("--input", "inputs", multiple=True, help="key=value or key=@file.txt")
@click.option("--json", "json_file", type=click.Path(exists=True))
@click.option("--model", default=None)
@click.option("--vault", type=click.Path(exists=True), default=None)
@click.option("--dry-run", is_flag=True, help="Print payload instead of calling the API.")
@click.option("--stream", is_flag=True, help="Stream tokens as they arrive (openai/anthropic).")
@click.option("--path", default="skills", type=click.Path(exists=True))
def run_cmd(
    name: str, provider: str, inputs: tuple[str, ...], json_file: str | None,
    model: str | None, vault: str | None, dry_run: bool, stream: bool, path: str,
) -> None:
    """Run a skill against a real LLM (or --dry-run to just print the payload)."""
    skill = _find(name, path)
    ins = _collect_inputs(inputs, json_file)
    vault_obj = load_vault(vault) if vault else None
    if dry_run:
        payload = skill.render(provider, ins, vault_obj)
        if model:
            payload["model"] = model
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    try:
        output = skill.run(provider, ins, vault=vault_obj, model=model, stream=stream)
    except Exception as exc:
        click.echo(click.style(f"error: {exc}", fg="red"), err=True)
        sys.exit(2)
    if not stream:
        click.echo(output)


@main.command("diff")
@click.argument("name")
@click.option("--provider", "providers", multiple=True, required=True,
              type=click.Choice(available_providers()))
@click.option("--input", "inputs", multiple=True)
@click.option("--json", "json_file", type=click.Path(exists=True))
@click.option("--path", default="skills", type=click.Path(exists=True))
def diff_cmd(name: str, providers: tuple[str, ...], inputs: tuple[str, ...],
             json_file: str | None, path: str) -> None:
    """Diff payloads generated for two providers."""
    if len(providers) != 2:
        click.echo("need exactly two --provider flags", err=True)
        sys.exit(2)
    skill = _find(name, path)
    ins = _collect_inputs(inputs, json_file)
    a = json.dumps(skill.render(providers[0], ins), indent=2, ensure_ascii=False).splitlines()
    b = json.dumps(skill.render(providers[1], ins), indent=2, ensure_ascii=False).splitlines()
    for line in difflib.unified_diff(a, b, fromfile=providers[0], tofile=providers[1], lineterm=""):
        if line.startswith("+"):
            click.echo(click.style(line, fg="green"))
        elif line.startswith("-"):
            click.echo(click.style(line, fg="red"))
        else:
            click.echo(line)


@main.command("export")
@click.argument("name")
@click.option(
    "--format", "fmt",
    type=click.Choice(list(__import__("usf.exporters", fromlist=["EXPORTERS"]).EXPORTERS)),
    default="claude",
    help="Target tool format.",
)
@click.option("--all", "export_all", is_flag=True, default=False, help="Export to all supported formats.")
@click.option("--out", type=click.Path(), default=None, help="Output directory (overrides per-format default).")
@click.option("--path", default="skills", type=click.Path(exists=True))
def export_cmd(name: str, fmt: str, export_all: bool, out: str | None, path: str) -> None:
    """Export a skill to any AI coding tool format.

    Formats: claude, antigravity, verdent, cursor, vscode, opencode, trae.
    Use --all to export to every format at once.
    """
    from .exporters import EXPORTERS, GLOBAL_DEFAULTS
    skill = _find(name, path)
    targets = list(EXPORTERS.keys()) if export_all else [fmt]
    for target_fmt in targets:
        if out is not None:
            out_dir = Path(out)
        else:
            out_dir = GLOBAL_DEFAULTS.get(target_fmt, Path.cwd())
        written = EXPORTERS[target_fmt](skill, out_dir)
        click.echo(f"wrote {written}")


USF_CONFIG = ".usf.json"
USF_GLOBAL_CONFIG = Path.home() / ".usf.json"  # machine-wide: remembers skills path
PROJECT_FORMATS = ("cursor", "vscode", "opencode", "trae", "windsurf", "roo", "claude", "antigravity", "verdent")
GLOBAL_ONLY_FORMATS: tuple[()] = ()  # all formats now support project-level
GLOBAL_FORMATS = PROJECT_FORMATS


def _load_global_config() -> dict:
    if USF_GLOBAL_CONFIG.exists():
        try:
            return json.loads(USF_GLOBAL_CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _save_global_config(data: dict) -> None:
    existing = _load_global_config()
    existing.update(data)
    USF_GLOBAL_CONFIG.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


@main.command("init")
@click.option("--skills", "skills_dir", default=None,
              help="Path to skills directory (default: auto-detect or prompt).")
@click.option("--formats", default=None,
              help="Comma-separated formats (cursor,vscode,trae,opencode). Default: prompt.")
@click.option("--team", "team_url", default=None,
              help="Git URL of a shared team skills repository.")
@click.option("--yes", is_flag=True, default=False, help="Accept defaults without prompting.")
def init_cmd(skills_dir: str | None, formats: str | None, team_url: str | None, yes: bool) -> None:
    """Create .usf.json in the current project and run initial sync.

    Links this project to your skills folder so `skill sync` keeps all
    AI coding tools up to date whenever skills change.
    """
    from .exporters import EXPORTERS

    config_path = Path(USF_CONFIG)

    if skills_dir is None:
        detected = _detect_skills_dir()
        global_cfg = _load_global_config()
        default = str(detected) if detected else global_cfg.get("skills", "~/universal-skills/skills")
        if yes:
            skills_dir = default
        else:
            skills_dir = click.prompt("Skills directory", default=default)

    skills_path = Path(skills_dir).expanduser().resolve()
    if not skills_path.exists():
        click.echo(click.style(f"error: skills directory not found: {skills_path}", fg="red"), err=True)
        sys.exit(2)

    available = [f for f in EXPORTERS if f in PROJECT_FORMATS]
    if formats is None:
        if yes:
            chosen = list(available)
        else:
            default_fmt = ",".join(available)
            raw = click.prompt(
                f"Formats ({', '.join(available)})",
                default=default_fmt,
            )
            chosen = [f.strip() for f in raw.split(",") if f.strip() in EXPORTERS]
    else:
        chosen = [f.strip() for f in formats.split(",") if f.strip() in EXPORTERS]

    if not chosen:
        click.echo(click.style("error: no valid formats selected.", fg="red"), err=True)
        sys.exit(2)

    config: dict = {
        "skills": str(skills_path),
        "formats": chosen,
    }
    if team_url:
        config["team"] = team_url
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    click.echo(f"wrote {config_path}")

    _save_global_config({"skills": str(skills_path)})

    if team_url:
        _sync_team(team_url, chosen, Path.cwd(), use_global=False)
    else:
        _do_sync(config, Path.cwd(), use_global=False)


@main.command("sync")
@click.option("--project", type=click.Path(exists=True), default=None,
              help="Project directory containing .usf.json (default: CWD).")
@click.option("--global", "sync_global", is_flag=True, default=False,
              help="Also sync to global tools (claude, antigravity, verdent).")
@click.option("--team", "sync_team", is_flag=True, default=False,
              help="Pull from the team git repo configured in .usf.json and sync.")
def sync_cmd(project: str | None, sync_global: bool, sync_team: bool) -> None:
    """Re-export all skills to every tool configured in .usf.json.

    Run this after adding or editing any skill to keep all AI coding
    tools in this project up to date.
    """
    project_dir = Path(project).resolve() if project else Path.cwd()
    config_path = project_dir / USF_CONFIG
    if not config_path.exists():
        if sync_global:
            # Allow --global without a project config — use machine-wide skills path
            global_cfg = _load_global_config()
            if not global_cfg.get("skills"):
                click.echo(
                    click.style("error: no skills path found. Run `skill init` in your skills folder first.", fg="red"),
                    err=True,
                )
                sys.exit(2)
            config = {"skills": global_cfg["skills"], "formats": list(PROJECT_FORMATS)}
        else:
            click.echo(
                click.style(f"error: {USF_CONFIG} not found in {project_dir}. Run `skill init` first.", fg="red"),
                err=True,
            )
            sys.exit(2)
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    if sync_team:
        team_url = config.get("team")
        if not team_url:
            click.echo(
                click.style("error: no team URL in .usf.json. Run `skill init --team URL` first.", fg="red"),
                err=True,
            )
            sys.exit(2)
        _sync_team(team_url, config.get("formats", list(PROJECT_FORMATS)), project_dir, use_global=sync_global)
        return
    if sync_global:
        config = dict(config)
        existing = list(config.get("formats", []))
        extra = [f for f in GLOBAL_ONLY_FORMATS if f not in existing]
        config["formats"] = existing + extra
    _do_sync(config, project_dir, use_global=sync_global)


def _sync_team(team_url: str, formats: list, project_dir: Path, use_global: bool = False) -> None:
    slug = team_url.rstrip("/").rstrip(".git").rsplit("/", 1)[-1]
    cache_dir = Path.home() / ".usf" / "teams" / slug

    try:
        if cache_dir.exists():
            click.echo(f"updating team skills from {team_url} ...")
            subprocess.run(["git", "-C", str(cache_dir), "fetch", "--quiet"],
                           capture_output=True, text=True)
            result = subprocess.run(
                ["git", "-C", str(cache_dir), "reset", "--hard", "FETCH_HEAD"],
                capture_output=True, text=True,
            )
        else:
            click.echo(f"cloning team skills from {team_url} ...")
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(["git", "clone", team_url, str(cache_dir)],
                                    capture_output=True, text=True)
        if result.returncode != 0:
            click.echo(click.style(f"error: git failed: {result.stderr.strip()}", fg="red"), err=True)
            sys.exit(2)
    except FileNotFoundError:
        click.echo(click.style("error: git is required for team sync but was not found.", fg="red"), err=True)
        sys.exit(2)

    skills_path = cache_dir / "skills" if (cache_dir / "skills").is_dir() else cache_dir
    _do_sync({"skills": str(skills_path), "formats": formats}, project_dir, use_global=use_global)


def _do_sync(config: dict, project_dir: Path, use_global: bool = False) -> None:
    from .exporters import EXPORTERS, GLOBAL_DEFAULTS, PROJECT_OUT_DIRS

    skills_path = Path(config["skills"]).expanduser().resolve()
    formats: list[str] = config.get("formats", [])
    skills = load_dir(str(skills_path))

    if not skills:
        click.echo("no skills found — nothing to sync")
        return

    for fmt in formats:
        if fmt not in EXPORTERS:
            click.echo(click.style(f"warning: unknown format '{fmt}', skipping", fg="yellow"), err=True)
            continue
        if use_global and fmt in GLOBAL_DEFAULTS:
            out_dir = GLOBAL_DEFAULTS[fmt]
        elif fmt in PROJECT_OUT_DIRS:
            out_dir = project_dir / PROJECT_OUT_DIRS[fmt]
        else:
            out_dir = project_dir
        count = 0
        for skill in skills:
            EXPORTERS[fmt](skill, out_dir)
            count += 1
        label = str(out_dir).replace(str(Path.home()), "~")
        click.echo(click.style(f"synced {count} skills", fg="green") + f" -> {fmt}  ({label})")


def _detect_skills_dir() -> Path | None:
    """Walk up from CWD looking for a skills/ directory with .md files."""
    current = Path.cwd()
    for _ in range(5):
        candidate = current / "skills"
        if candidate.is_dir() and any(candidate.glob("*.md")):
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _find(name: str, path: str) -> Skill:
    skills = load_dir(path)
    for s in skills:
        if s.name == name:
            return s
    click.echo(f"skill '{name}' not found in {path}", err=True)
    sys.exit(2)


def _collect_inputs(inputs: tuple[str, ...], json_file: str | None) -> dict:
    result: dict = {}
    if json_file:
        result.update(json.loads(Path(json_file).read_text(encoding="utf-8")))
    for raw in inputs:
        if "=" not in raw:
            raise click.UsageError(f"--input expects key=value, got: {raw}")
        key, _, value = raw.partition("=")
        if value.startswith("@"):
            value = Path(value[1:]).read_text(encoding="utf-8")
        result[key] = value
    return result


if __name__ == "__main__":
    main()
