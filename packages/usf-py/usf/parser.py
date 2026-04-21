"""Parse a USF skill markdown file into frontmatter + sections."""
from __future__ import annotations

import re
from dataclasses import dataclass

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

REQUIRED_SECTIONS = ("Role", "Task", "Context", "Constraints", "Output Format")


@dataclass
class ParsedSkill:
    frontmatter: dict
    sections: dict[str, str]
    raw: str


def parse(text: str) -> ParsedSkill:
    """Split raw markdown into frontmatter (dict) and H1 sections (dict[name,body])."""
    frontmatter, body = _split_frontmatter(text)
    sections = _split_sections(body)
    return ParsedSkill(frontmatter=frontmatter, sections=sections, raw=text)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data, text[m.end():]


def _split_sections(body: str) -> dict[str, str]:
    headings = list(_H1_RE.finditer(body))
    sections: dict[str, str] = {}
    for i, h in enumerate(headings):
        name = h.group(1).strip()
        start = h.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        sections[name] = body[start:end].strip("\n")
    return sections


def missing_required_sections(sections: dict[str, str]) -> list[str]:
    return [s for s in REQUIRED_SECTIONS if s not in sections]
