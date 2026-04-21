"""Provider-agnostic prompt compilation.

Splits the skill body into:
  system  = Role + Context + Constraints + Guardrails
  user    = Task + Output Format + Examples

This mapping is empirically robust across OpenAI/Anthropic/Gemini/Ollama:
role/constraints/context go to the stable "system" slot; the actual request
(task, requested output, few-shot) goes as the user turn.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import obsidian as obsidian_mod
from .template import render as render_template

if TYPE_CHECKING:
    from .loader import Skill
    from .obsidian import Vault

SYSTEM_SECTIONS = ("Role", "Context", "Constraints", "Guardrails")
USER_SECTIONS = ("Task", "Output Format", "Examples")


@dataclass
class CompiledPrompt:
    system: str
    user: str
    metadata: dict = field(default_factory=dict)
    frontmatter: dict = field(default_factory=dict)


def build_prompt(
    skill: "Skill",
    inputs: dict | None = None,
    vault: "Vault | None" = None,
) -> CompiledPrompt:
    inputs = dict(inputs or {})
    _apply_defaults_and_validate(skill, inputs)

    sections = dict(skill.sections)
    wikilink_stats = None

    if vault is not None:
        mode = skill.frontmatter.get("wikilink_mode", "truncate")
        limit = int(skill.frontmatter.get("wikilink_token_limit", 1000))
        for name, body in list(sections.items()):
            if "[[" in body:
                expanded, stats = obsidian_mod.resolve_wikilinks(
                    vault, body, mode=mode, per_link_token_limit=limit
                )
                sections[name] = expanded
                if wikilink_stats is None:
                    wikilink_stats = stats
                else:
                    wikilink_stats.resolved += stats.resolved
                    wikilink_stats.truncated += stats.truncated
                    wikilink_stats.skipped += stats.skipped
                    wikilink_stats.total_tokens += stats.total_tokens
                if stats.truncated:
                    print(
                        f"[warn] wikilinks truncated in section '{name}': "
                        f"{stats.truncated} link(s) → {limit} tokens each",
                        file=sys.stderr,
                    )

    for name, body in list(sections.items()):
        sections[name] = render_template(body, inputs)

    system_parts = [f"# {s}\n{sections[s]}" for s in SYSTEM_SECTIONS if s in sections]
    user_parts = [f"# {s}\n{sections[s]}" for s in USER_SECTIONS if s in sections]

    meta: dict = {"skill": skill.frontmatter.get("name")}
    if wikilink_stats is not None:
        meta["wikilink_stats"] = {
            "resolved": wikilink_stats.resolved,
            "truncated": wikilink_stats.truncated,
            "skipped": wikilink_stats.skipped,
            "total_tokens": wikilink_stats.total_tokens,
        }

    return CompiledPrompt(
        system="\n\n".join(system_parts).strip(),
        user="\n\n".join(user_parts).strip(),
        metadata=meta,
        frontmatter=dict(skill.frontmatter),
    )


def _apply_defaults_and_validate(skill: "Skill", inputs: dict) -> None:
    missing: list[str] = []
    for spec in skill.inputs_spec:
        if spec.name in inputs and inputs[spec.name] not in (None, ""):
            continue
        if spec.default is not None:
            inputs[spec.name] = spec.default
        elif spec.required:
            missing.append(spec.name)
    if missing:
        raise ValueError(
            f"Missing required input(s) for skill '{skill.frontmatter.get('name')}': "
            f"{', '.join(missing)}"
        )
