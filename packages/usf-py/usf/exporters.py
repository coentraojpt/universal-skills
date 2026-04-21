"""Export USF skills to third-party AI coding tool formats.

Each exporter has the same interface:
    export_<format>(skill: Skill, out_dir: Path) -> Path
and returns the path of the primary file written.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .loader import Skill

_ALL_SECTIONS = ("Role", "Task", "Context", "Constraints", "Output Format", "Guardrails", "Examples")


def _skill_body(skill: Skill) -> str:
    """Full markdown body — all present sections concatenated with H1 headings."""
    parts = [f"# {s}\n{skill.sections[s]}" for s in _ALL_SECTIONS if s in skill.sections]
    return "\n\n".join(parts) + "\n"


def _skill_md_content(skill: Skill) -> str:
    """SKILL.md format used by Claude Code, Antigravity, Verdent."""
    fm = {
        "name": skill.frontmatter["name"],
        "description": skill.frontmatter["description"],
    }
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---\n")
    parts = [f"# {s}\n{skill.sections[s]}" for s in _ALL_SECTIONS if s in skill.sections]
    return "\n".join(lines) + "\n\n".join(parts) + "\n"


# ── SKILL.md variants ─────────────────────────────────────────────────────────

def export_claude(skill: Skill, out_dir: Path) -> Path:
    """Claude Code: ~/.claude/skills/<name>/SKILL.md"""
    target = out_dir / skill.name
    target.mkdir(parents=True, exist_ok=True)
    out = target / "SKILL.md"
    out.write_text(_skill_md_content(skill), encoding="utf-8")
    return out


def export_antigravity(skill: Skill, out_dir: Path) -> Path:
    """Antigravity: ~/.gemini/antigravity/skills/<name>/SKILL.md"""
    target = out_dir / skill.name
    target.mkdir(parents=True, exist_ok=True)
    out = target / "SKILL.md"
    out.write_text(_skill_md_content(skill), encoding="utf-8")
    return out


def export_verdent(skill: Skill, out_dir: Path) -> Path:
    """Verdent: uses same path as Claude Code (~/.claude/skills/)."""
    return export_claude(skill, out_dir)


# ── Cursor ────────────────────────────────────────────────────────────────────

def export_cursor(skill: Skill, out_dir: Path) -> Path:
    """Cursor: <project>/.cursor/rules/<name>.mdc"""
    rules_dir = out_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    out = rules_dir / f"{skill.name}.mdc"
    description = str(skill.frontmatter.get("description", ""))
    tags = skill.frontmatter.get("tags", [])
    globs = _tags_to_globs(tags)
    fm_lines = ["---", f"description: {json.dumps(description)}"]
    if globs:
        fm_lines.append(f"globs: {json.dumps(globs)}")
    fm_lines += ["alwaysApply: false", "---\n"]
    content = "\n".join(fm_lines) + "\n" + _skill_body(skill)
    out.write_text(content, encoding="utf-8")
    return out


def _tags_to_globs(tags: object) -> list[str]:
    """Best-effort: map known tags to file globs."""
    mapping = {
        "python": ["**/*.py"],
        "typescript": ["**/*.ts", "**/*.tsx"],
        "javascript": ["**/*.js", "**/*.jsx"],
        "sql": ["**/*.sql"],
        "api": ["**/*.yaml", "**/*.json", "openapi.*"],
    }
    if not isinstance(tags, list):
        return []
    result: list[str] = []
    for tag in tags:
        result.extend(mapping.get(str(tag).lower(), []))
    return result


# ── VS Code / GitHub Copilot ──────────────────────────────────────────────────

def export_vscode(skill: Skill, out_dir: Path) -> Path:
    """VS Code Copilot: <project>/.github/instructions/<name>.instructions.md"""
    inst_dir = out_dir / ".github" / "instructions"
    inst_dir.mkdir(parents=True, exist_ok=True)
    out = inst_dir / f"{skill.name}.instructions.md"
    name = str(skill.frontmatter.get("name", skill.name))
    description = str(skill.frontmatter.get("description", ""))
    fm_lines = [
        "---",
        f"name: {json.dumps(name)}",
        f"description: {json.dumps(description)}",
        "applyTo: '**'",
        "---\n",
    ]
    content = "\n".join(fm_lines) + "\n" + _skill_body(skill)
    out.write_text(content, encoding="utf-8")
    return out


# ── OpenCode ──────────────────────────────────────────────────────────────────

def export_opencode(skill: Skill, out_dir: Path) -> Path:
    """OpenCode: <project>/.opencode/<name>.md + registers in opencode.json"""
    oc_dir = out_dir / ".opencode"
    oc_dir.mkdir(parents=True, exist_ok=True)
    out = oc_dir / f"{skill.name}.md"
    header = f"# {skill.frontmatter.get('name', skill.name)}\n{skill.frontmatter.get('description', '')}\n\n"
    out.write_text(header + _skill_body(skill), encoding="utf-8")

    # Register in opencode.json
    config_path = out_dir / "opencode.json"
    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    instructions: list = config.get("instructions", [])
    entry = f".opencode/{skill.name}.md"
    if entry not in instructions:
        instructions.append(entry)
    config["instructions"] = instructions
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


# ── TRAE ──────────────────────────────────────────────────────────────────────

def export_trae(skill: Skill, out_dir: Path) -> Path:
    """TRAE: <project>/.trae/rules/<name>.md"""
    rules_dir = out_dir / ".trae" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    out = rules_dir / f"{skill.name}.md"
    header = f"# {skill.frontmatter.get('name', skill.name)}\n{skill.frontmatter.get('description', '')}\n\n"
    out.write_text(header + _skill_body(skill), encoding="utf-8")
    return out


# ── Registry ──────────────────────────────────────────────────────────────────

EXPORTERS: dict[str, Callable[[Skill, Path], Path]] = {
    "claude": export_claude,
    "antigravity": export_antigravity,
    "verdent": export_verdent,
    "cursor": export_cursor,
    "vscode": export_vscode,
    "opencode": export_opencode,
    "trae": export_trae,
}

# Global paths per format — used when --global is passed to skill sync/export
GLOBAL_DEFAULTS: dict[str, Path] = {
    "claude": Path.home() / ".claude" / "skills",
    "antigravity": Path.home() / ".gemini" / "antigravity" / "skills",
    "verdent": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "rules",
    "vscode": Path.home() / ".vscode" / "instructions",
    "trae": Path.home() / ".trae" / "rules",
    "opencode": Path.home() / ".opencode",
}
