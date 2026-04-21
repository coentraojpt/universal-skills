"""Load a USF skill from a .md file into a Skill object."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .parser import parse
from .prompt import CompiledPrompt, build_prompt


@dataclass
class InputSpec:
    name: str
    type: str = "string"
    required: bool = False
    default: object = None
    description: str | None = None


@dataclass
class Skill:
    frontmatter: dict
    sections: dict[str, str]
    inputs_spec: list[InputSpec] = field(default_factory=list)
    source_path: Path | None = None

    @property
    def name(self) -> str:
        return str(self.frontmatter.get("name", ""))

    @property
    def description(self) -> str:
        return str(self.frontmatter.get("description", ""))

    def build_prompt(self, inputs: dict | None = None, vault=None) -> CompiledPrompt:
        return build_prompt(self, inputs, vault)

    def render(self, provider: str, inputs: dict | None = None, vault=None) -> dict:
        from .adapters import get_adapter
        compiled = self.build_prompt(inputs, vault)
        return get_adapter(provider).render(compiled)

    def run(self, provider: str, inputs: dict | None = None, vault=None, **kwargs) -> str:
        from .runner import run as run_runner
        return run_runner(self, provider, inputs or {}, vault=vault, **kwargs)


def load(path: str | Path) -> Skill:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    parsed = parse(text)
    inputs_spec = [_parse_input_spec(x) for x in parsed.frontmatter.get("inputs", []) or []]
    return Skill(
        frontmatter=parsed.frontmatter,
        sections=parsed.sections,
        inputs_spec=inputs_spec,
        source_path=p,
    )


def load_dir(path: str | Path, *, recursive: bool = False) -> list[Skill]:
    p = Path(path)
    pattern = "**/*.md" if recursive else "*.md"
    out: list[Skill] = []
    for md in sorted(p.glob(pattern)):
        try:
            s = load(md)
        except Exception:
            continue
        if s.frontmatter.get("usf") is False:
            continue
        if "name" not in s.frontmatter or "description" not in s.frontmatter:
            continue
        out.append(s)
    return out


def _parse_input_spec(raw: dict) -> InputSpec:
    return InputSpec(
        name=str(raw["name"]),
        type=str(raw.get("type", "string")),
        required=bool(raw.get("required", False)),
        default=raw.get("default"),
        description=raw.get("description"),
    )
