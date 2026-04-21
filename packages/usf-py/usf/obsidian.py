"""Obsidian vault integration — load skills and resolve [[wikilinks]] as memory."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .parser import parse

_WIKILINK_RE = re.compile(r"\[\[([^\[\]#|]+)(?:#([^\[\]|]+))?(?:\|[^\[\]]+)?\]\]")


def approx_tokens(text: str) -> int:
    """Approximate token count (len/4) — avoids a tiktoken dependency."""
    return max(1, len(text) // 4)


@dataclass
class WikilinkStats:
    resolved: int = 0
    truncated: int = 0
    skipped: int = 0
    total_tokens: int = 0


@dataclass
class Vault:
    root: Path
    notes: dict[str, Path] = field(default_factory=dict)

    def get_note_text(self, name: str) -> str | None:
        path = self.notes.get(name)
        if not path:
            return None
        return path.read_text(encoding="utf-8")


def load_vault(root: str | Path) -> Vault:
    root_path = Path(root).resolve()
    notes: dict[str, Path] = {}
    for md in root_path.rglob("*.md"):
        # Ignore Obsidian config/plugin dirs
        if any(part.startswith(".") and part != "." for part in md.relative_to(root_path).parts):
            continue
        notes[md.stem] = md
    return Vault(root=root_path, notes=notes)


def resolve_wikilinks(
    vault: Vault,
    text: str,
    mode: Literal["truncate", "summary", "full"] = "truncate",
    per_link_token_limit: int = 1000,
    _visited: set[str] | None = None,
) -> tuple[str, WikilinkStats]:
    """Expand [[wikilinks]] inline. Returns (expanded_text, stats)."""
    if mode not in ("truncate", "summary", "full"):
        raise ValueError(f"invalid wikilink mode: {mode}")
    stats = WikilinkStats()
    visited = set(_visited or ())

    def replace(m: re.Match) -> str:
        name = m.group(1).strip()
        section = m.group(2).strip() if m.group(2) else None
        if name in visited:
            stats.skipped += 1
            return f"[[{name}]]"  # cycle — leave literal
        raw = vault.get_note_text(name)
        if raw is None:
            stats.skipped += 1
            return f"[[{name}]]"

        parsed = parse(raw)
        # Respect explicit opt-out only when resolving by wikilink in summary/truncate mode.
        # (Notes with usf:false are still referenceable as memory.)
        body = _extract_section(parsed, section) if section else _note_body(parsed)
        content = _apply_mode(parsed.frontmatter, body, mode, per_link_token_limit, stats)
        # Recursive resolution
        if "[[" in content:
            child_visited = visited | {name}
            content, child_stats = resolve_wikilinks(
                vault, content, mode=mode, per_link_token_limit=per_link_token_limit,
                _visited=child_visited,
            )
            stats.resolved += child_stats.resolved
            stats.truncated += child_stats.truncated
            stats.skipped += child_stats.skipped
            stats.total_tokens += child_stats.total_tokens
        stats.resolved += 1
        stats.total_tokens += approx_tokens(content)
        return content

    expanded = _WIKILINK_RE.sub(replace, text)
    return expanded, stats


def _note_body(parsed) -> str:
    """Full markdown body with sections joined."""
    if not parsed.sections:
        return parsed.raw.split("---", 2)[-1].strip() if parsed.frontmatter else parsed.raw
    parts = []
    for name, body in parsed.sections.items():
        parts.append(f"# {name}\n{body}")
    return "\n\n".join(parts)


def _extract_section(parsed, section: str) -> str:
    for name, body in parsed.sections.items():
        if name.lower() == section.lower():
            return body
    return _note_body(parsed)


def _apply_mode(
    frontmatter: dict,
    body: str,
    mode: str,
    per_link_token_limit: int,
    stats: WikilinkStats,
) -> str:
    if mode == "full":
        return body
    if mode == "summary":
        summary = frontmatter.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        # fall through to truncate
    # truncate
    limit_chars = per_link_token_limit * 4
    if len(body) > limit_chars:
        stats.truncated += 1
        return body[:limit_chars].rstrip() + "\n\n…[truncated]"
    return body
